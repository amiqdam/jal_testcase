/* User Chatbot Page */
function renderChatbot(app) {
  const sessionId = getOrCreateSessionId();
  let messagesData = [];
  let quickStartShown = false;

  app.innerHTML = `
    <div class="chat-container">
      <div class="chat-header">
        <div class="avatar">🎓</div>
        <div class="info">
          <h2>JAL Admissions</h2>
          <p>Online • Universitas Luminara</p>
        </div>
      </div>
      <div class="chat-messages" id="chat-messages"></div>
      <div class="chat-input-area">
        <input type="text" id="chat-input" placeholder="Ketik pesan..." autocomplete="off" />
        <button id="chat-send">Kirim</button>
      </div>
    </div>`;

  const messagesEl = document.getElementById('chat-messages');
  const inputEl = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send');

  // Welcome message
  const welcomeMsg = { direction: 'outbound', content: 'Selamat datang di JAL Admissions! 🎓\nSaya AI asisten Universitas Luminara. Pilih topik di bawah atau langsung ketik pertanyaan Anda.', created_at: new Date().toISOString() };
  messagesEl.appendChild(createChatBubble(welcomeMsg));

  // Quick-start options
  const quickStart = createQuickStartOptions(async (option) => {
    quickStartShown = true;
    await sendMessage(option.message, option.intent);
  });
  messagesEl.appendChild(quickStart);

  async function sendMessage(content, quickStartIntent) {
    if (!content.trim()) return;

    // Remove quick-start if still visible
    const qs = document.getElementById('quick-start-options');
    if (qs) qs.remove();

    // Show user message
    const userMsg = { direction: 'inbound', content, created_at: new Date().toISOString() };
    messagesEl.appendChild(createChatBubble(userMsg));
    
    inputEl.value = '';
    inputEl.disabled = true;
    sendBtn.disabled = true;

    // Show typing indicator
    messagesEl.appendChild(createTypingIndicator());
    scrollToBottom();

    try {
      const body = { session_id: sessionId, content };
      if (quickStartIntent) body.quick_start_intent = quickStartIntent;

      const res = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();

      // Remove typing indicator
      const typing = document.getElementById('typing-indicator');
      if (typing) typing.remove();

      // Show AI response
      const aiMsg = { direction: 'outbound', content: data.response, created_at: new Date().toISOString() };
      messagesEl.appendChild(createChatBubble(aiMsg));
    } catch (err) {
      const typing = document.getElementById('typing-indicator');
      if (typing) typing.remove();
      const errorMsg = { direction: 'outbound', content: 'Maaf, terjadi kesalahan. Silakan coba lagi. 🙏', created_at: new Date().toISOString() };
      messagesEl.appendChild(createChatBubble(errorMsg));
    }

    inputEl.disabled = false;
    sendBtn.disabled = false;
    inputEl.focus();
    scrollToBottom();
  }

  sendBtn.onclick = () => sendMessage(inputEl.value);
  inputEl.onkeydown = (e) => {
    if (e.key === 'Enter') sendMessage(inputEl.value);
    // Remove quick-start on typing
    if (!quickStartShown) {
      const qs = document.getElementById('quick-start-options');
      if (qs && inputEl.value.length > 0) qs.remove();
    }
  };

  function scrollToBottom() {
    setTimeout(() => { messagesEl.scrollTop = messagesEl.scrollHeight; }, 50);
  }

  scrollToBottom();
}

function getOrCreateSessionId() {
  let sid = localStorage.getItem('jal_session_id');
  if (!sid) {
    sid = 'sess-' + Math.random().toString(36).slice(2, 10);
    localStorage.setItem('jal_session_id', sid);
  }
  return sid;
}
