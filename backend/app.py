from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from mlx_lm import load, generate
import json

app = Flask(__name__)
CORS(app)

# Global variables for model
model = None
tokenizer = None
MODEL_NAME = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"

def load_model():
    """Load the MLX model and tokenizer"""
    global model, tokenizer
    print(f"Loading model: {MODEL_NAME}")
    model, tokenizer = load(MODEL_NAME)
    print("Model loaded successfully!")

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "model_loaded": model is not None
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint that streams responses"""
    data = request.json
    user_message = data.get('message', '')
    conversation_history = data.get('history', [])

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    if model is None:
        return jsonify({"error": "Model not loaded"}), 503

    # Build the prompt with conversation history
    prompt = build_prompt(conversation_history, user_message)

    def generate_stream():
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

    return Response(
        generate_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

def build_prompt(history, user_message):
    """Build a prompt from conversation history and new message"""
    # Mistral instruction format
    messages = []

    # Add conversation history
    for msg in history:
        if msg['role'] == 'user':
            messages.append(f"[INST] {msg['content']} [/INST]")
        else:
            messages.append(msg['content'])

    # Add current user message
    messages.append(f"[INST] {user_message} [/INST]")

    return " ".join(messages)

if __name__ == '__main__':
    load_model()
    app.run(debug=True, port=5000, threaded=True)
