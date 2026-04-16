/* Admin Dashboard Page — Overview */
async function renderDashboard(app) {
  const content = document.querySelector('.dashboard-content') || app;
  content.innerHTML = '<div style="padding:var(--space-6)"><p style="color:var(--text-muted)">Loading dashboard...</p></div>';

  try {
    const [summaryRes, funnelRes, analyticsRes] = await Promise.all([
      fetch('/api/dashboard/summary'), fetch('/api/dashboard/funnel'), fetch('/api/dashboard/analytics')
    ]);
    const summary = await summaryRes.json();
    const funnel = await funnelRes.json();
    const analytics = await analyticsRes.json();

    content.innerHTML = `
      <div class="dashboard-content">
        <h2 style="margin-bottom:var(--space-6);font-size:var(--font-size-2xl)">📊 Dashboard Overview</h2>
        <div class="stat-cards" id="stat-cards"></div>
        <div id="attention-panel"></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-5);margin-top:var(--space-5)">
          <div class="chart-card"><h3>Funnel Stage</h3><div id="funnel-chart"></div></div>
          <div class="chart-card"><h3>Intent Distribution</h3><canvas id="intent-chart"></canvas></div>
        </div>
      </div>`;

    // Stat cards
    const cardsEl = document.getElementById('stat-cards');
    cardsEl.appendChild(createStatCard('Total Leads', summary.total_leads, { text: `+${summary.new_today} hari ini`, direction: 'up' }));
    cardsEl.appendChild(createStatCard('Hari Ini', summary.new_today));
    cardsEl.appendChild(createStatCard('Perlu Perhatian', summary.attention_needed, summary.attention_needed > 0 ? { text: '⚠️ Perlu tindakan', direction: 'down' } : null));
    const totalInFunnel = Object.values(summary.funnel_distribution || {}).reduce((a,b) => a+b, 0) || 1;
    const decisionPct = ((summary.funnel_distribution?.decision || 0) / totalInFunnel * 100).toFixed(0);
    cardsEl.appendChild(createStatCard('Decision Rate', decisionPct + '%'));

    // Funnel chart
    createFunnelChart(document.getElementById('funnel-chart'), funnel);

    // Intent chart
    const intentDist = analytics.intent_distribution || [];
    new Chart(document.getElementById('intent-chart').getContext('2d'), {
      type: 'bar',
      data: {
        labels: intentDist.map(i => i.intent),
        datasets: [{ data: intentDist.map(i => i.count),
          backgroundColor: ['#7c83ff','#4ecdc4','#ff6b9d','#ffd93d','#60a5fa','#8b5cf6','#6b7280','#10b981'],
          borderRadius: 6 }]
      },
      options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } },
        scales: { x: { ticks: { color: '#a0a0b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                 y: { ticks: { color: '#e8e8f0', font: { size: 11 } }, grid: { display: false } } } }
    });

    // Attention panel
    if ((analytics.attention_items || []).length > 0) {
      const panel = document.getElementById('attention-panel');
      panel.innerHTML = `<div class="attention-panel"><h3>🚨 Perlu Perhatian Segera</h3>
        ${analytics.attention_items.slice(0, 5).map(item => `
          <div class="attention-item">
            <div>
              <strong>${item.name || item.session_id}</strong>
              <div style="font-size:12px;color:var(--text-muted)">${(item.last_message || '').slice(0, 60)}...</div>
            </div>
            <div>${createUrgencyBadge(item.urgency).outerHTML}</div>
          </div>`).join('')}
      </div>`;
    }
  } catch (err) {
    content.innerHTML = `<div class="dashboard-content"><p style="color:var(--urgency-critical)">Error loading dashboard: ${err.message}</p></div>`;
  }
}
