/**
 * Spell Bee Voice Bot — Frontend Script
 *
 * Handles WebRTC connection to the Pipecat bot via SmallWebRTCTransport.
 * Uses the Pipecat runner's /api/offer endpoint for signaling.
 * Receives game state updates via WebRTC data channel messages.
 */

// ─── DOM Elements ────────────────────────────────────────────
const connectScreen = document.getElementById("connect-screen");
const gameScreen = document.getElementById("game-screen");
const gameoverScreen = document.getElementById("gameover-screen");
const btnStart = document.getElementById("btn-start");
const btnEnd = document.getElementById("btn-end");
const connectionBadge = document.getElementById("connection-badge");

// Score elements
const scoreValue = document.getElementById("score-value");
const wordNum = document.getElementById("word-num");
const maxWords = document.getElementById("max-words");
const correctCount = document.getElementById("correct-count");
const incorrectCount = document.getElementById("incorrect-count");

// Word display
const wordDisplay = document.getElementById("word-display");
const currentWord = document.getElementById("current-word");
const difficultyBadge = document.getElementById("difficulty-badge");
const wordStatus = document.getElementById("word-status");

// Voice indicator
const voiceIndicator = document.getElementById("voice-indicator");
const voiceText = document.getElementById("voice-text");

// History
const historyList = document.getElementById("history-list");

// Game over
const finalScore = document.getElementById("final-score");
const finalAccuracy = document.getElementById("final-accuracy");
const finalCorrect = document.getElementById("final-correct");
const finalHistory = document.getElementById("final-history");

// Audio
const botAudio = document.getElementById("bot-audio");

// ─── State ───────────────────────────────────────────────────
let peerConnection = null;
let isConnected = false;

// ─── WebRTC Connection ───────────────────────────────────────

async function startGame() {
  btnStart.disabled = true;
  btnStart.innerHTML =
    '<span class="btn-icon">⏳</span><span>Connecting...</span>';

  try {
    // Create peer connection
    peerConnection = new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    });

    // MUST create data channel BEFORE creating the offer to negotiate it in SDP
    const dataChannel = peerConnection.createDataChannel("pipecat");
    dataChannel.onmessage = (evt) => {
      try {
        const message = JSON.parse(evt.data);
        handleBotMessage(message);
      } catch (e) {
        console.log("Data channel message (raw):", evt.data);
      }
    };
    dataChannel.onopen = () => console.log("Local data channel opened");
    dataChannel.onclose = () => console.log("Local data channel closed");

    // Handle incoming audio tracks from the bot
    peerConnection.ontrack = (event) => {
      console.log("Received remote track:", event.track.kind);
      if (event.track.kind === "audio") {
        const stream = new MediaStream([event.track]);
        botAudio.srcObject = stream;
        botAudio
          .play()
          .catch((e) => console.warn("Audio autoplay blocked:", e));
      }
    };

    // Handle data channels created by the remote peer (the bot)
    peerConnection.ondatachannel = (event) => {
      console.log("Received data channel:", event.channel.label);
      const channel = event.channel;
      channel.onmessage = (evt) => {
        try {
          const message = JSON.parse(evt.data);
          handleBotMessage(message);
        } catch (e) {
          console.log("Data channel message (raw):", evt.data);
        }
      };
      channel.onopen = () => console.log("Remote data channel opened");
      channel.onclose = () => console.log("Remote data channel closed");
    };

    // Get user microphone
    const localStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 16000,
      },
    });

    // Add audio track to peer connection
    localStream.getTracks().forEach((track) => {
      peerConnection.addTrack(track, localStream);
    });

    // Connection state changes
    peerConnection.onconnectionstatechange = () => {
      const state = peerConnection.connectionState;
      console.log("Connection state:", state);
      if (state === "connected") {
        onConnected();
      } else if (
        state === "disconnected" ||
        state === "failed" ||
        state === "closed"
      ) {
        onDisconnected();
      }
    };

    // Create offer
    const offer = await peerConnection.createOffer({
      offerToReceiveAudio: true,
    });
    await peerConnection.setLocalDescription(offer);

    // Wait for ICE gathering to complete (or timeout)
    await waitForICEGathering(peerConnection, 3000);

    // Send offer to the Pipecat runner's signaling endpoint
    const response = await fetch("/api/offer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sdp: peerConnection.localDescription.sdp,
        type: peerConnection.localDescription.type,
      }),
    });

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}: ${await response.text()}`);
    }

    const answer = await response.json();

    // Set the remote description (answer from the bot)
    await peerConnection.setRemoteDescription(
      new RTCSessionDescription({
        sdp: answer.sdp,
        type: answer.type,
      })
    );

    console.log("WebRTC signaling complete");
  } catch (error) {
    console.error("Connection failed:", error);
    btnStart.disabled = false;
    btnStart.innerHTML =
      '<span class="btn-icon">🎤</span><span>Retry Connection</span>';
    alert(
      "Failed to connect. Make sure the bot server is running.\n\nError: " +
        error.message
    );
  }
}

function waitForICEGathering(pc, timeout) {
  return new Promise((resolve) => {
    if (pc.iceGatheringState === "complete") {
      resolve();
      return;
    }

    const timer = setTimeout(resolve, timeout);

    pc.onicegatheringstatechange = () => {
      if (pc.iceGatheringState === "complete") {
        clearTimeout(timer);
        resolve();
      }
    };
  });
}

function onConnected() {
  isConnected = true;
  connectionBadge.classList.add("connected");
  connectionBadge.querySelector(".badge-text").textContent = "Connected";

  // Switch to game screen
  connectScreen.classList.add("hidden");
  gameScreen.classList.remove("hidden");
  gameoverScreen.classList.add("hidden");

  setBotSpeaking(true);
}

function onDisconnected() {
  isConnected = false;
  connectionBadge.classList.remove("connected");
  connectionBadge.querySelector(".badge-text").textContent = "Disconnected";
}

async function endSession() {
  if (peerConnection) {
    peerConnection.close();
    peerConnection = null;
  }
  connectScreen.classList.remove("hidden");
  gameScreen.classList.add("hidden");
  gameoverScreen.classList.add("hidden");
  btnStart.disabled = false;
  btnStart.innerHTML =
    '<span class="btn-icon">🎤</span><span>Start Game</span>';
  resetUI();
  onDisconnected();
}

function playAgain() {
  gameoverScreen.classList.add("hidden");
  connectScreen.classList.remove("hidden");
  btnStart.disabled = false;
  btnStart.innerHTML =
    '<span class="btn-icon">🎤</span><span>Start Game</span>';
  resetUI();
  onDisconnected();
}

// ─── Message Handling ────────────────────────────────────────

function handleBotMessage(message) {
  console.log("Bot message:", message);

  const type = message.type;

  if (type === "game_state") {
    updateGameState(message);
  } else if (type === "game_over") {
    showGameOver(message);
  }

  // Handle event-specific UI updates
  const event = message.event;
  if (event === "new_word") {
    onNewWord(message);
  } else if (event === "spelling_result") {
    onSpellingResult(message);
  }
}

function updateGameState(state) {
  // Update score
  animateValue(scoreValue, state.score);
  wordNum.textContent = state.total_words || 0;
  maxWords.textContent = state.max_words || 10;
  animateValue(correctCount, state.correct_count);
  animateValue(incorrectCount, state.incorrect_count);

  // Update current word display (show masked word)
  if (state.current_word) {
    currentWord.textContent = state.current_word
      .split("")
      .map(() => "·")
      .join(" ");
  }

  // Update difficulty badge
  if (state.difficulty) {
    difficultyBadge.textContent = state.difficulty.toUpperCase();
    difficultyBadge.className = "difficulty-badge " + state.difficulty;
  }

  // Update word history
  if (state.word_history && state.word_history.length > 0) {
    renderHistory(state.word_history);
  }
}

function onNewWord(state) {
  wordDisplay.classList.remove("correct", "incorrect");
  wordStatus.innerHTML =
    '<div class="pulse-ring"></div><span>Listening for your spelling...</span>';
  setBotSpeaking(true);

  if (state.current_word) {
    currentWord.textContent = state.current_word
      .split("")
      .map(() => "·")
      .join(" ");
  }
}

function onSpellingResult(state) {
  const result = state.last_result;
  if (!result) return;

  // Reveal the actual word
  currentWord.textContent = result.word.toUpperCase();

  if (result.correct) {
    wordDisplay.classList.add("correct");
    wordDisplay.classList.remove("incorrect");
    wordStatus.innerHTML =
      '<span style="color: var(--accent-green)">✅ Correct!</span>';
  } else {
    wordDisplay.classList.add("incorrect");
    wordDisplay.classList.remove("correct");
    wordStatus.innerHTML = `<span style="color: var(--accent-red)">❌ Incorrect — You spelled: ${result.given}</span>`;
  }

  // Animate score
  scoreValue.classList.add("score-pop");
  setTimeout(() => scoreValue.classList.remove("score-pop"), 400);
}

function showGameOver(summary) {
  gameScreen.classList.add("hidden");
  gameoverScreen.classList.remove("hidden");

  finalScore.textContent = summary.final_score;
  finalAccuracy.textContent = summary.percentage + "%";
  finalCorrect.textContent = `${summary.correct_count}/${summary.total_words}`;

  // Render word history chips
  finalHistory.innerHTML = "";
  if (summary.word_history) {
    summary.word_history.forEach((entry) => {
      const chip = document.createElement("div");
      chip.className = `final-word-chip ${entry.correct ? "correct" : "incorrect"}`;
      chip.textContent = `${entry.correct ? "✅" : "❌"} ${entry.word}`;
      finalHistory.appendChild(chip);
    });
  }

  // Disconnect after game over
  setTimeout(() => {
    if (peerConnection) {
      peerConnection.close();
      peerConnection = null;
    }
    onDisconnected();
  }, 2000);
}

// ─── UI Helpers ──────────────────────────────────────────────

function renderHistory(history) {
  historyList.innerHTML = "";
  [...history].reverse().forEach((entry) => {
    const item = document.createElement("div");
    item.className = `history-item ${entry.correct ? "correct" : "incorrect"}`;
    item.innerHTML = `
      <div class="history-icon">${entry.correct ? "✅" : "❌"}</div>
      <span class="history-word">${entry.word}</span>
      <span class="history-answer">${entry.user_answer || ""}</span>
    `;
    historyList.appendChild(item);
  });
}

function animateValue(element, newValue) {
  const currentValue = parseInt(element.textContent) || 0;
  if (currentValue !== newValue) {
    element.textContent = newValue;
    element.classList.add("score-pop");
    setTimeout(() => element.classList.remove("score-pop"), 400);
  }
}

function setBotSpeaking(speaking) {
  if (speaking) {
    voiceIndicator.classList.add("active");
    voiceText.textContent = "Bot is speaking...";
  } else {
    voiceIndicator.classList.remove("active");
    voiceText.textContent = "Your turn to spell!";
  }
}

function resetUI() {
  scoreValue.textContent = "0";
  wordNum.textContent = "0";
  correctCount.textContent = "0";
  incorrectCount.textContent = "0";
  currentWord.textContent = "Waiting...";
  difficultyBadge.textContent = "MEDIUM";
  difficultyBadge.className = "difficulty-badge";
  wordDisplay.classList.remove("correct", "incorrect");
  wordStatus.innerHTML =
    '<div class="pulse-ring"></div><span>Listening...</span>';
  historyList.innerHTML =
    '<div class="history-empty">Words will appear here as you play</div>';
  voiceIndicator.classList.remove("active");
}

// ─── Initialize ──────────────────────────────────────────────
console.log("Spell Bee Voice Bot — Frontend loaded");
