/* Lead Detail Page — profile + conversation + AI reasoning log */
function renderLeadDetail(leadId) {
  const app = document.getElementById('app');
  app.innerHTML = `
    <nav class="admin-nav">
      <span class="logo">JAL Admin</span>
      <a href="#/admin">💬 Chat Monitor</a>
      <a href="#/admin/dashboard">📊 Dashboard</a>
      <a href="#/admin/analytics">📈 Analytics</a>
    </nav>
    <div class="lead-detail-layout">
      <div class="lead-profile-card" id="profileCard">Loading...</div>
      <div class="lead-detail-content" id="detailContent">Loading...</div>
    </div>
  `;

  loadLeadDetail(leadId);
}

async function loadLeadDetail(leadId) {
  try {
    const res = await fetch(`/api/leads/${leadId}`);
    const lead = await res.json();

    // Profile card
    const profileCard = document.getElementById('profileCard');
    profileCard.innerHTML = `
      <h2>${lead.name || 'Unknown'}</h2>
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px;">
        ${lead.funnel_stage ? `<span class="funnel-badge ${lead.funnel_stage}">${lead.funnel_stage}</span>` : ''}
        ${lead.urgency ? `<span class="urgency-badge ${lead.urgency}">${lead.urgency}</span>` : ''}
        ${lead.macro_intent ? `<span class="macro-badge ${lead.macro_intent}">${lead.macro_intent}</span>` : ''}
      </div>
      ${profileField('Email', lead.email)}
      ${profileField('Nama', lead.name)}
      ${profileField('Tipe Kontak', lead.contact_type)}
      ${profileField('Sumber Lead', lead.lead_source)}
      ${profileField('Sekolah Asal', lead.school_origin)}
      ${profileField('Tipe Sekolah', lead.school_type)}
      ${profileField('Kelas', lead.kelas)}
      ${profileField('Umur', lead.umur)}
      ${profileField('Program Diminati', lead.interested_program)}
      ${profileField('Kebangsaan', lead.nationality)}
      ${profileField('Prestasi Akademik', lead.academic_achievement)}
      ${profileField('Financial Concern', lead.financial_concern ? 'Ya ⚠️' : 'Tidak')}
      ${profileField('Micro Intent', lead.micro_intent)}
      ${profileField('Bergabung', lead.created_at ? new Date(lead.created_at).toLocaleDateString('id-ID') : '-')}
    `;

    // Detail content — messages + reasoning log
    const detailContent = document.getElementById('detailContent');
    detailContent.innerHTML = '';

    // Funnel Journey Timeline
    const funnelJourney = document.createElement('div');
    funnelJourney.style.cssText = 'display:flex;gap:8px;margin-bottom:24px;padding:16px;background:var(--bg-card);border-radius:12px;border:1px solid var(--border-color);overflow-x:auto;';
    const stages = ['awareness','interest','consideration','decision','enrolled'];
    const currentIdx = stages.indexOf(lead.funnel_stage || 'awareness');
    stages.forEach((stage, idx) => {
      const pill = document.createElement('div');
      pill.style.cssText = `padding:6px 14px;border-radius:20px;font-size:12px;font-weight:500;white-space:nowrap;${idx <= currentIdx ? 'background:var(--accent-primary);color:white;' : 'background:var(--bg-glass);color:var(--text-muted);'}`;
      pill.textContent = stage;
      funnelJourney.appendChild(pill);
      if (idx < stages.length - 1) {
        const arrow = document.createElement('span');
        arrow.style.cssText = `color:${idx < currentIdx ? 'var(--accent-primary)' : 'var(--text-muted)'};align-self:center;`;
        arrow.textContent = '→';
        funnelJourney.appendChild(arrow);
      }
    });
    detailContent.appendChild(funnelJourney);

    // Conversation section
    const convTitle = document.createElement('h3');
    convTitle.style.cssText = 'font-size:16px;font-weight:600;margin-bottom:12px;';
    convTitle.textContent = '💬 Conversation History';
    detailContent.appendChild(convTitle);

    const messages = lead.messages || [];
    const msgContainer = document.createElement('div');
    msgContainer.style.cssText = 'display:flex;flex-direction:column;gap:8px;margin-bottom:24px;';
    messages.forEach(msg => msgContainer.appendChild(createChatBubble(msg)));
    detailContent.appendChild(msgContainer);

    // AI Reasoning Log per message
    const logTitle = document.createElement('h3');
    logTitle.style.cssText = 'font-size:16px;font-weight:600;margin-bottom:12px;';
    logTitle.textContent = '🔍 AI Processing Logs';
    detailContent.appendChild(logTitle);

    const inbound = messages.filter(m => m.direction === 'inbound');
    inbound.forEach((msg, idx) => {
      let log = msg.processing_log;
      if (typeof log === 'string') { try { log = JSON.parse(log); } catch(e) { log = {}; } }
      
      const section = document.createElement('div');
      section.style.cssText = 'margin-bottom:20px;padding:16px;background:#121220;border-radius:12px;border:1px solid var(--border-color);';
      section.innerHTML = `<div style="font-size:13px;font-weight:600;color:var(--text-primary);margin-bottom:10px;">Pesan ${idx+1}: "${(msg.content||'').substring(0,80)}"</div>`;

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
          ${step.confidence != null ? `<div style="margin-top:4px;"><div class="confidence-bar"><div class="fill ${step.confidence >= 0.8 ? 'high' : step.confidence >= 0.6 ? 'medium' : 'low'}" style="width:${step.confidence*100}%"></div></div></div>` : ''}
        `;
        section.appendChild(stepEl);
      });
      detailContent.appendChild(section);
    });

  } catch(e) {
    console.error('Failed to load lead detail:', e);
  }
}

function profileField(label, value) {
  if (!value && value !== 0) return '';
  return `<div class="profile-field"><div class="label">${label}</div><div class="value">${value}</div></div>`;
}
