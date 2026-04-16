/* Lead Table Component */
function createLeadTable(data) { return ''; }
/* Funnel Chart Component */
function createFunnelChart(container, data) {
  if (!data || !data.funnel) return;
  const ctx = document.createElement('canvas');
  container.appendChild(ctx);
  new Chart(ctx.getContext('2d'), {
    type: 'bar',
    data: {
      labels: data.funnel.map(s => s.stage),
      datasets: [{ data: data.funnel.map(s => s.count),
        backgroundColor: ['#60a5fa','#3b82f6','#6366f1','#8b5cf6','#10b981'], borderRadius: 8, barThickness: 50 }]
    },
    options: { responsive: true, plugins: { legend: { display: false } },
      scales: { x: { ticks: { color: '#a0a0b8' }, grid: { display: false } },
               y: { ticks: { color: '#a0a0b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true } } }
  });
}
/* Processing Log Component */
function createProcessingLog(logData) {
  const container = document.createElement('div');
  container.className = 'processing-log';
  let steps = [];
  if (typeof logData === 'string') { try { steps = JSON.parse(logData).steps || []; } catch(e) {} }
  else if (logData && logData.steps) { steps = logData.steps; }
  steps.forEach(step => {
    const el = document.createElement('div');
    el.className = 'log-step';
    const conf = step.confidence || 0;
    const confClass = conf >= 0.8 ? 'high' : conf >= 0.6 ? 'medium' : 'low';
    el.innerHTML = `<div class="step-name">${step.order || ''}. ${step.step || ''}</div>
      <div class="step-result">Hasil: ${typeof step.result === 'object' ? JSON.stringify(step.result) : step.result || '-'}</div>
      <div class="step-reasoning">${step.reasoning || ''}</div>
      ${step.confidence != null ? `<div class="confidence-bar"><div class="fill ${confClass}" style="width:${conf*100}%"></div></div>` : ''}`;
    container.appendChild(el);
  });
  return container;
}
