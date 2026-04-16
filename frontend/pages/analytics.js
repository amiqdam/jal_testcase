/* Analytics Page */
async function renderAnalytics(app) {
  const content = document.querySelector('.dashboard-content') || app;
  content.innerHTML = '<div style="padding:var(--space-6);color:var(--text-muted)">Loading analytics...</div>';

  try {
    const [funnelRes, analyticsRes] = await Promise.all([
      fetch('/api/dashboard/funnel'), fetch('/api/dashboard/analytics')
    ]);
    const funnel = await funnelRes.json();
    const analytics = await analyticsRes.json();

    content.innerHTML = `
      <div class="dashboard-content">
        <h2 style="margin-bottom:var(--space-6);font-size:var(--font-size-2xl)">📈 Analytics</h2>
        <div class="charts-grid">
          <div class="chart-card"><h3>Leads per Funnel Stage</h3><canvas id="a-funnel"></canvas></div>
          <div class="chart-card"><h3>Urgency Distribution</h3><canvas id="a-urgency"></canvas></div>
          <div class="chart-card"><h3>Intent Distribution</h3><canvas id="a-intent"></canvas></div>
          <div class="chart-card"><h3>Daily Trend (Leads Baru)</h3><canvas id="a-trend"></canvas></div>
        </div>
      </div>`;

    // Funnel bar
    const fData = funnel.funnel || [];
    new Chart(document.getElementById('a-funnel').getContext('2d'), {
      type: 'bar', data: { labels: fData.map(f => f.stage), datasets: [{ data: fData.map(f => f.count),
        backgroundColor: ['#60a5fa','#3b82f6','#6366f1','#8b5cf6','#10b981'], borderRadius: 8 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
        scales: { x: { ticks: { color: '#a0a0b8' } }, y: { ticks: { color: '#a0a0b8' }, beginAtZero: true } } }
    });

    // Urgency pie
    const uLabels = ['low','medium','high','critical'];
    const uColors = ['#6b7280','#f59e0b','#f97316','#ef4444'];
    // re-use summary data
    const summRes = await fetch('/api/dashboard/summary');
    const summary = await summRes.json();
    const uData = uLabels.map(l => summary.urgency_distribution?.[l] || 0);
    new Chart(document.getElementById('a-urgency').getContext('2d'), {
      type: 'doughnut', data: { labels: uLabels, datasets: [{ data: uData, backgroundColor: uColors, borderWidth: 0 }] },
      options: { responsive: true, cutout: '55%', plugins: { legend: { position: 'bottom', labels: { color: '#a0a0b8', padding: 12 } } } }
    });

    // Intent
    const iData = analytics.intent_distribution || [];
    new Chart(document.getElementById('a-intent').getContext('2d'), {
      type: 'bar', data: { labels: iData.map(i => i.intent), datasets: [{ data: iData.map(i => i.count),
        backgroundColor: ['#7c83ff','#4ecdc4','#ff6b9d','#ffd93d','#60a5fa','#8b5cf6','#6b7280','#10b981'], borderRadius: 6 }] },
      options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } },
        scales: { x: { ticks: { color: '#a0a0b8' } }, y: { ticks: { color: '#e8e8f0', font: { size: 11 } } } } }
    });

    // Trend
    const tData = (analytics.daily_trend || []).reverse();
    new Chart(document.getElementById('a-trend').getContext('2d'), {
      type: 'line', data: { labels: tData.map(t => t.date), datasets: [{ data: tData.map(t => t.count),
        borderColor: '#7c83ff', backgroundColor: 'rgba(124,131,255,0.1)', fill: true, tension: 0.4, pointRadius: 4, pointBackgroundColor: '#7c83ff' }] },
      options: { responsive: true, plugins: { legend: { display: false } },
        scales: { x: { ticks: { color: '#a0a0b8', font: { size: 10 } } }, y: { ticks: { color: '#a0a0b8' }, beginAtZero: true } } }
    });
  } catch (err) {
    content.innerHTML = `<div style="padding:var(--space-6);color:var(--urgency-critical)">Error: ${err.message}</div>`;
  }
}
