/* Dynamic Charts Component — Reactive Chart.js Visualizations */
let chartInstances = {};

async function renderDynamicCharts(container, filters) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
  }

  const res = await fetch(`/api/admin/categorization/stats?${params}`);
  const stats = await res.json();

  // Destroy existing charts
  Object.values(chartInstances).forEach(c => c.destroy());
  chartInstances = {};

  container.innerHTML = '';
  const grid = document.createElement('div');
  grid.className = 'charts-grid';

  const filterLabel = Object.entries(filters || {}).filter(([,v]) => v).map(([k,v]) => `${k}=${v}`).join(', ');
  const suffix = filterLabel ? ` (${filterLabel})` : '';

  // 1. Intent Distribution — Horizontal Bar
  const intentCard = createChartCard(`Intent Distribution${suffix}`);
  grid.appendChild(intentCard);
  const intentCtx = intentCard.querySelector('canvas').getContext('2d');
  const intentLabels = Object.keys(stats.intent_distribution || {});
  const intentData = Object.values(stats.intent_distribution || {});
  const intentColors = ['#7c83ff','#4ecdc4','#ff6b9d','#ffd93d','#60a5fa','#8b5cf6','#6b7280','#10b981'];
  chartInstances.intent = new Chart(intentCtx, {
    type: 'bar',
    data: {
      labels: intentLabels,
      datasets: [{ data: intentData, backgroundColor: intentColors.slice(0, intentLabels.length), borderRadius: 6, barThickness: 24 }]
    },
    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#a0a0b8' } },
               y: { grid: { display: false }, ticks: { color: '#e8e8f0', font: { size: 11 } } } } }
  });

  // 2. Funnel Distribution — Donut
  const funnelCard = createChartCard(`Funnel Distribution${suffix}`);
  grid.appendChild(funnelCard);
  const funnelCtx = funnelCard.querySelector('canvas').getContext('2d');
  const funnelLabels = Object.keys(stats.funnel_distribution || {});
  const funnelData = Object.values(stats.funnel_distribution || {});
  const funnelColors = ['#60a5fa','#3b82f6','#6366f1','#8b5cf6','#10b981'];
  chartInstances.funnel = new Chart(funnelCtx, {
    type: 'doughnut',
    data: {
      labels: funnelLabels,
      datasets: [{ data: funnelData, backgroundColor: funnelColors.slice(0, funnelLabels.length), borderWidth: 0 }]
    },
    options: { responsive: true, maintainAspectRatio: false, cutout: '60%',
      plugins: { legend: { position: 'bottom', labels: { color: '#a0a0b8', padding: 12, font: { size: 11 } } } } }
  });

  // 3. Urgency Breakdown — Bar
  const urgencyCard = createChartCard(`Urgency Breakdown${suffix}`);
  grid.appendChild(urgencyCard);
  const urgencyCtx = urgencyCard.querySelector('canvas').getContext('2d');
  const urgencyOrder = ['low','medium','high','critical'];
  const urgencyLabels = urgencyOrder.filter(u => (stats.urgency_breakdown || {})[u] !== undefined);
  const urgencyData = urgencyLabels.map(u => stats.urgency_breakdown[u]);
  const urgencyColors = ['#6b7280','#f59e0b','#f97316','#ef4444'];
  chartInstances.urgency = new Chart(urgencyCtx, {
    type: 'bar',
    data: {
      labels: urgencyLabels.map(l => l.toUpperCase()),
      datasets: [{ data: urgencyData, backgroundColor: urgencyColors.slice(0, urgencyLabels.length), borderRadius: 6, barThickness: 40 }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { x: { grid: { display: false }, ticks: { color: '#a0a0b8' } },
               y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#a0a0b8' } } } }
  });

  // 4. Volume Timeline — Line
  const timelineCard = createChartCard(`Chat Volume${suffix}`);
  grid.appendChild(timelineCard);
  const timelineCtx = timelineCard.querySelector('canvas').getContext('2d');
  const timeline = stats.volume_timeline || [];
  chartInstances.timeline = new Chart(timelineCtx, {
    type: 'line',
    data: {
      labels: timeline.map(t => t.date ? new Date(t.date).toLocaleDateString('id-ID', {day:'numeric',month:'short'}) : ''),
      datasets: [{ data: timeline.map(t => t.count), borderColor: '#7c83ff', backgroundColor: 'rgba(124,131,255,0.1)',
        fill: true, tension: 0.4, pointRadius: 3, pointBackgroundColor: '#7c83ff' }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#a0a0b8', font: { size: 10 } } },
               y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#a0a0b8' }, beginAtZero: true } } }
  });

  container.appendChild(grid);
}

function createChartCard(title) {
  const card = document.createElement('div');
  card.className = 'chart-card';
  card.innerHTML = `<h3>${title}</h3><canvas></canvas>`;
  return card;
}
