/* Lead Detail Page */
async function renderLeadDetail(app, leadId) {
  const content = document.querySelector('.dashboard-content') || app;
  content.innerHTML = '<div style="padding:var(--space-6);color:var(--text-muted)">Loading lead detail...</div>';

  try {
    const res = await fetch(`/api/leads/${leadId}`);
    if (!res.ok) throw new Error('Lead not found');
    const lead = await res.json();

    content.innerHTML = `
      <div class="lead-detail-layout">
        <div class="lead-profile-card">
          <a href="#/admin" style="color:var(--text-muted);text-decoration:none;font-size:13px">← Kembali</a>
          <h2 style="margin-top:var(--space-3)">${lead.name || lead.session_id}</h2>
          <div style="margin: var(--space-3) 0">${createUrgencyBadge(lead.urgency).outerHTML} ${createFunnelBadge(lead.funnel_stage).outerHTML}</div>
          <div class="profile-field"><div class="label">Contact Type</div><div class="value">${lead.contact_type || '-'}</div></div>
          <div class="profile-field"><div class="label">Language</div><div class="value">${lead.language_pref || '-'}</div></div>
          <div class="profile-field"><div class="label">Sekolah Asal</div><div class="value">${lead.school_origin || '-'}</div></div>
          <div class="profile-field"><div class="label">Tipe Sekolah</div><div class="value">${lead.school_type || '-'}</div></div>
          <div class="profile-field"><div class="label">Program Diminati</div><div class="value">${lead.interested_program || '-'}</div></div>
          <div class="profile-field"><div class="label">Nationality</div><div class="value">${lead.nationality || '-'}</div></div>
          <div class="profile-field"><div class="label">Financial Concern</div><div class="value">${lead.financial_concern ? '⚠️ Ya' : 'Tidak'}</div></div>
          <div class="profile-field"><div class="label">Channel</div><div class="value">${lead.channel || '-'}</div></div>
          <div class="profile-field"><div class="label">Created</div><div class="value">${lead.created_at ? new Date(lead.created_at).toLocaleString('id-ID') : '-'}</div></div>
          
          ${(lead.next_actions || []).length > 0 ? `
          <h3 style="margin-top:var(--space-5);font-size:var(--font-size-base)">📋 Next Actions</h3>
          ${lead.next_actions.map(a => `
            <div style="padding:var(--space-3);margin-top:var(--space-2);background:var(--bg-glass);border-radius:var(--border-radius-sm);font-size:13px">
              <strong>${a.action_type}</strong> ${createUrgencyBadge(a.priority).outerHTML}
              <div style="color:var(--text-muted);margin-top:4px">${a.action_detail}</div>
            </div>`).join('')}` : ''}
        </div>
        <div class="lead-detail-content">
          <h3 style="margin-bottom:var(--space-4)">💬 Conversation History</h3>
          <div id="lead-chat-msgs" style="display:flex;flex-direction:column;gap:var(--space-3)"></div>
          
          <h3 style="margin-top:var(--space-8);margin-bottom:var(--space-4)">🔍 Processing Logs</h3>
          <div id="lead-proc-logs"></div>
        </div>
      </div>`;

    // Render messages
    const msgsEl = document.getElementById('lead-chat-msgs');
    (lead.messages || []).forEach(msg => {
      msgsEl.appendChild(createChatBubble(msg));
    });

    // Render processing logs
    const logsEl = document.getElementById('lead-proc-logs');
    (lead.messages || []).filter(m => m.processing_log).forEach(msg => {
      const wrapper = document.createElement('div');
      wrapper.style.cssText = 'margin-bottom:var(--space-5);padding:var(--space-4);background:var(--bg-card);border-radius:var(--border-radius-md);border:1px solid var(--border-color)';
      wrapper.innerHTML = `<div style="font-size:13px;color:var(--text-muted);margin-bottom:var(--space-2)">📝 "${(msg.content || '').slice(0, 60)}..."</div>`;
      wrapper.appendChild(createProcessingLog(msg.processing_log));
      logsEl.appendChild(wrapper);
    });

  } catch (err) {
    content.innerHTML = `<div style="padding:var(--space-6);color:var(--urgency-critical)">Error: ${err.message}</div>`;
  }
}
