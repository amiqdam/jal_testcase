/* Chatbot Page — User-facing chat with landing, onboarding, and continue options */

function renderChatbot() {
  const app = document.getElementById('app');
  
  // Always show landing page first — no auto-login from localStorage
  renderLanding(app);
}

/* ========== Landing Page ========== */
function renderLanding(app) {
  app.innerHTML = `
    <div class="landing-overlay">
      <div class="landing-card">
        <div class="landing-logo">🎓</div>
        <h1 class="landing-title">JAL University</h1>
        <p class="landing-subtitle">AI Asisten Admisi</p>
        <p class="landing-desc">Selamat datang! Pilih opsi di bawah untuk memulai percakapan.</p>
        <div class="landing-actions">
          <button class="landing-btn landing-btn-new" id="btnNewChat">
            <span class="landing-btn-icon">✨</span>
            <span class="landing-btn-text">
              <strong>Chat Baru</strong>
              <small>Mulai percakapan baru dengan mengisi data diri</small>
            </span>
          </button>
          <button class="landing-btn landing-btn-continue" id="btnContinueChat">
            <span class="landing-btn-icon">💬</span>
            <span class="landing-btn-text">
              <strong>Lanjutkan Chat</strong>
              <small>Masuk dengan nama & email untuk melanjutkan</small>
            </span>
          </button>
        </div>
      </div>
    </div>
  `;

  document.getElementById('btnNewChat').onclick = () => renderOnboarding(app);
  document.getElementById('btnContinueChat').onclick = () => renderContinueForm(app);
}

/* ========== New Chat — Full Onboarding ========== */
function renderOnboarding(app) {
  app.innerHTML = `
    <div class="onboarding-overlay">
      <div class="onboarding-card">
        <button class="back-btn" id="obBack">← Kembali</button>
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

  document.getElementById('obBack').onclick = () => renderLanding(app);

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
    startChat(user);
  };
}

/* ========== Continue Chat — Name + Email lookup ========== */
function renderContinueForm(app) {
  app.innerHTML = `
    <div class="onboarding-overlay">
      <div class="onboarding-card">
        <button class="back-btn" id="contBack">← Kembali</button>
        <h2>Lanjutkan Chat 💬</h2>
        <p>Masukkan nama dan email yang sudah terdaftar untuk melanjutkan percakapan.</p>
        <div class="form-group">
          <label>Nama Lengkap</label>
          <input type="text" id="contName" placeholder="Masukkan nama kamu">
        </div>
        <div class="form-group">
          <label>Email</label>
          <input type="email" id="contEmail" placeholder="email@contoh.com">
        </div>
        <div id="contError" class="form-error" style="display:none;"></div>
        <button class="btn-start" id="contStart" disabled>Masuk 🔑</button>
      </div>
    </div>
  `;

  document.getElementById('contBack').onclick = () => renderLanding(app);

  const nameEl = document.getElementById('contName');
  const emailEl = document.getElementById('contEmail');
  const startBtn = document.getElementById('contStart');
  const errorEl = document.getElementById('contError');

  function checkForm() {
    startBtn.disabled = !(nameEl.value.trim() && emailEl.value.trim());
    errorEl.style.display = 'none';
  }
  nameEl.oninput = checkForm;
  emailEl.oninput = checkForm;

  startBtn.onclick = async () => {
    const email = emailEl.value.trim().toLowerCase();
    const name = nameEl.value.trim();

    startBtn.disabled = true;
    startBtn.textContent = 'Mencari...';

    try {
      const res = await fetch(`/api/chat/history/${encodeURIComponent(email)}`);
      const data = await res.json();

      if (!data.lead_id) {
        // No history found
        errorEl.innerHTML = '⚠️ Tidak ditemukan riwayat chat untuk email ini. Silakan mulai <strong>Chat Baru</strong>.';
        errorEl.style.display = 'block';
        startBtn.disabled = false;
        startBtn.textContent = 'Masuk 🔑';
        return;
      }

      // History found — proceed to chat
      const user = { name, email };
      localStorage.setItem('jal_user', JSON.stringify(user));
      startChat(user);
    } catch (e) {
      errorEl.innerHTML = '❌ Terjadi kesalahan koneksi. Silakan coba lagi.';
      errorEl.style.display = 'block';
      startBtn.disabled = false;
      startBtn.textContent = 'Masuk 🔑';
    }
  };
}

/* ========== Chat Interface ========== */
function startChat(stored) {
  const app = document.getElementById('app');

  app.innerHTML = `
    <div class="chat-container">
      <div class="chat-header">
        <div class="avatar">🎓</div>
        <div class="info">
          <h2>JAL University</h2>
          <p>AI Asisten Admisi • Online</p>
        </div>
        <button class="chat-exit-btn" id="chatExit" title="Keluar">✕</button>
      </div>
      <div class="chat-messages" id="chatMessages"></div>
      <div class="chat-input-area">
        <input type="text" id="chatInput" placeholder="Ketik pertanyaan..." autocomplete="off">
        <button id="chatSend">Kirim</button>
      </div>
    </div>
  `;

  document.getElementById('chatExit').onclick = () => {
    localStorage.removeItem('jal_user');
    renderChatbot();
  };

  const messagesEl = document.getElementById('chatMessages');
  const inputEl = document.getElementById('chatInput');
  const sendBtn = document.getElementById('chatSend');

  let lastMessageCount = -1;
  let pollingInterval = null;

  async function loadHistory() {
    try {
      const res = await fetch(`/api/chat/history/${encodeURIComponent(stored.email)}`);
      const data = await res.json();
      
      if (!data.messages) return;
      
      if (data.messages.length > lastMessageCount) {
        messagesEl.innerHTML = '';
        
        // Render welcome message
        messagesEl.appendChild(createChatBubble({ direction: 'outbound', content: `Halo ${stored.name}! 👋\nSelamat datang di JAL University.\nAda yang bisa saya bantu tentang pendaftaran, program studi, beasiswa, atau informasi kampus?`, created_at: new Date().toISOString() }));
        
        // Render Quick start options only if no messages yet
        if (data.messages.length === 0) {
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
        }
        
        // Render history
        data.messages.forEach(msg => {
          let sender = msg.direction === 'inbound' ? 'user' : 'bot';
          if (msg.direction === 'outbound' && msg.processing_log && msg.processing_log.includes('admin_manual')) {
            sender = 'admin';
          }
          messagesEl.appendChild(createChatBubble({ sender, content: msg.content, created_at: msg.created_at }));
        });
        
        lastMessageCount = data.messages.length;
        messagesEl.scrollTop = messagesEl.scrollHeight;
      }
    } catch (e) {
      console.error("Failed to load history", e);
    }
  }

  // Initial load
  loadHistory();
  
  // Start polling
  pollingInterval = setInterval(loadHistory, 3000);

  // Clean up interval when navigating away
  const observer = new MutationObserver((mutations) => {
    if (!document.body.contains(app)) {
      clearInterval(pollingInterval);
      observer.disconnect();
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });

  async function sendMessage(content, quickIntent) {
    if (!content.trim()) return;
    inputEl.value = '';

    // User bubble immediately for optimistic UI
    messagesEl.appendChild(createChatBubble({ direction: 'inbound', content, created_at: new Date().toISOString() }));
    lastMessageCount++; // manually increment so polling doesn't wipe it before server returns

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
      
      // Wait for next polling to show the bot response, or we can just call loadHistory
      loadHistory();
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
