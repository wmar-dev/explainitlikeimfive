# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A chat application that uses FastAPI (backend), React (frontend), and Apple's MLX framework to run the Google Gemma 3 12B model locally for AI-powered explanations. The AI responds in the style of XKCD's "Thing Explainer", using only the 1,000 most common words to explain complex topics in simple terms.

## Commands

This project requires Python 3.10+ and Node.js/npm.

**Backend setup and run:**
```bash
# Install Python dependencies using uv
uv sync

# Run the FastAPI server (will download model on first run)
uv run python backend/app.py
```

**Frontend setup and run:**
```bash
# Install dependencies
cd frontend && npm install

# Start development server
npm start
```

**Running both (in separate terminals):**
```bash
# Terminal 1: Backend
uv run python backend/app.py

# Terminal 2: Frontend
cd frontend && npm start
```

## Architecture

### Backend (`/backend`)
- **app.py**: FastAPI server with MLX integration
  - `/api/health`: Health check endpoint
  - `/api/chat`: Streaming chat endpoint using Server-Sent Events (SSE)
  - `/docs`: Interactive API documentation (Swagger UI)
  - Uses `mlx-lm` library to load and run Google Gemma 3 12B (4-bit quantized)
  - Supports conversation history for multi-turn dialogues
  - Streams responses in real-time
  - Pydantic models for request/response validation
  - **Thing Explainer system prompt**: Instructs the AI to explain everything using only the 1,000 most common words, breaking down complex topics into simple, everyday language

### Frontend (`/frontend`)
- **React SPA** with modern hooks (useState, useEffect, useRef)
- **App.js**: Main chat interface component
  - Real-time message streaming display
  - Conversation history management
  - Health status indicator
  - Responsive design with gradient UI
- **Proxy configuration**: Development server proxies API requests to FastAPI backend (port 5000)

### Key Technical Details
- Model runs locally using Apple MLX (optimized for Apple Silicon)
- Backend uses FastAPI with CORS middleware and Pydantic validation
- Frontend uses fetch API with ReadableStream for SSE
- Messages use Gemma 3 instruction format: `<start_of_turn>user\n...<end_of_turn>` with system prompt embedded in first user message
- System prompt enforces XKCD Thing Explainer style (using only 1,000 most common words)
- Automatic API documentation at `/docs` and `/redoc`
