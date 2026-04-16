/* Database Page — Full leads table with filters, search, sorting, pagination */
function renderDatabase() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <nav class="admin-nav">
      <span class="logo">JAL Admin</span>
      <a href="#/admin">💬 Chat Monitor</a>
      <a href="#/admin/dashboard">📊 Dashboard</a>
      <a href="#/admin/analytics">📈 Analytics</a>
      <a href="#/admin/database" class="active">📋 Database</a>
      <a href="#/admin/settings">⚙️ Settings</a>
    </nav>
    <div class="database-page">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
        <h1 style="font-size:24px;font-weight:700;">📋 Lead Database</h1>
        <button class="btn-export" onclick="window.open('/api/admin/export/leads/csv','_blank'); ToastManager.show('CSV export dimulai...','success');">📥 Export CSV</button>
      </div>

      <div class="filter-bar" id="dbFilterBar">
        <input type="text" id="dbSearch" placeholder="🔍 Cari nama / email...">
        <select id="dbFunnel">
          <option value="">Semua Funnel</option>
          <option value="awareness">Awareness</option>
          <option value="interest">Interest</option>
          <option value="consideration">Consideration</option>
          <option value="decision">Decision</option>
          <option value="enrolled">Enrolled</option>
        </select>
        <select id="dbUrgency">
          <option value="">Semua Urgency</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="critical">Critical</option>
        </select>
        <select id="dbSource">
          <option value="">Semua Source</option>
        </select>
        <select id="dbContactType">
          <option value="">Semua Tipe</option>
          <option value="student">Student</option>
          <option value="parent">Parent</option>
          <option value="counselor">Counselor</option>
          <option value="unknown">Unknown</option>
        </select>
      </div>

      <div class="data-table-wrapper">
        <table class="data-table" id="dbTable">
          <thead>
            <tr>
              <th>Nama</th>
              <th>Email</th>
              <th>HP</th>
              <th>Sekolah</th>
              <th>Kelas</th>
              <th>Program Minat</th>
              <th>Funnel</th>
              <th>Urgency</th>
              <th>Source</th>
              <th>Tipe</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody id="dbBody"></tbody>
        </table>
      </div>
      <div class="pagination" id="dbPagination"></div>
    </div>
  `;

  startNotificationPolling();
  populateSourceFilter();
  loadDatabaseTable(1);

  // Filter handlers
  const reload = () => loadDatabaseTable(1);
  document.getElementById('dbFunnel').onchange = reload;
  document.getElementById('dbUrgency').onchange = reload;
  document.getElementById('dbSource').onchange = reload;
  document.getElementById('dbContactType').onchange = reload;

  let searchTimeout;
  document.getElementById('dbSearch').oninput = () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(reload, 400);
  };
}

async function populateSourceFilter() {
  try {
    const res = await fetch('/api/dashboard/config');
    const config = await res.json();
    const select = document.getElementById('dbSource');
    (config.lead_sources || []).forEach(src => {
      const opt = document.createElement('option');
      opt.value = src.id;
      opt.textContent = src.label;
      select.appendChild(opt);
    });
  } catch(e) { /* ignore */ }
}

async function loadDatabaseTable(page) {
  const search = document.getElementById('dbSearch')?.value || '';
  const funnel = document.getElementById('dbFunnel')?.value || '';
  const urgency = document.getElementById('dbUrgency')?.value || '';
  const source = document.getElementById('dbSource')?.value || '';
  const contactType = document.getElementById('dbContactType')?.value || '';

  let url = `/api/leads?page=${page}&limit=20`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  if (funnel) url += `&stage=${funnel}`;
  if (urgency) url += `&urgency=${urgency}`;
  if (source) url += `&lead_source=${source}`;
  if (contactType) url += `&contact_type=${contactType}`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    const tbody = document.getElementById('dbBody');
    tbody.innerHTML = '';

    (data.data || []).forEach(lead => {
      const tr = document.createElement('tr');
      tr.style.cursor = 'pointer';
      tr.onclick = () => { window.location.hash = `#/admin/lead/${lead.id}`; };
      tr.innerHTML = `
        <td style="font-weight:600;">${lead.name || '-'}</td>
        <td style="font-size:12px;color:var(--text-secondary);">${lead.email || '-'}</td>
        <td style="font-size:12px;">${lead.phone_number || '-'}</td>
        <td style="font-size:12px;">${lead.school_origin || '-'}</td>
        <td style="font-size:12px;text-align:center;">${lead.kelas || '-'}</td>
        <td style="font-size:12px;">${lead.interested_program || '-'}</td>
        <td><span class="funnel-badge ${lead.funnel_stage || ''}">${lead.funnel_stage || '-'}</span></td>
        <td><span class="urgency-badge ${lead.urgency || ''}">${(lead.urgency || '-').toUpperCase()}</span></td>
        <td style="font-size:11px;">${(lead.lead_source || '-').replace(/_/g, ' ')}</td>
        <td style="font-size:11px;">${lead.contact_type || '-'}</td>
        <td style="font-size:11px;color:var(--text-muted);">${lead.created_at ? new Date(lead.created_at).toLocaleDateString('id-ID', {day:'2-digit',month:'short',year:'2-digit'}) : '-'}</td>
      `;
      tbody.appendChild(tr);
    });

    if ((data.data || []).length === 0) {
      tbody.innerHTML = '<tr><td colspan="11" style="text-align:center;color:var(--text-muted);padding:40px;">Tidak ada data ditemukan</td></tr>';
    }

    // Pagination
    const pag = document.getElementById('dbPagination');
    pag.innerHTML = '';
    const totalPages = data.total_pages || 1;
    if (totalPages > 1) {
      if (page > 1) {
        const prev = document.createElement('button');
        prev.textContent = '← Prev';
        prev.onclick = () => loadDatabaseTable(page - 1);
        pag.appendChild(prev);
      }
      const maxShow = Math.min(totalPages, 7);
      let start = Math.max(1, page - 3);
      let end = Math.min(totalPages, start + maxShow - 1);
      if (end - start < maxShow - 1) start = Math.max(1, end - maxShow + 1);

      for (let i = start; i <= end; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = i === page ? 'active' : '';
        btn.onclick = () => loadDatabaseTable(i);
        pag.appendChild(btn);
      }
      if (page < totalPages) {
        const next = document.createElement('button');
        next.textContent = 'Next →';
        next.onclick = () => loadDatabaseTable(page + 1);
        pag.appendChild(next);
      }
      pag.appendChild(Object.assign(document.createElement('span'), {
        textContent: `${data.total} leads total`
      }));
    }
  } catch(e) {
    console.error('Failed to load database:', e);
  }
}
