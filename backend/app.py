import json
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from mlx_lm import generate, load
from mlx_lm.models.cache import make_prompt_cache
from pydantic import BaseModel

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
MODEL_NAME = "mlx-community/gemma-3-12b-it-4bit"


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
    print(f"Loading model: {MODEL_NAME}")
    model, tokenizer = load(MODEL_NAME)
    print("Model loaded successfully!")
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
    """Build a prompt from conversation history and new message"""
    # System prompt for Thing Explainer style responses
    system_prompt = """You are a helpful teacher who explains things using only the ten hundred (1,000) most common words in English, like XKCD's Thing Explainer.

Rules:
- Use ONLY simple, common words that everyone knows
- Break down hard ideas into easy parts
- Use examples from everyday life
- If you need to use a big word, explain it with small words first
- Keep it fun and easy to understand
- Short sentences are better than long ones

Remember: No big science words, no hard business words, just simple talk that a kid could understand."""

    # Gemma 3 instruction format
    prompt_parts = []

    # Add conversation history
    if history:
        for msg in history:
            if msg.role == "user":
                prompt_parts.append(
                    f"<start_of_turn>user\n{msg.content}<end_of_turn>\n"
                )
            else:
                prompt_parts.append(
                    f"<start_of_turn>model\n{msg.content}<end_of_turn>\n"
                )

    # Add current user message with system prompt included in first message
    if not history:
        # First message: include system prompt
        prompt_parts.append(
            f"<start_of_turn>user\n{system_prompt}\n\n{user_message}<end_of_turn>\n"
        )
    else:
        # Subsequent messages
        prompt_parts.append(f"<start_of_turn>user\n{user_message}<end_of_turn>\n")

    # Add model turn indicator
    prompt_parts.append("<start_of_turn>model\n")

    return "".join(prompt_parts)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000)
