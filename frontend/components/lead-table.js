/* Lead Table — funnel chart — processing log combined component */
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
  if (typeof logData === 'string') { try { steps = JSON.parse(logData).reasoning_trace || []; } catch(e) {} }
  else if (logData && logData.reasoning_trace) { steps = logData.reasoning_trace; }
  steps.forEach(step => {
    const el = document.createElement('div');
    el.className = 'agent-step';
    el.innerHTML = `
      <div class="agent-name">${step.agent || ''}</div>
      <div class="react-label thought">💭 Thought</div>
      <div class="react-content">${step.thought || '-'}</div>
      <div class="react-label action">⚡ Action</div>
      <div class="react-content">${step.action || '-'}</div>
      ${step.confidence != null ? `<div class="confidence-bar"><div class="fill ${step.confidence >= 0.8 ? 'high' : step.confidence >= 0.6 ? 'medium' : 'low'}" style="width:${step.confidence*100}%"></div></div>` : ''}
    `;
    container.appendChild(el);
  });
  return container;
}
