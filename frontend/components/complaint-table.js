/* Complaint Table Component */
function createComplaintTable(container) {
  container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;">Loading complaints...</div>';
  fetch('/api/admin/complaints')
    .then(r => r.json())
    .then(data => {
      container.innerHTML = '';
      const complaints = data.complaints || [];
      if (complaints.length === 0) {
        container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:40px;">Tidak ada keluhan saat ini 🎉</div>';
        return;
      }
      const header = document.createElement('div');
      header.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;';
      header.innerHTML = `<h3 style="font-size:16px;font-weight:600;">📋 Keluhan / Complaint Log</h3><span style="font-size:12px;color:var(--text-muted);">${complaints.filter(c=>c.status==='open').length} open</span>`;
      container.appendChild(header);

      complaints.forEach(c => {
        const row = document.createElement('div');
        row.className = `complaint-row ${c.status === 'resolved' ? 'resolved' : ''}`;
        row.innerHTML = `
          <input type="checkbox" class="complaint-checkbox" ${c.status === 'resolved' ? 'checked disabled' : ''} data-id="${c.id}">
          <div class="complaint-text">${c.description || '-'}</div>
          <div class="complaint-meta">
            <div>${c.lead_name || ''} (${c.lead_email || ''})</div>
            <div>${c.status === 'resolved' ? '✅ Resolved' : '🔴 Open'}</div>
          </div>
        `;
        const checkbox = row.querySelector('input');
        if (c.status !== 'resolved') {
          checkbox.onchange = async () => {
            try {
              await fetch(`/api/admin/complaints/${c.id}/resolve`, { method: 'PATCH' });
              row.classList.add('resolved');
              checkbox.disabled = true;
              ToastManager.show('Keluhan berhasil di-resolve ✅', 'success');
            } catch(e) { checkbox.checked = false; }
          };
        }
        container.appendChild(row);
      });
    });
}
