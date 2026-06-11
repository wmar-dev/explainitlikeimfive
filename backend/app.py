import json
import logging
import os
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from mlx_lm import generate, load
from mlx_lm.models.cache import make_prompt_cache
from mlx_lm.utils import MODEL_REMAPPING
from pydantic import BaseModel

from tools import check_words_in_corpus

# Gemma 4 MLX quantized models use model_type "gemma4_unified" (multimodal),
# but mlx-lm's text-only module expects "gemma4". Remap so the text model loads.
MODEL_REMAPPING["gemma4_unified"] = "gemma4"

# Default vocabulary corpus for check_words_in_corpus, used to keep chat
# responses in the XKCD Simple Writer word list.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault(
    "WORD_CORPUS_PATH", os.path.join(PROJECT_ROOT, "xkcd-words.txt")
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model
model = None
tokenizer = None
MODEL_NAME = "mlx-community/gemma-4-12B-it-OptiQ-4bit"

# Tools available for tool-calling (see https://www.tryaisuite.com/docs/tool-calling)
tools = [check_words_in_corpus]


# Pydantic models for request/response
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


def load_model():
    """Load the MLX model and tokenizer"""
    global model, tokenizer, prompt_cache
    logger.info(f"Loading model: {MODEL_NAME}")
    model, tokenizer = load(MODEL_NAME)
    logger.info("Model loaded successfully!")
    prompt_cache = make_prompt_cache(model, max_kv_size=4096)


@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    load_model()


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat endpoint that streams responses"""
    if not request.message:
        raise HTTPException(status_code=400, detail="No message provided")

    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Build the prompt with conversation history
    prompt = build_prompt(request.history, request.message)

    async def generate_stream():
        """Generator function for streaming responses"""
        try:
            response = generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=512,
                verbose=False,
                prompt_cache=prompt_cache,
            )

            # If the response strays from the simple-word corpus, give the
            # model one chance to rewrite it using only allowed words.
            check = check_words_in_corpus(response)
            if not check["all_words_in_corpus"]:
                logger.info(f"Words not in corpus: {check['words_not_in_corpus']}")
                retry_prompt = build_retry_prompt(
                    request.history,
                    request.message,
                    response,
                    check["words_not_in_corpus"],
                )
                response = generate(
                    model,
                    tokenizer,
                    prompt=retry_prompt,
                    max_tokens=512,
                    verbose=False,
                )

            # Send the complete response
            yield f"data: {json.dumps({'content': response, 'done': False})}\n\n"
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

        except Exception as e:
            error_msg = json.dumps({"error": str(e)})
            yield f"data: {error_msg}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def build_prompt(history: List[Message], user_message: str) -> str:
    """Build a prompt from conversation history and new message using Gemma 4 format"""
    system_prompt = """You are a helpful teacher who explains things using only the ten hundred (1,000) most common words in English, like XKCD's Thing Explainer.

Rules:
- Use ONLY simple, common words that everyone knows
- Break down hard ideas into easy parts
- Use examples from everyday life
- If you need to use a big word, explain it with small words first
- Keep it fun and easy to understand
- Short sentences are better than long ones

Remember: No big science words, no hard business words, just simple talk that a kid could understand."""

    prompt_parts = ["<bos>"]

    if history:
        for msg in history:
            if msg.role == "user":
                prompt_parts.append(
                    f"<|turn>user\n{msg.content}<turn|>\n"
                )
            else:
                prompt_parts.append(
                    f"<|turn>model\n{msg.content}<turn|>\n"
                )

    if not history:
        prompt_parts.append(
            f"<|turn>system\n{system_prompt}<turn|>\n<|turn>user\n{user_message}<turn|>\n"
        )
    else:
        prompt_parts.append(f"<|turn>user\n{user_message}<turn|>\n")

    prompt_parts.append("<|turn>model\n<|channel>thought\n<channel|>")

    return "".join(prompt_parts)


def build_retry_prompt(
    history: List[Message],
    user_message: str,
    draft_response: str,
    bad_words: List[str],
) -> str:
    """Build a follow-up prompt asking the model to rewrite a draft response
    without the given words, which are not in the simple-word corpus."""
    prompt = build_prompt(history, user_message)
    prompt = prompt.removesuffix("<|turn>model\n<|channel>thought\n<channel|>")

    feedback = (
        "Your last answer used these words, which are not on the list of "
        f"simple words: {', '.join(bad_words)}. Rewrite your answer so it "
        "means the same thing, using only simple, common words. Do not use "
        "any of those words."
    )

    prompt += f"<|turn>model\n{draft_response}<turn|>\n"
    prompt += f"<|turn>user\n{feedback}<turn|>\n"
    prompt += "<|turn>model\n<|channel>thought\n<channel|>"

    return prompt


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
