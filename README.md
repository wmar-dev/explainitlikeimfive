# Explain It Like I'm Five

A chat application that uses FastAPI, React, and Apple's MLX framework to run AI models locally for simple, clear explanations in the style of XKCD's "Thing Explainer" and [Simple Writer](https://xkcd.com/simplewriter/) (using only the 1,000 most common words).

## Features

- Local AI chat powered by Google Gemma 4 12B (4-bit OptiQ quantized)
- Real-time streaming responses
- Conversation history support
- Beautiful, responsive UI
- Runs entirely on your machine (no API keys needed)

## Prerequisites

- **macOS** with Apple Silicon - MLX is optimized for Apple Silicon
- **Python 3.10+**
- **Node.js 16+** and npm

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd explainitlikeimfive
```

### 2. Install dependencies

Use the included `Makefile` to install both the backend and frontend dependencies:

```bash
make install
```

This is equivalent to running `uv sync` for the backend and `npm install` in `frontend/` for the frontend.

To remove installed dependencies and build artifacts (`node_modules`, `frontend/build`, `.venv`):

```bash
make clean
```

## Running the Application

You need to run both the backend and frontend in separate terminal windows.

### Terminal 1: Start the Backend

```bash
make run-backend
```

The first time you run this, it will download the Gemma 4 12B model (~7GB). This may take a few minutes depending on your internet connection.

The backend will start on `http://localhost:5000`

### Terminal 2: Start the Frontend

```bash
make run-frontend
```

The frontend will start on `http://localhost:3000` and automatically open in your browser.

## Usage

1. Wait for the status indicator to show "Ready" (the model needs to load on first startup)
2. Type your question in the input field
3. Press Enter or click the send button
4. Watch as the AI streams its response in real-time using simple, common words

## Project Structure

```
explainitlikeimfive/
├── backend/
│   └── app.py              # FastAPI server with MLX integration
├── frontend/
│   ├── public/
│   │   └── index.html      # HTML template
│   ├── src/
│   │   ├── App.js          # Main React component
│   │   ├── App.css         # Styles
│   │   ├── index.js        # React entry point
│   │   └── index.css       # Global styles
│   └── package.json        # Node dependencies
├── pyproject.toml          # Python project metadata (uv managed)
├── CLAUDE.md               # Development guidance
└── README.md               # This file
```

## API Endpoints

### GET `/api/health`
Returns the health status and whether the model is loaded.

Response:
```json
{
  "status": "ok",
  "model_loaded": true
}
```

### POST `/api/chat`
Streams chat responses using Server-Sent Events (SSE).

Request body:
```json
{
  "message": "Explain quantum physics",
  "history": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello!"}
  ]
}
```

Response: Server-Sent Events stream with JSON data chunks.

## Tool Calling

The backend gives the model a `check_words_in_corpus` tool (defined in `backend/tools.py`) that checks whether a piece of text only uses words from the simple-word vocabulary (`xkcd-words.txt`).

After generating a response, the backend calls this tool to check the response against the vocabulary list. If it finds words outside the list, it asks the model to rewrite the response without those words and sends the corrected version to the user.

## Technology Stack

- **Backend**: FastAPI, MLX, mlx-lm
- **Frontend**: React 18, Modern CSS
- **AI Model**: Google Gemma 4 12B (4-bit OptiQ quantized, [`mlx-community/gemma-4-12B-it-OptiQ-4bit`](https://huggingface.co/mlx-community/gemma-4-12B-it-OptiQ-4bit))
- **Communication**: REST API with Server-Sent Events for streaming
- **Style**: XKCD Thing Explainer (using only the 1,000 most common words)

## Notes

- The model runs locally on your machine using MLX, which is optimized for Apple Silicon
- First-time startup will be slower due to model download and loading
- Model responses are streamed in real-time for a better user experience
- The quantized 4-bit model provides a good balance between quality and performance
- All explanations use only the 1,000 most common words, making complex topics simple to understand
- The vocabulary list (`xkcd-words.txt`) is fetched from XKCD's [Simple Writer](https://xkcd.com/simplewriter/) tool via `scripts/xkcdwords.py`

## Troubleshooting

**Backend won't start:**
- Make sure you have Python 3.10+ installed
- Verify you're on macOS with Apple Silicon (MLX requirement)
- Check that all dependencies are installed: `uv sync`

**Frontend won't start:**
- Make sure Node.js 16+ is installed
- Delete `node_modules` and run `npm install` again
- Check that port 3000 is available

**Model loading is slow:**
- This is normal on first run (downloading ~7GB model)
- Subsequent runs will be faster as the model is cached

**API errors:**
- Ensure the backend is running on port 5000
- Check the browser console for detailed error messages
