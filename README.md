# 🐝 Spell Bee Voice Bot

A voice-based Spell Bee game bot built with the **Pipecat** framework. The bot conducts a spelling bee competition over a real-time voice call — it speaks a word, you spell it out letter by letter, and the bot evaluates your response.

## 🎯 Features

- **Real-time voice interaction** — Speak and listen naturally via WebRTC
- **AI-powered game host** — Google Gemini acts as a friendly spelling bee host
- **30 words** across 3 difficulty levels (Easy, Medium, Hard)
- **Instant feedback** — Hear if you're correct or incorrect immediately
- **Score tracking** — Real-time score display on the web UI
- **Turn-taking** — VAD-based detection waits for you to finish spelling
- **Interruption handling** — Bot stops cleanly if you interrupt mid-speech
- **Word history** — See all your attempts in the game dashboard

## 🏗️ Architecture

```
Browser (WebRTC) ←→ SmallWebRTCTransport ←→ Pipecat Pipeline
                                                │
                                    ┌───────────┼───────────┐
                                    ▼           ▼           ▼
                              Deepgram STT  Gemini LLM  Deepgram TTS
                                            (Game Host)
                                                │
                                          Function Calls
                                    ┌───────────┼───────────┐
                                    ▼           ▼           ▼
                              present_word  check_spell  end_game
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Voice Pipeline | [Pipecat](https://github.com/pipecat-ai/pipecat) |
| Speech-to-Text | Deepgram (Nova-2) |
| Text-to-Speech | Deepgram (Aura) |
| LLM | Google Gemini 2.0 Flash |
| Transport | SmallWebRTC (peer-to-peer) |
| Frontend | Vanilla HTML/CSS/JS |

## 📋 Prerequisites

- **Python 3.10+**
- **Deepgram API Key** — [Sign up free](https://deepgram.com)
- **Google Gemini API Key** — [Get free key](https://aistudio.google.com)

## 🚀 Setup & Run

### 1. Clone the repository

```bash
git clone <repo-url>
cd SpellBeeVoiceBot
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

```bash
copy .env.example .env
```

Edit `.env` and add your API keys:

```env
DEEPGRAM_API_KEY=your_actual_deepgram_key
GOOGLE_API_KEY=your_actual_gemini_key
```

### 5. Run the bot

**Option A — Custom Game UI (recommended):**
```bash
python server.py
```
Then open **http://localhost:7860** in your browser.

**Option B — Pipecat's built-in client:**
```bash
python bot.py -t webrtc
```
Then open **http://localhost:7860/client** in your browser.

> **Note:** Allow microphone access when prompted by your browser.

## 🎮 How to Play

1. Click **"Start Game"** — the bot will welcome you and explain the rules
2. The bot says a word, gives its definition, and uses it in a sentence
3. **Spell it out loud**, letter by letter (e.g., "R-H-Y-T-H-M")
4. The bot tells you if you're correct or incorrect
5. After 10 words, the game ends with a final score summary

## 📁 Project Structure

```
SpellBeeVoiceBot/
├── server.py              # FastAPI server serving custom frontend + WebRTC signaling
├── bot.py                 # Pipecat pipeline & bot logic (also works with runner)
├── game_processor.py      # Game state management & LLM function tools
├── word_list.py           # Hardcoded word list (30 words, 3 levels)
├── frontend/
│   ├── index.html         # Custom game UI
│   ├── style.css          # Dark theme styling
│   └── script.js          # WebRTC client & state rendering
├── requirements.txt       # Python dependencies
├── .env.example           # API key template
├── .gitignore
└── README.md
```

## 🔧 Key Implementation Details

### Pipeline (bot.py)
The Pipecat pipeline chains these processors:
```
TransportInput → Deepgram STT → UserAggregator → Gemini LLM → Deepgram TTS → TransportOutput → AssistantAggregator
```

### Custom Game Logic (game_processor.py)
The LLM uses **function calling** to interact with the game state:
- `present_new_word()` — Gets the next word from the pool
- `check_user_spelling(spelling)` — Validates the user's attempt
- `get_current_score()` — Returns current stats
- `end_spell_bee_game()` — Ends the game with a summary

### Turn-Taking & Interruptions
- **Silero VAD** detects when the user starts/stops speaking
- **Interruptions are enabled** — if you speak while the bot is talking, it stops cleanly
- The bot waits for you to finish spelling before evaluating

### Frontend Communication
Game state updates are sent from the bot to the frontend via the WebRTC data channel, enabling real-time score and history updates without polling.

## 📝 Notes

- The bot uses **Deepgram** for both STT and TTS (free tier credits available)
- **Google Gemini** is used as the LLM (generous free tier)
- No external WebRTC service (like Daily) is needed — uses peer-to-peer `SmallWebRTCTransport`
- The word list contains 30 words across Easy, Medium, and Hard difficulty levels
