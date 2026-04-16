/* Admin Chat Monitor & Intervention Page */
function renderAdminChat(app) {
  let selectedLeadId = null;
  let chartsContainer = null;

  app.innerHTML = `
    <div class="admin-tabs" style="padding: var(--space-4) var(--space-6);">
      <button class="admin-tab active" id="tab-monitor">💬 Chat Monitor</button>
      <button class="admin-tab" id="tab-categorization">📊 Categorization</button>
    </div>
    <div id="admin-content" style="height:calc(100% - 52px);overflow:auto"></div>`;

  document.getElementById('tab-monitor').onclick = () => showMonitor();
  document.getElementById('tab-categorization').onclick = () => showCategorization();

  function setActiveTab(id) {
    document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
    document.getElementById(id).classList.add('active');
  }

  async function showMonitor() {
    setActiveTab('tab-monitor');
    const content = document.getElementById('admin-content');
    content.innerHTML = `
      <div class="admin-layout">
        <div class="admin-chat-list">
          <div class="search-box"><input type="text" placeholder="🔍 Cari percakapan..." id="conv-search" /></div>
          <div id="conv-list"></div>
        </div>
        <div class="admin-chat-detail" id="chat-detail">
          <div class="empty-state">← Pilih percakapan untuk melihat detail</div>
        </div>
      </div>`;
    
    await loadConversations();
    document.getElementById('conv-search').oninput = (e) => filterConversations(e.target.value);
  }

  let allConversations = [];

  async function loadConversations() {
    const res = await fetch('/api/admin/conversations');
    const data = await res.json();
    allConversations = data.conversations || [];
    renderConversationList(allConversations);
  }

  function filterConversations(query) {
    const q = query.toLowerCase();
    const filtered = allConversations.filter(c =>
      (c.lead_name || '').toLowerCase().includes(q) ||
      (c.last_message_preview || '').toLowerCase().includes(q)
    );
    renderConversationList(filtered);
  }

  function renderConversationList(conversations) {
    const list = document.getElementById('conv-list');
    if (!list) return;
    list.innerHTML = '';
    conversations.forEach(conv => {
      const urgencyColors = { low: '#6b7280', medium: '#f59e0b', high: '#f97316', critical: '#ef4444' };
      const bgColor = urgencyColors[conv.urgency] || '#6b7280';
      const initial = (conv.lead_name || '?')[0].toUpperCase();
      const time = conv.last_timestamp ? new Date(conv.last_timestamp).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) : '';

      const item = document.createElement('div');
      item.className = `conversation-item ${selectedLeadId === conv.lead_id ? 'active' : ''}`;
      item.innerHTML = `
        <div class="conv-avatar" style="background:${bgColor}30;color:${bgColor}">${initial}</div>
        <div class="conv-info">
          <div class="conv-name">${conv.lead_name || 'Unknown'} ${conv.needs_review ? '<span class="needs-review-badge">NEEDS REVIEW</span>' : ''}</div>
          <div class="conv-preview">"${conv.last_message_preview || ''}"</div>
        </div>
        <div class="conv-meta">
          <div class="conv-time">${time}</div>
          ${createUrgencyBadge(conv.urgency).outerHTML}
        </div>`;
      item.onclick = () => loadChat(conv.lead_id);
      list.appendChild(item);
    });
  }

  async function loadChat(leadId) {
    selectedLeadId = leadId;
    renderConversationList(allConversations);

    const detail = document.getElementById('chat-detail');
    detail.innerHTML = '<div style="padding:var(--space-4);color:var(--text-muted)">Loading...</div>';

    const res = await fetch(`/api/admin/conversations/${leadId}`);
    const data = await res.json();
    const lead = data.lead_profile || {};
    const messages = data.messages || [];

    const needsIntervention = lead.urgency === 'critical' || messages.some(m => m.intent_confidence && m.intent_confidence < 0.6);

    detail.innerHTML = `
      <div class="chat-header" style="max-width:none">
        <div class="avatar" style="background:linear-gradient(135deg, var(--accent-tertiary), var(--accent-primary))">${(lead.name || '?')[0]}</div>
        <div class="info" style="flex:1">
          <h2>${lead.name || lead.session_id}</h2>
          <p>${lead.contact_type || 'unknown'} • ${lead.funnel_stage || 'awareness'} • ${lead.school_origin || 'N/A'}</p>
        </div>
        <div>${createUrgencyBadge(lead.urgency).outerHTML} ${createFunnelBadge(lead.funnel_stage).outerHTML}</div>
      </div>
      ${needsIntervention ? '<div style="padding:var(--space-2) var(--space-4);background:rgba(239,68,68,0.1);color:#ef4444;font-size:13px;text-align:center">⚠️ Percakapan ini memerlukan intervensi admin</div>' : ''}
      <div class="chat-messages" id="admin-chat-msgs" style="flex:1;max-width:none"></div>
      <div class="chat-input-area" style="max-width:none">
        <input type="text" id="admin-reply-input" placeholder="Reply sebagai admin..." />
        <button id="admin-reply-btn">Kirim</button>
      </div>`;

    const msgsEl = document.getElementById('admin-chat-msgs');
    messages.forEach(msg => msgsEl.appendChild(createChatBubble(msg)));
    setTimeout(() => { msgsEl.scrollTop = msgsEl.scrollHeight; }, 50);

    document.getElementById('admin-reply-btn').onclick = () => sendAdminReply(leadId);
    document.getElementById('admin-reply-input').onkeydown = (e) => { if (e.key === 'Enter') sendAdminReply(leadId); };
  }

  async function sendAdminReply(leadId) {
    const input = document.getElementById('admin-reply-input');
    const content = input.value.trim();
    if (!content) return;

    input.value = '';
    const res = await fetch(`/api/admin/conversations/${leadId}/reply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });

    if (res.ok) {
      const data = await res.json();
      const msgsEl = document.getElementById('admin-chat-msgs');
      const adminMsg = {
        direction: 'outbound', content, sender: 'admin',
        processing_log: { source: 'admin_manual' },
        created_at: data.timestamp
      };
      msgsEl.appendChild(createChatBubble(adminMsg));
      msgsEl.scrollTop = msgsEl.scrollHeight;
    }
  }

  async function showCategorization() {
    setActiveTab('tab-categorization');
    const content = document.getElementById('admin-content');
    content.innerHTML = `
      <div class="admin-categorization">
        <h2 style="margin-bottom:var(--space-4);font-size:var(--font-size-xl)">📊 Chat Categorization Dashboard</h2>
        <div id="cat-table-container"></div>
        <div id="cat-charts-container"></div>
      </div>`;

    chartsContainer = document.getElementById('cat-charts-container');
    const tableContainer = document.getElementById('cat-table-container');

    createCategoryTable(tableContainer, async (filters) => {
      await renderDynamicCharts(chartsContainer, filters);
    });

    // Initial chart render
    await renderDynamicCharts(chartsContainer, {});
  }

  showMonitor();
}
