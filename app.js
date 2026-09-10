const chatScroll = document.querySelector('#chatScroll');
const composer = document.querySelector('#composer');
const messageInput = document.querySelector('#messageInput');
const wordList = document.querySelector('#wordList');
const vocabCount = document.querySelector('#vocabCount');
const toast = document.querySelector('#toast');
const micButton = document.querySelector('#micButton');
let vocabulary = [];

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('show');
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove('show'), 2200);
}

function renderVocabulary(words) {
  vocabulary = words;
  vocabCount.textContent = words.length;
  wordList.innerHTML = words.slice(0, 4).map((word) => `
    <article class="word-card">
      <div class="word-top"><strong>${escapeHtml(word.word)}</strong><span class="word-category">${escapeHtml(word.category)}</span></div>
      <p>${escapeHtml(word.meaning)}</p>
      <p class="word-example">“${escapeHtml(word.example)}”</p>
    </article>`).join('');
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' }[character]));
}

function addMessage(text, role) {
  const row = document.createElement('div');
  row.className = `message-row ${role === 'user' ? 'user-row' : 'assistant-row'}`;
  row.innerHTML = role === 'user'
    ? `<div class="message-group"><span class="message-author">You <time>now</time></span><div class="bubble user-bubble">${escapeHtml(text)}</div></div>`
    : `<div class="mini-avatar">L</div><div class="message-group"><span class="message-author">Lingo <time>now</time></span><div class="bubble assistant-bubble">${escapeHtml(text)}</div></div>`;
  chatScroll.appendChild(row);
  chatScroll.scrollTop = chatScroll.scrollHeight;
}

function addCorrection(correction) {
  const card = document.createElement('div');
  card.className = 'correction-card';
  card.innerHTML = `<div class="correction-heading"><span class="check-icon">✓</span><strong>Small correction</strong><span class="correction-label">1 of 1 this turn</span></div><div class="correction-body"><div><span class="muted-label">Try this</span><p><del>${escapeHtml(correction.before)}</del> <span class="arrow">→</span> <strong>${escapeHtml(correction.after)}</strong></p></div><div class="why"><span class="muted-label">Why?</span><p>${escapeHtml(correction.reason)}</p></div></div>`;
  chatScroll.appendChild(card);
}

async function sendMessage(event) {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;
  messageInput.value = '';
  messageInput.style.height = 'auto';
  addMessage(message, 'user');
  try {
    const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message }) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error);
    if (result.correction) addCorrection(result.correction);
    addMessage(result.reply, 'assistant');
    if ('speechSynthesis' in window) speak(result.reply);
  } catch (error) {
    showToast(error.message || 'Could not send message.');
  }
}

async function saveWord(word, meaning = 'pleasant or beautiful', example = `That was a ${word} moment.`) {
  const response = await fetch('/api/vocabulary', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ word, meaning, example, category: 'Conversation' }) });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error);
  renderVocabulary(result.vocabulary);
  showToast(result.saved ? `${word} added to vocabulary` : `${word} is already in your list`);
}

function speak(text) {
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-US';
  utterance.rate = 0.92;
  window.speechSynthesis.speak(utterance);
}

composer.addEventListener('submit', sendMessage);
messageInput.addEventListener('input', () => {
  messageInput.style.height = 'auto';
  messageInput.style.height = `${Math.min(messageInput.scrollHeight, 90)}px`;
});
document.addEventListener('click', async (event) => {
  const addButton = event.target.closest('.add-word');
  if (addButton) {
    addButton.disabled = true;
    try { await saveWord(addButton.dataset.word); } catch (error) { showToast(error.message); addButton.disabled = false; }
  }
});
document.querySelector('#clearButton').addEventListener('click', () => {
  document.querySelectorAll('.chat-scroll .message-row, .chat-scroll .correction-card, .chat-scroll .vocab-suggestion').forEach((element) => element.remove());
  showToast('Chat cleared');
});
document.querySelector('#viewAllButton').addEventListener('click', () => showToast(`${vocabulary.length} words in your collection`));
document.querySelector('#addVocabButton').addEventListener('click', () => {
  const word = window.prompt('New word');
  if (word && word.trim()) saveWord(word.trim()).catch((error) => showToast(error.message));
});

if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new Recognition();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  micButton.addEventListener('click', () => { recognition.start(); micButton.textContent = '...'; });
  recognition.onresult = (event) => { messageInput.value = event.results[0][0].transcript; messageInput.dispatchEvent(new Event('input')); };
  recognition.onend = () => { micButton.textContent = '⌕'; };
} else {
  micButton.addEventListener('click', () => showToast('Voice input is not supported in this browser.'));
}

fetch('/api/state').then((response) => response.json()).then((state) => renderVocabulary(state.vocabulary)).catch(() => showToast('Vocabulary is offline.'));
