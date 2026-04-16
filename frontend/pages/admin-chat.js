/* Admin Chat Monitor — 3-panel layout with AI logging sidebar */
function renderAdminChat() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <nav class="admin-nav">
      <span class="logo">JAL Admin</span>
      <a href="#/admin" class="active">💬 Chat Monitor</a>
      <a href="#/admin/dashboard">📊 Dashboard</a>
      <a href="#/admin/analytics">📈 Analytics</a>
    </nav>
    <div class="admin-layout" id="adminLayout">
      <div class="admin-chat-list" id="chatList">
        <div class="search-box"><input type="text" id="chatSearch" placeholder="Cari nama / email..."></div>
        <div id="conversationList"></div>
      </div>
      <div class="admin-chat-detail" id="chatDetail">
        <div class="empty-state">Pilih percakapan untuk melihat detail</div>
      </div>
      <div id="loggingSidebar"></div>
    </div>
  `;

  const loggingSidebar = document.getElementById('loggingSidebar');
  loggingSidebar.appendChild(createAILoggingSidebar([]));

  startNotificationPolling();
  loadConversations();

  document.getElementById('chatSearch').oninput = (e) => {
    const q = e.target.value.toLowerCase();
    document.querySelectorAll('.conversation-item').forEach(el => {
      el.style.display = el.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  };
}

async function loadConversations() {
  try {
    const res = await fetch('/api/admin/chat/conversations');
    const data = await res.json();
    const list = document.getElementById('conversationList');
    list.innerHTML = '';

    (data.conversations || []).forEach(conv => {
      const el = document.createElement('div');
      el.className = 'conversation-item';
      el.dataset.leadId = conv.lead_id;

      // Avatar color based on urgency
      const colors = { low: '#6b7280', medium: '#f59e0b', critical: '#ef4444' };
      const bgColor = colors[conv.urgency] || '#6b7280';
      const initials = (conv.lead_name || 'U').substring(0, 2).toUpperCase();

      el.innerHTML = `
        <div class="conv-avatar" style="background:${bgColor};color:white">${initials}</div>
        <div class="conv-info">
          <div class="conv-name">
            ${conv.lead_name || 'Unknown'}
            ${conv.needs_review ? '<span class="needs-review-badge">REVIEW</span>' : ''}
          </div>
          <div class="conv-preview">${conv.last_message_preview || 'No messages'}</div>
          <div class="conv-badges">
            ${conv.macro_intent ? `<span class="macro-badge ${conv.macro_intent}" style="font-size:9px;padding:1px 5px;">${conv.macro_intent}</span>` : ''}
            ${conv.funnel_stage ? `<span class="funnel-badge ${conv.funnel_stage}" style="font-size:9px;padding:1px 5px;">${conv.funnel_stage}</span>` : ''}
            ${conv.urgency ? `<span class="urgency-badge ${conv.urgency}" style="font-size:9px;padding:1px 5px;">${conv.urgency}</span>` : ''}
          </div>
        </div>
        <div class="conv-meta">
          <div class="conv-time">${conv.last_timestamp ? new Date(conv.last_timestamp).toLocaleTimeString('id-ID', {hour:'2-digit',minute:'2-digit'}) : ''}</div>
        </div>
      `;
      el.onclick = () => selectConversation(conv.lead_id);
      list.appendChild(el);
    });
  } catch(e) {
    console.error('Failed to load conversations:', e);
  }
}

async function selectConversation(leadId) {
  document.querySelectorAll('.conversation-item').forEach(el => el.classList.remove('active'));
  document.querySelector(`.conversation-item[data-lead-id="${leadId}"]`)?.classList.add('active');

  try {
    const res = await fetch(`/api/admin/chat/conversations/${leadId}`);
    const data = await res.json();
    const detail = document.getElementById('chatDetail');

    detail.innerHTML = `
      <div class="chat-header" style="background:var(--bg-secondary);">
        <div class="info">
          <h2>${data.lead_profile?.name || 'Unknown'}</h2>
          <p>${data.lead_profile?.email || ''} • ${data.lead_profile?.funnel_stage || 'awareness'} • ${data.lead_profile?.lead_source || ''}</p>
        </div>
        <a href="#/admin/lead/${leadId}" style="color:var(--accent-primary);font-size:12px;text-decoration:none;">Detail →</a>
      </div>
      <div class="chat-messages" id="adminMessages" style="flex:1;overflow-y:auto;padding:16px;"></div>
      <div class="chat-input-area">
        <input type="text" id="adminReplyInput" placeholder="Balas sebagai admin...">
        <button id="adminReplySend">Kirim</button>
      </div>
    `;

    const msgsEl = document.getElementById('adminMessages');
    const messages = data.messages || [];
    messages.forEach(msg => msgsEl.appendChild(createChatBubble(msg)));
    msgsEl.scrollTop = msgsEl.scrollHeight;

    // Update logging sidebar
    const sidebar = document.getElementById('loggingSidebar');
    sidebar.innerHTML = '';
    sidebar.appendChild(createAILoggingSidebar(messages));

    // Admin reply
    const replyInput = document.getElementById('adminReplyInput');
    const replySend = document.getElementById('adminReplySend');
    const sendReply = async () => {
      const content = replyInput.value.trim();
      if (!content) return;
      replyInput.value = '';
      try {
        await fetch(`/api/admin/chat/conversations/${leadId}/reply`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content }),
        });
        msgsEl.appendChild(createChatBubble({ direction: 'outbound', sender: 'admin', content, created_at: new Date().toISOString() }));
        msgsEl.scrollTop = msgsEl.scrollHeight;
      } catch(e) { console.error(e); }
    };
    replySend.onclick = sendReply;
    replyInput.onkeydown = (e) => { if (e.key === 'Enter') sendReply(); };
  } catch(e) {
    console.error('Failed to load conversation:', e);
  }
}
