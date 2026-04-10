"""
Spell Bee Voice Bot — Main Entry Point

A Pipecat-based voice bot that conducts a Spell Bee game.
Uses:
  - Deepgram for STT (Speech-to-Text) and TTS (Text-to-Speech)
  - Google Gemini for LLM (game master logic via function calling)
  - SmallWebRTC for peer-to-peer voice transport (no Daily API key needed)

Run:
  python bot.py
  Then open http://localhost:7860 in your browser.
"""

import json
import os
import sys

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.adapters.schemas.tools_schema import AdapterType
from pipecat.frames.frames import OutputTransportMessageFrame, LLMContextFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext, ToolsSchema
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.deepgram.tts import DeepgramTTSService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.transports.base_transport import TransportParams
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport

from game_processor import SpellBeeGame, SPELL_BEE_TOOLS

load_dotenv(override=True)

# ─── Validate Environment ─────────────────────────────────────
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not DEEPGRAM_API_KEY or DEEPGRAM_API_KEY == "your_deepgram_api_key_here":
    logger.error("DEEPGRAM_API_KEY not set. Please add it to your .env file.")
    sys.exit(1)

if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_google_gemini_api_key_here":
    logger.error("GOOGLE_API_KEY not set. Please add it to your .env file.")
    sys.exit(1)


# ─── System Prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are a friendly and encouraging Spell Bee game host conducting a spelling bee competition over voice.

IMPORTANT RULES:
1. When presenting a word, ALWAYS use the present_new_word function first to get the word details.
2. After getting the word, say it clearly, give the definition, use it in a sentence, then say the word again.
3. When the user spells a word (says individual letters), use the check_user_spelling function to verify it.
4. Extract ONLY the letters from what the user says. Ignore filler words like "um", "uh", "so", etc.
5. After checking, give enthusiastic feedback for correct answers, or gentle encouragement for incorrect ones. For incorrect answers, tell them the correct spelling by reading out each letter.
6. Then ask if they're ready for the next word, or present the next word.
7. Keep track of progress — after every few words, briefly mention the score.
8. After 10 words (or if user wants to stop), use end_spell_bee_game to end the game.

VOICE GUIDELINES:
- Speak naturally and conversationally — this is a voice call, not text.
- Don't use emojis, bullet points, markdown, or special characters.
- Be warm, patient, and encouraging like a real spelling bee host.
- Keep responses concise — don't ramble.
- When saying letters, say them clearly and individually, like "The correct spelling is: C, O, N, S, C, I, E, N, T, I, O, U, S".
- Always pronounce the word clearly before and after giving the definition.

START THE GAME:
When the user connects, welcome them warmly, briefly explain the rules (you'll say a word, they spell it letter by letter), and then present the first word using the present_new_word function."""


# ─── Transport Parameters ──────────────────────────────────────
# These are used by the Pipecat runner to create the appropriate transport.
# We use lambdas to defer creation until the transport type is selected.
transport_params = {
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        audio_in_sample_rate=16000,
        audio_out_sample_rate=16000,
        vad_analyzer=SileroVADAnalyzer(params=VADParams(
            start_secs=0.9,     # require almost 1 full second of continuous speech to interrupt
            stop_secs=1.5,
            min_volume=0.8      # extremely high volume threshold
        )),
    ),
}


async def run_bot(transport, runner_args: RunnerArguments):
    """Set up and run the Spell Bee bot pipeline."""
    logger.info("Starting Spell Bee Voice Bot pipeline")

    # Helper to send messages to the frontend via data channel.
    # The SmallWebRTCTransport doesn't expose send_message directly,
    # so we access the connection via the transport's internal client.
    def send_to_frontend(data: dict):
        """Send a JSON message to the frontend via WebRTC data channel."""
        try:
            # The client itself is a Datachannel interface in the new Small WebRTC
            transport._client.send_message(
                OutputTransportMessageFrame(data)
            )
        except Exception as e:
            logger.warning(f"Could not send message to frontend: {e}")

    # ─── Speech-to-Text (Deepgram) ─────────────────────────────
    stt = DeepgramSTTService(
        api_key=DEEPGRAM_API_KEY,
        settings=DeepgramSTTService.Settings(
            language="en",
            model="nova-2",
            smart_format=True,
        ),
    )

    # ─── Text-to-Speech (Deepgram) ─────────────────────────────
    tts = DeepgramTTSService(
        api_key=DEEPGRAM_API_KEY,
        settings=DeepgramTTSService.Settings(
            voice="aura-2-andromeda-en",
        ),
    )

    # ─── LLM (Google Gemini) ───────────────────────────────────
    llm = GoogleLLMService(
        api_key=GOOGLE_API_KEY,
        settings=GoogleLLMService.Settings(model="gemini-2.5-flash-lite")
    )

    # ─── Game State ────────────────────────────────────────────
    game = SpellBeeGame()

    # ─── LLM Context & Aggregators ─────────────────────────────
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    context = LLMContext(
        messages=messages,
        tools=ToolsSchema(standard_tools=[], custom_tools={AdapterType.GEMINI: SPELL_BEE_TOOLS})
    )
    context_aggregator = LLMContextAggregatorPair(context=context)

    # ─── Register Function Handlers ────────────────────────────

    async def handle_present_word(params):
        """Get the next word and present it to the user."""
        word_info = game.get_next_word()

        # Send game state update to frontend via data channel
        game_state = game.get_game_state()
        game_state["event"] = "new_word"
        send_to_frontend(game_state)

        # Return word info to LLM so it can present it naturally
        await params.result_callback(
            f"Word #{game.total_words}: '{word_info['word']}'. "
            f"Definition: {word_info['definition']}. "
            f"Example sentence: {word_info['sentence']}. "
            f"Difficulty: {word_info['difficulty']}."
        )

    async def handle_check_spelling(params):
        """Check the user's spelling attempt."""
        spelling = params.arguments.get("spelling", "")
        result = game.check_spelling(spelling)

        # Send state update to frontend
        game_state = game.get_game_state()
        game_state["event"] = "spelling_result"
        game_state["last_result"] = result
        send_to_frontend(game_state)

        if result.get("correct"):
            response = (
                f"CORRECT! The spelling '{result['given']}' is correct. "
                f"Current score: {result['score']} points. "
                f"{result['correct_count']} correct out of {result['total_words']} words so far."
            )
        else:
            response = (
                f"INCORRECT. The user spelled '{result['given']}' but the correct "
                f"spelling is '{result['expected']}'. "
                f"Current score: {result['score']} points. "
                f"{result['correct_count']} correct out of {result['total_words']} words so far."
            )

        # Check if game should end
        if game.total_words >= game.max_words:
            response += " This was the last word. Please end the game now using end_spell_bee_game."

        await params.result_callback(response)

    async def handle_get_score(params):
        """Return the current game score."""
        state = game.get_game_state()
        send_to_frontend(state)

        await params.result_callback(
            f"Score: {state['score']} points. "
            f"{state['correct_count']} correct, {state['incorrect_count']} incorrect, "
            f"out of {state['total_words']} words. "
            f"Words remaining: {state['max_words'] - state['total_words']}."
        )

    async def handle_end_game(params):
        """End the game and provide summary."""
        summary = game.end_game()

        # Send game over state to frontend
        send_to_frontend(summary)

        await params.result_callback(
            f"GAME OVER! Final results: "
            f"Score: {summary['final_score']} points. "
            f"{summary['correct_count']} correct out of {summary['total_words']} words "
            f"({summary['percentage']}% accuracy). "
            f"Please give a warm summary and thank the player."
        )

    llm.register_function("present_new_word", handle_present_word)
    llm.register_function("check_user_spelling", handle_check_spelling)
    llm.register_function("get_current_score", handle_get_score)
    llm.register_function("end_spell_bee_game", handle_end_game)

    # ─── Pipeline ──────────────────────────────────────────────
    pipeline = Pipeline(
        [
            transport.input(),               # Audio from user's browser
            stt,                              # Speech → Text
            context_aggregator.user(),        # Collect user responses
            llm,                              # Gemini processes + function calls
            tts,                              # Text → Speech
            transport.output(),               # Audio back to user's browser
            context_aggregator.assistant(),   # Track assistant responses
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    # ─── Event Handlers ───────────────────────────────────────

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected")
        # Send initial game state to frontend
        send_to_frontend(game.get_game_state())
        # Kick off the conversation — LLM will welcome user and present first word
        await task.queue_frames([LLMContextFrame(context)])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")
        await task.cancel()

    # ─── Run ───────────────────────────────────────────────────
    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat runner."""
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
