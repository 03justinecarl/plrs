// Typing speed mini-game
const sentences = [
  "The quick brown fox jumps over the lazy dog.",
  "Practice makes perfect in every skill you learn.",
  "Information technology shapes the modern world.",
  "Hard work and dedication lead to success.",
  "Knowledge is the foundation of every achievement."
];

let currentSentence = '';
let startTime = null;
let isRunning = false;

function initTypingGame() {
  const target = document.getElementById('typing-target');
  const input = document.getElementById('typing-input');
  const wpmDisplay = document.getElementById('wpm-display');
  const accDisplay = document.getElementById('acc-display');
  const startBtn = document.getElementById('start-game-btn');
  const statusMsg = document.getElementById('game-status');

  if (!target) return;

  startBtn.addEventListener('click', () => {
    currentSentence = sentences[Math.floor(Math.random() * sentences.length)];
    renderTarget(currentSentence, '', target);
    input.value = '';
    input.disabled = false;
    input.focus();
    startTime = null;
    isRunning = true;
    wpmDisplay.textContent = '0';
    accDisplay.textContent = '100';
    statusMsg.textContent = 'Start typing!';
    startBtn.textContent = 'Restart';
  });

  input.addEventListener('input', () => {
    if (!isRunning) return;
    if (!startTime) startTime = Date.now();

    const typed = input.value;
    renderTarget(currentSentence, typed, target);

    const elapsed = (Date.now() - startTime) / 1000 / 60;
    const words = typed.trim().split(' ').filter(Boolean).length;
    const wpm = elapsed > 0 ? Math.round(words / elapsed) : 0;
    wpmDisplay.textContent = wpm;

    // Accuracy
    let correct = 0;
    for (let i = 0; i < typed.length; i++) {
      if (typed[i] === currentSentence[i]) correct++;
    }
    const acc = typed.length > 0 ? Math.round((correct / typed.length) * 100) : 100;
    accDisplay.textContent = acc;

    if (typed === currentSentence) {
      isRunning = false;
      input.disabled = true;
      statusMsg.textContent = `✅ Done! ${wpm} WPM · ${acc}% accuracy`;
    }
  });
}

function renderTarget(sentence, typed, container) {
  container.innerHTML = '';
  for (let i = 0; i < sentence.length; i++) {
    const span = document.createElement('span');
    span.textContent = sentence[i];
    if (i < typed.length) {
      span.className = typed[i] === sentence[i] ? 'char-correct' : 'char-wrong';
    } else if (i === typed.length) {
      span.className = 'char-current';
    }
    container.appendChild(span);
  }
}

document.addEventListener('DOMContentLoaded', initTypingGame);
