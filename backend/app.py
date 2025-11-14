from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from mlx_lm import load, generate
import json
from typing import List, Dict

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
MODEL_NAME = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"

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
    global model, tokenizer
    print(f"Loading model: {MODEL_NAME}")
    model, tokenizer = load(MODEL_NAME)
    print("Model loaded successfully!")

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    load_model()

@app.get('/api/health', response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "model_loaded": model is not None
    }

@app.post('/api/chat')
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
                verbose=False
            )

            # Send the complete response
            yield f"data: {json.dumps({'content': response, 'done': False})}\n\n"
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

        except Exception as e:
            error_msg = json.dumps({'error': str(e)})
            yield f"data: {error_msg}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
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

    # Mistral instruction format
    messages = []

    # Add system prompt to the first message
    if not history:
        messages.append(f"[INST] {system_prompt}\n\n{user_message} [/INST]")
    else:
        # Add conversation history
        for i, msg in enumerate(history):
            if msg.role == 'user':
                # Include system prompt in first user message if not already there
                if i == 0:
                    messages.append(f"[INST] {system_prompt}\n\n{msg.content} [/INST]")
                else:
                    messages.append(f"[INST] {msg.content} [/INST]")
            else:
                messages.append(msg.content)

        # Add current user message
        messages.append(f"[INST] {user_message} [/INST]")

    return " ".join(messages)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)