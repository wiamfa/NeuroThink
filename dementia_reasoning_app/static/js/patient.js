const socket = io();
const transcriptEl = document.getElementById("transcript");
const micToggle = document.getElementById("mic-toggle");
const statusIndicator = document.getElementById("status-indicator");
const assistantResponseEl = document.getElementById("assistant-response");
const reasoningListEl = document.getElementById("reasoning-chain");
const scoreValueEl = document.getElementById("reasoning-score");
const metricGridEl = document.getElementById("metric-grid");

let recognition;
let listening = false;

function appendTranscript(message, speaker = "Patient") {
  const paragraph = document.createElement("p");
  const speakerEl = document.createElement("strong");
  speakerEl.textContent = `${speaker}:`;
  const messageNode = document.createTextNode(` ${message}`);
  paragraph.appendChild(speakerEl);
  paragraph.appendChild(messageNode);
  transcriptEl.appendChild(paragraph);
  transcriptEl.scrollTop = transcriptEl.scrollHeight;
}

function ensureRecognition() {
  if (recognition) {
    return recognition;
  }

  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    statusIndicator.textContent =
      "Speech recognition is unavailable. Please update your browser.";
    micToggle.disabled = true;
    return null;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.lang = "en-US";
  recognition.interimResults = false;

  recognition.addEventListener("result", (event) => {
    const transcript = Array.from(event.results)
      .map((result) => result[0].transcript)
      .join(" ")
      .trim();

    if (transcript) {
      appendTranscript(transcript);
      socket.emit("patient_message", { transcript });
    }
  });

  recognition.addEventListener("end", () => {
    if (listening) {
      toggleListening(false);
    }
  });

  recognition.addEventListener("error", (event) => {
    console.error("Speech recognition error", event.error);
    statusIndicator.textContent = `Error: ${event.error}`;
    toggleListening(false);
  });

  return recognition;
}

function toggleListening(forceState) {
  const nextState =
    typeof forceState === "boolean" ? forceState : !Boolean(listening);
  listening = nextState;
  micToggle.classList.toggle("recording", listening);
  statusIndicator.classList.toggle("listening", listening);
  micToggle.textContent = listening ? "⏹️ Stop" : "🎤 Start Speaking";
  statusIndicator.textContent = listening
    ? "Listening…"
    : "Microphone idle";

  if (!recognition) {
    return;
  }

  try {
    if (listening) {
      recognition.start();
    } else {
      recognition.stop();
    }
  } catch (error) {
    console.error("Error toggling recognition", error);
  }
}

micToggle.addEventListener("click", () => {
  if (!ensureRecognition()) {
    return;
  }
  toggleListening();
});

socket.on("assistant_response", (payload) => {
  if (payload.response) {
    appendTranscript(payload.response, "Assistant");
    assistantResponseEl.textContent = payload.response;

    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(payload.response);
      utterance.lang = "en-US";
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    }
  }

  reasoningListEl.innerHTML = "";
  (payload.reasoning || []).forEach((step) => {
    const item = document.createElement("li");
    item.textContent = step;
    reasoningListEl.appendChild(item);
  });

  scoreValueEl.textContent = payload.score ?? "–";

  metricGridEl.innerHTML = "";
  const metrics = payload.metrics || {};
  Object.keys(metrics).forEach((metric) => {
    const wrapper = document.createElement("div");
    wrapper.className = "metric";
    wrapper.innerHTML = `
      <span class="metric-title">${metric.replace(/_/g, " ")}</span>
      <span class="metric-value">${metrics[metric]}</span>
    `;
    metricGridEl.appendChild(wrapper);
  });

  if (payload.insights) {
    const insights = document.createElement("p");
    insights.className = "insights";
    insights.textContent = payload.insights;
    metricGridEl.appendChild(insights);
  }
});
