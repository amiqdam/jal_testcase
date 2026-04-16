/* Dashboard Page — Admin overview with stats, charts, and export */
function renderDashboard() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <nav class="admin-nav">
      <span class="logo">JAL Admin</span>
      <a href="#/admin">💬 Chat Monitor</a>
      <a href="#/admin/dashboard" class="active">📊 Dashboard</a>
      <a href="#/admin/analytics">📈 Analytics</a>
      <a href="#/admin/database">📋 Database</a>
      <a href="#/admin/settings">⚙️ Settings</a>
    </nav>
    <div class="dashboard-content" id="dashContent">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
        <h1 style="font-size:24px;font-weight:700;">Dashboard Overview</h1>
        <button class="btn-export" onclick="exportCSV()">📥 Export CSV</button>
      </div>
      <div class="stat-cards" id="statCards"></div>
      <div id="complaintSection" style="margin-top:24px;"></div>
      <div class="charts-grid" id="chartsGrid"></div>
    </div>
  `;

  startNotificationPolling();
  loadDashboardData();
}

async function loadDashboardData() {
  try {
    const [summaryRes, chartRes] = await Promise.all([
      fetch('/api/dashboard/summary'),
      fetch('/api/categorization/chart-data'),
    ]);
    const summary = await summaryRes.json();
    const charts = await chartRes.json();

    // Stat cards
    const statCards = document.getElementById('statCards');
    statCards.innerHTML = '';
    const stats = [
      { label: 'Total Leads', value: summary.total_leads || 0 },
      { label: 'Baru Hari Ini', value: summary.new_today || 0, trend: { text: 'hari ini', direction: 'up' } },
      { label: '⚠️ Perlu Perhatian', value: summary.attention_needed || 0, trend: summary.attention_needed > 0 ? { text: 'urgent', direction: 'down' } : null },
    ];
    // Add funnel summary
    const funnelDist = summary.funnel_distribution || {};
    stats.push({ label: 'Enrolled', value: funnelDist.enrolled || 0, trend: { text: 'terdaftar', direction: 'up' } });
    stats.forEach(s => statCards.appendChild(createStatCard(s.label, s.value, s.trend)));

    // Complaint section
    const complaintSection = document.getElementById('complaintSection');
    createComplaintTable(complaintSection);

    // Charts
    const chartsGrid = document.getElementById('chartsGrid');
    chartsGrid.innerHTML = '';

    // Funnel chart
    const funnelCard = document.createElement('div');
    funnelCard.className = 'chart-card';
    funnelCard.innerHTML = '<h3>📊 Funnel Distribution</h3>';
    const funnelCanvas = document.createElement('canvas');
    funnelCard.appendChild(funnelCanvas);
    chartsGrid.appendChild(funnelCard);

    const funnel = charts.funnel || [];
    new Chart(funnelCanvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: funnel.map(f => f.stage),
        datasets: [{ data: funnel.map(f => f.count),
          backgroundColor: ['#60a5fa','#3b82f6','#6366f1','#8b5cf6','#10b981'], borderRadius: 8, barThickness: 40 }]
      },
      options: { responsive: true, plugins: { legend: { display: false } },
        scales: { x: { ticks: { color: '#a0a0b8' }, grid: { display: false } },
                  y: { ticks: { color: '#a0a0b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true } } }
    });

    // Macro intent chart
    const intentCard = document.createElement('div');
    intentCard.className = 'chart-card';
    intentCard.innerHTML = '<h3>🏷️ Macro Intent Distribution</h3>';
    const intentCanvas = document.createElement('canvas');
    intentCard.appendChild(intentCanvas);
    chartsGrid.appendChild(intentCard);

    const intentDist = charts.macro_intent_distribution || {};
    new Chart(intentCanvas.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: Object.keys(intentDist),
        datasets: [{ data: Object.values(intentDist),
          backgroundColor: ['#3b82f6','#8b5cf6','#ef4444','#6b7280'] }]
      },
      options: { responsive: true, plugins: { legend: { position: 'bottom', labels: { color: '#a0a0b8', font: { size: 11 } } } } }
    });

    // Urgency chart
    const urgencyCard = document.createElement('div');
    urgencyCard.className = 'chart-card';
    urgencyCard.innerHTML = '<h3>🚨 Urgency Distribution</h3>';
    const urgencyCanvas = document.createElement('canvas');
    urgencyCard.appendChild(urgencyCanvas);
    chartsGrid.appendChild(urgencyCard);

    const urgencyDist = charts.urgency_distribution || {};
    new Chart(urgencyCanvas.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: Object.keys(urgencyDist),
        datasets: [{ data: Object.values(urgencyDist),
          backgroundColor: ['#6b7280','#f59e0b','#ef4444'] }]
      },
      options: { responsive: true, plugins: { legend: { position: 'bottom', labels: { color: '#a0a0b8', font: { size: 11 } } } } }
    });

    // Lead source chart
    const sourceCard = document.createElement('div');
    sourceCard.className = 'chart-card';
    sourceCard.innerHTML = '<h3>📡 Lead Source Distribution</h3>';
    const sourceCanvas = document.createElement('canvas');
    sourceCard.appendChild(sourceCanvas);
    chartsGrid.appendChild(sourceCard);

    const sourceDist = charts.source_distribution || {};
    new Chart(sourceCanvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: Object.keys(sourceDist),
        datasets: [{ data: Object.values(sourceDist),
          backgroundColor: ['#7c83ff','#4ecdc4','#ff6b9d','#ffd93d','#60a5fa','#6b7280'], borderRadius: 6, barThickness: 35 }]
      },
      options: { responsive: true, indexAxis: 'y', plugins: { legend: { display: false } },
        scales: { x: { ticks: { color: '#a0a0b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true },
                  y: { ticks: { color: '#a0a0b8' }, grid: { display: false } } } }
    });

  } catch(e) {
    console.error('Dashboard load failed:', e);
  }
}

function exportCSV() {
  window.open('/api/admin/export/leads/csv', '_blank');
  ToastManager.show('CSV export dimulai...', 'success');
}
