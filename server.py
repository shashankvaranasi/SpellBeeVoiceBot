"""
Spell Bee Voice Bot — Server

Custom FastAPI server that:
1. Serves our custom game frontend at /
2. Handles WebRTC signaling at /api/offer
3. Creates a new bot pipeline for each connecting client

This replaces the Pipecat runner's default server to give us
full control over the frontend while keeping WebRTC signaling.
"""

import asyncio
import json
import os
import sys

import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

load_dotenv(override=True)

# Validate API keys early
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not DEEPGRAM_API_KEY or DEEPGRAM_API_KEY == "your_deepgram_api_key_here":
    logger.error("DEEPGRAM_API_KEY not set. Please add it to your .env file.")
    logger.error("Get your free key at: https://deepgram.com")
    sys.exit(1)

if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_google_gemini_api_key_here":
    logger.error("GOOGLE_API_KEY not set. Please add it to your .env file.")
    logger.error("Get your free key at: https://aistudio.google.com")
    sys.exit(1)

# ─── Import Pipecat SmallWebRTC components ─────────────────────
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.request_handler import (
    SmallWebRTCRequest,
    SmallWebRTCPatchRequest,
    SmallWebRTCRequestHandler,
)

# ─── Create FastAPI App ────────────────────────────────────────
app = FastAPI(title="Spell Bee Voice Bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the SmallWebRTC request handler
small_webrtc_handler = SmallWebRTCRequestHandler(host="0.0.0.0")

# ─── Serve Custom Frontend ────────────────────────────────────

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the custom game frontend."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/style.css")
async def serve_css():
    """Serve the CSS file."""
    return FileResponse(
        os.path.join(FRONTEND_DIR, "style.css"),
        media_type="text/css",
    )


@app.get("/script.js")
async def serve_js():
    """Serve the JavaScript file."""
    return FileResponse(
        os.path.join(FRONTEND_DIR, "script.js"),
        media_type="application/javascript",
    )


# ─── WebRTC Signaling Endpoints ───────────────────────────────

@app.post("/api/offer")
async def offer(request: SmallWebRTCRequest, background_tasks: BackgroundTasks):
    """Handle WebRTC offer requests — creates a new bot instance per connection."""
    from bot import bot
    from pipecat.runner.types import SmallWebRTCRunnerArguments

    async def webrtc_connection_callback(connection: SmallWebRTCConnection):
        """Called when the WebRTC connection is established."""
        runner_args = SmallWebRTCRunnerArguments(
            webrtc_connection=connection,
            body=request.request_data,
        )
        # Run the bot in a background task
        background_tasks.add_task(bot, runner_args)

    # Let the handler negotiate the WebRTC connection
    answer = await small_webrtc_handler.handle_web_request(
        request=request,
        webrtc_connection_callback=webrtc_connection_callback,
    )
    return answer


@app.patch("/api/offer")
async def ice_candidate(request: SmallWebRTCPatchRequest):
    """Handle ICE candidate exchange."""
    await small_webrtc_handler.handle_patch_request(request)
    return {"status": "success"}


# ─── Run Server ───────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("  🐝 Spell Bee Voice Bot")
    logger.info("  Open http://localhost:7860 in your browser")
    logger.info("=" * 60)

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=7860,
        log_level="info",
        reload=False,
    )
