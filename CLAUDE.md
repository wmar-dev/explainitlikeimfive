# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A chat application that uses Flask (backend), React (frontend), and Apple's MLX framework to run the Mistral-7B-Instruct-v0.3-4bit model locally for AI-powered explanations.

## Commands

This project requires Python 3.10+ and Node.js/npm.

**Backend setup and run:**
```bash
# Install Python dependencies
pip install -e .
# OR use requirements.txt
cd backend && pip install -r requirements.txt

# Run the Flask server (will download model on first run)
cd backend && python app.py
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
cd backend && python app.py

# Terminal 2: Frontend
cd frontend && npm start
```

## Architecture

### Backend (`/backend`)
- **app.py**: Flask server with MLX integration
  - `/api/health`: Health check endpoint
  - `/api/chat`: Streaming chat endpoint using Server-Sent Events (SSE)
  - Uses `mlx-lm` library to load and run Mistral-7B-Instruct-v0.3-4bit
  - Supports conversation history for multi-turn dialogues
  - Streams responses in real-time

### Frontend (`/frontend`)
- **React SPA** with modern hooks (useState, useEffect, useRef)
- **App.js**: Main chat interface component
  - Real-time message streaming display
  - Conversation history management
  - Health status indicator
  - Responsive design with gradient UI
- **Proxy configuration**: Development server proxies API requests to Flask backend (port 5000)

### Key Technical Details
- Model runs locally using Apple MLX (optimized for Apple Silicon)
- Backend uses Flask-CORS for cross-origin requests
- Frontend uses fetch API with ReadableStream for SSE
- Messages use Mistral instruction format: `[INST] prompt [/INST]`
