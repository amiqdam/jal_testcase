/* Chatbot Page — User-facing chat with onboarding form */
function renderChatbot() {
  const app = document.getElementById('app');
  const stored = JSON.parse(localStorage.getItem('jal_user') || 'null');

  if (!stored) {
    renderOnboarding(app);
    return;
  }

  app.innerHTML = `
    <div class="chat-container">
      <div class="chat-header">
        <div class="avatar">🎓</div>
        <div class="info">
          <h2>JAL University</h2>
          <p>AI Asisten Admisi • Online</p>
        </div>
      </div>
      <div class="chat-messages" id="chatMessages"></div>
      <div class="chat-input-area">
        <input type="text" id="chatInput" placeholder="Ketik pertanyaan..." autocomplete="off">
        <button id="chatSend">Kirim</button>
      </div>
    </div>
  `;

  const messagesEl = document.getElementById('chatMessages');
  const inputEl = document.getElementById('chatInput');
  const sendBtn = document.getElementById('chatSend');

  // Welcome message
  const welcome = createChatBubble({ direction: 'outbound', content: `Halo ${stored.name}! 👋\nSelamat datang di JAL University.\nAda yang bisa saya bantu tentang pendaftaran, program studi, beasiswa, atau informasi kampus?`, created_at: new Date().toISOString() });
  messagesEl.appendChild(welcome);

  // Quick start options
  fetch('/api/dashboard/config')
    .then(r => r.json())
    .then(config => {
      const qs = createQuickStartOptions(config.quick_start_options || [], (opt) => {
        sendMessage(opt.message, opt.micro_intent);
        qs.remove();
      });
      messagesEl.appendChild(qs);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    });

  async function sendMessage(content, quickIntent) {
    if (!content.trim()) return;
    inputEl.value = '';

    // User bubble
    messagesEl.appendChild(createChatBubble({ direction: 'inbound', content, created_at: new Date().toISOString() }));

    // Typing indicator
    const typing = document.createElement('div');
    typing.className = 'typing-indicator';
    typing.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    messagesEl.appendChild(typing);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    try {
      const body = { email: stored.email, name: stored.name, content };
      if (quickIntent) body.quick_start_intent = quickIntent;
      if (stored.lead_source) body.lead_source = stored.lead_source;

      const res = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      typing.remove();

      messagesEl.appendChild(createChatBubble({
        direction: 'outbound', content: data.response || data.detail || 'Maaf, terjadi kesalahan.',
        created_at: new Date().toISOString()
      }));
    } catch(e) {
      typing.remove();
      messagesEl.appendChild(createChatBubble({
        direction: 'outbound', content: 'Maaf, koneksi terputus. Silakan coba lagi.',
        created_at: new Date().toISOString()
      }));
    }
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  sendBtn.onclick = () => sendMessage(inputEl.value);
  inputEl.onkeydown = (e) => { if (e.key === 'Enter') sendMessage(inputEl.value); };
}

function renderOnboarding(app) {
  app.innerHTML = `
    <div class="onboarding-overlay">
      <div class="onboarding-card">
        <h2>JAL University 🎓</h2>
        <p>Selamat datang! Sebelum mulai, isi data berikut ya.</p>
        <div class="form-group">
          <label>Nama Lengkap</label>
          <input type="text" id="obName" placeholder="Masukkan nama kamu">
        </div>
        <div class="form-group">
          <label>Email</label>
          <input type="email" id="obEmail" placeholder="email@contoh.com">
        </div>
        <div class="form-group">
          <label>Dapet informasi JAL University darimana?</label>
          <div class="source-grid" id="sourceGrid"></div>
        </div>
        <button class="btn-start" id="obStart" disabled>Mulai Chat 🚀</button>
      </div>
    </div>
  `;

  const sources = [
    { id: 'formulir_pendaftaran', label: '📋 Formulir Pendaftaran' },
    { id: 'media_sosial', label: '📱 Media Sosial' },
    { id: 'website', label: '🌐 Website' },
    { id: 'event', label: '🎓 Event' },
    { id: 'referral', label: '👥 Referral' },
    { id: 'lainnya', label: '📌 Lainnya' },
  ];

  const grid = document.getElementById('sourceGrid');
  let selectedSource = '';
  sources.forEach(s => {
    const btn = document.createElement('button');
    btn.className = 'source-option';
    btn.textContent = s.label;
    btn.onclick = () => {
      grid.querySelectorAll('.source-option').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedSource = s.id;
      checkForm();
    };
    grid.appendChild(btn);
  });

  const nameEl = document.getElementById('obName');
  const emailEl = document.getElementById('obEmail');
  const startBtn = document.getElementById('obStart');

  function checkForm() {
    startBtn.disabled = !(nameEl.value.trim() && emailEl.value.trim() && selectedSource);
  }
  nameEl.oninput = checkForm;
  emailEl.oninput = checkForm;

  startBtn.onclick = () => {
    const user = { name: nameEl.value.trim(), email: emailEl.value.trim().toLowerCase(), lead_source: selectedSource };
    localStorage.setItem('jal_user', JSON.stringify(user));
    renderChatbot();
  };
}
