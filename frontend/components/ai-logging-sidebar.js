/* AI Logging Sidebar Component */
function createAILoggingSidebar(messages) {
  const sidebar = document.createElement('div');
  sidebar.className = 'ai-logging-sidebar';

  const header = document.createElement('div');
  header.className = 'sidebar-header';
  header.innerHTML = `<h3>🔍 AI Reasoning Log</h3>`;
  sidebar.appendChild(header);

  if (!messages || messages.length === 0) {
    const empty = document.createElement('div');
    empty.style.cssText = 'color: var(--text-muted); font-size: var(--font-size-sm); text-align: center; padding: 40px 0;';
    empty.textContent = 'Pilih pesan untuk melihat AI reasoning log';
    sidebar.appendChild(empty);
    return sidebar;
  }

  // Show reasoning traces for selected messages
  const inbound = messages.filter(m => m.direction === 'inbound');
  const latestInbound = inbound[inbound.length - 1];
  if (!latestInbound) { return sidebar; }

  let processingLog = latestInbound.processing_log;
  if (typeof processingLog === 'string') {
    try { processingLog = JSON.parse(processingLog); } catch(e) { processingLog = {}; }
  }
  if (!processingLog) processingLog = {};

  // Show message info
  const msgInfo = document.createElement('div');
  msgInfo.style.cssText = 'margin-bottom: 16px; padding: 12px; background: var(--bg-glass); border-radius: 8px; font-size: 12px;';
  msgInfo.innerHTML = `
    <div style="color: var(--text-muted); margin-bottom: 4px;">PESAN TERAKHIR</div>
    <div style="color: var(--text-primary); margin-bottom: 8px;">"${(latestInbound.content || '').substring(0, 100)}${(latestInbound.content || '').length > 100 ? '...' : ''}"</div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;">
      ${processingLog.macro_intent ? `<span class="macro-badge ${processingLog.macro_intent}">${processingLog.macro_intent}</span>` : ''}
      ${processingLog.micro_intent ? `<span style="font-size:10px;color:var(--text-secondary)">${processingLog.micro_intent}</span>` : ''}
    </div>
  `;
  sidebar.appendChild(msgInfo);

  // Reasoning trace
  const traces = processingLog.reasoning_trace || [];
  traces.forEach(step => {
    const stepEl = document.createElement('div');
    stepEl.className = 'agent-step';
    stepEl.innerHTML = `
      <div class="agent-name">${step.agent || 'Agent'} <span class="time-inline">${step.time_ms || 0}ms</span></div>
      <div class="react-label thought">💭 Thought</div>
      <div class="react-content">${step.thought || '-'}</div>
      <div class="react-label action">⚡ Action</div>
      <div class="react-content">${step.action || '-'}</div>
      <div class="react-label observation">👁 Observation</div>
      <div class="react-content">${step.observation || '-'}</div>
      ${step.confidence != null ? `<div style="margin-top:6px;"><div class="confidence-bar"><div class="fill ${step.confidence >= 0.8 ? 'high' : step.confidence >= 0.6 ? 'medium' : 'low'}" style="width:${step.confidence*100}%"></div></div><span class="confidence-inline">${(step.confidence*100).toFixed(0)}%</span></div>` : ''}
    `;
    sidebar.appendChild(stepEl);
  });

  // Full log button
  if (traces.length > 0) {
    const fullBtn = document.createElement('button');
    fullBtn.className = 'full-log-btn';
    fullBtn.textContent = '📋 Baca Full Logging';
    fullBtn.onclick = () => showFullLogModal(messages);
    sidebar.appendChild(fullBtn);
  }

  return sidebar;
}

function showFullLogModal(messages) {
  const overlay = document.createElement('div');
  overlay.className = 'log-modal-overlay';
  overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };

  const modal = document.createElement('div');
  modal.className = 'log-modal';
  modal.innerHTML = `
    <div class="modal-header">
      <h2>📋 Full AI Processing Log</h2>
      <button class="modal-close" onclick="this.closest('.log-modal-overlay').remove()">✕</button>
    </div>
  `;

  const inbound = messages.filter(m => m.direction === 'inbound');
  inbound.forEach((msg, idx) => {
    let log = msg.processing_log;
    if (typeof log === 'string') { try { log = JSON.parse(log); } catch(e) { log = {}; } }

    const section = document.createElement('div');
    section.style.cssText = 'margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid var(--border-color);';
    section.innerHTML = `<div style="font-size:14px;font-weight:600;color:var(--text-primary);margin-bottom:12px;">Pesan ${idx+1}: "${(msg.content||'').substring(0,80)}"</div>`;

    const traces = (log && log.reasoning_trace) || [];
    traces.forEach(step => {
      const stepEl = document.createElement('div');
      stepEl.className = 'agent-step';
      stepEl.innerHTML = `
        <div class="agent-name">${step.agent || 'Agent'} <span class="time-inline">${step.time_ms || 0}ms</span></div>
        <div class="react-label thought">💭 Thought</div>
        <div class="react-content">${step.thought || '-'}</div>
        <div class="react-label action">⚡ Action</div>
        <div class="react-content">${step.action || '-'}</div>
        <div class="react-label observation">👁 Observation</div>
        <div class="react-content">${step.observation || '-'}</div>
      `;
      section.appendChild(stepEl);
    });

    modal.appendChild(section);
  });

  overlay.appendChild(modal);
  document.body.appendChild(overlay);
}
