/* Analytics Page — detailed charts and categorization table */
function renderAnalytics() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <nav class="admin-nav">
      <span class="logo">JAL Admin</span>
      <a href="#/admin">💬 Chat Monitor</a>
      <a href="#/admin/dashboard">📊 Dashboard</a>
      <a href="#/admin/analytics" class="active">📈 Analytics</a>
    </nav>
    <div class="admin-categorization">
      <h1 style="font-size:24px;font-weight:700;margin-bottom:24px;">Analytics & Categorization</h1>
      
      <div class="filter-bar" id="filterBar">
        <select id="filterMacro">
          <option value="">Semua Macro Intent</option>
          <option value="INQUIRY">INQUIRY</option>
          <option value="TRANSACTIONAL">TRANSACTIONAL</option>
          <option value="SUPPORT">SUPPORT</option>
          <option value="AMBIGUOUS">AMBIGUOUS</option>
        </select>
        <select id="filterUrgency">
          <option value="">Semua Urgency</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="critical">Critical</option>
        </select>
        <select id="filterFunnel">
          <option value="">Semua Funnel</option>
          <option value="awareness">Awareness</option>
          <option value="interest">Interest</option>
          <option value="consideration">Consideration</option>
          <option value="decision">Decision</option>
          <option value="enrolled">Enrolled</option>
        </select>
      </div>

      <div class="data-table-wrapper">
        <table class="data-table" id="catTable">
          <thead>
            <tr>
              <th>Nama</th>
              <th>Pesan</th>
              <th>Macro</th>
              <th>Micro</th>
              <th>Funnel</th>
              <th>Urgency</th>
              <th>Confidence</th>
              <th>Waktu</th>
            </tr>
          </thead>
          <tbody id="catBody"></tbody>
        </table>
      </div>
      <div class="pagination" id="catPagination"></div>

      <div class="charts-grid" id="analyticsCharts" style="margin-top:32px;"></div>
    </div>
  `;

  startNotificationPolling();
  loadCategorizedMessages(1);
  loadAnalyticsCharts();

  // Filter handlers
  document.getElementById('filterMacro').onchange = () => loadCategorizedMessages(1);
  document.getElementById('filterUrgency').onchange = () => loadCategorizedMessages(1);
  document.getElementById('filterFunnel').onchange = () => loadCategorizedMessages(1);
}

async function loadCategorizedMessages(page) {
  const macro = document.getElementById('filterMacro').value;
  const urgency = document.getElementById('filterUrgency').value;
  const funnel = document.getElementById('filterFunnel').value;

  let url = `/api/categorization/messages?page=${page}&limit=15`;
  if (macro) url += `&macro_intent=${macro}`;
  if (urgency) url += `&urgency=${urgency}`;
  if (funnel) url += `&funnel_stage=${funnel}`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    const tbody = document.getElementById('catBody');
    tbody.innerHTML = '';

    (data.data || []).forEach(msg => {
      const tr = document.createElement('tr');
      tr.style.cursor = 'pointer';
      tr.onclick = () => { window.location.hash = `#/admin/lead/${msg.lead_id}`; };
      tr.innerHTML = `
        <td>${msg.name || '-'}</td>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${msg.content || '-'}</td>
        <td><span class="macro-badge ${msg.macro_intent || ''}">${msg.macro_intent || '-'}</span></td>
        <td style="font-size:12px;color:var(--text-secondary);">${msg.micro_intent || '-'}</td>
        <td><span class="funnel-badge ${msg.funnel_stage || ''}">${msg.funnel_stage || '-'}</span></td>
        <td><span class="urgency-badge ${msg.urgency || ''}">${(msg.urgency || '-').toUpperCase()}</span></td>
        <td style="font-size:12px;">${msg.intent_confidence != null ? (msg.intent_confidence*100).toFixed(0) + '%' : '-'}</td>
        <td style="font-size:11px;color:var(--text-muted);">${msg.created_at ? new Date(msg.created_at).toLocaleString('id-ID', {day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}) : '-'}</td>
      `;
      tbody.appendChild(tr);
    });

    // Pagination
    const pag = document.getElementById('catPagination');
    pag.innerHTML = '';
    const totalPages = data.total_pages || 1;
    if (totalPages > 1) {
      for (let i = 1; i <= Math.min(totalPages, 5); i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = i === page ? 'active' : '';
        btn.onclick = () => loadCategorizedMessages(i);
        pag.appendChild(btn);
      }
    }
  } catch(e) {
    console.error('Failed to load categorized messages:', e);
  }
}

async function loadAnalyticsCharts() {
  try {
    const res = await fetch('/api/categorization/chart-data');
    const data = await res.json();
    const grid = document.getElementById('analyticsCharts');
    grid.innerHTML = '';

    // Micro intent breakdown
    const microCard = document.createElement('div');
    microCard.className = 'chart-card';
    microCard.innerHTML = '<h3>🔬 Micro Intent Breakdown</h3>';
    const microCanvas = document.createElement('canvas');
    microCard.appendChild(microCanvas);
    grid.appendChild(microCard);

    const microDist = data.micro_intent_distribution || {};
    new Chart(microCanvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: Object.keys(microDist),
        datasets: [{ data: Object.values(microDist),
          backgroundColor: ['#3b82f6','#60a5fa','#818cf8','#8b5cf6','#a78bfa','#ef4444','#f87171','#6b7280'], borderRadius: 6, barThickness: 30 }]
      },
      options: { responsive: true, indexAxis: 'y', plugins: { legend: { display: false } },
        scales: { x: { ticks: { color: '#a0a0b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true },
                  y: { ticks: { color: '#a0a0b8', font: { size: 10 } }, grid: { display: false } } } }
    });

    // Daily volume
    const volumeCard = document.createElement('div');
    volumeCard.className = 'chart-card';
    volumeCard.innerHTML = '<h3>📈 Daily Message Volume</h3>';
    const volumeCanvas = document.createElement('canvas');
    volumeCard.appendChild(volumeCanvas);
    grid.appendChild(volumeCard);

    const daily = data.daily_volume || [];
    new Chart(volumeCanvas.getContext('2d'), {
      type: 'line',
      data: {
        labels: daily.map(d => d.date),
        datasets: [{ data: daily.map(d => d.count), borderColor: '#7c83ff', backgroundColor: 'rgba(124,131,255,0.1)',
          fill: true, tension: 0.4, pointBackgroundColor: '#7c83ff', pointRadius: 4 }]
      },
      options: { responsive: true, plugins: { legend: { display: false } },
        scales: { x: { ticks: { color: '#a0a0b8' }, grid: { display: false } },
                  y: { ticks: { color: '#a0a0b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true } } }
    });
  } catch(e) {
    console.error('Failed to load analytics charts:', e);
  }
}
