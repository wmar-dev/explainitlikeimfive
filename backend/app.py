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
    # Mistral instruction format
    messages = []

    # Add conversation history
    for msg in history:
        if msg.role == 'user':
            messages.append(f"[INST] {msg.content} [/INST]")
        else:
            messages.append(msg.content)

    # Add current user message
    messages.append(f"[INST] {user_message} [/INST]")

    return " ".join(messages)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)