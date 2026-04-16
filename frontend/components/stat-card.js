/* Stat Card Component */
function createStatCard(label, value, trend) {
  const card = document.createElement('div');
  card.className = 'stat-card';
  card.innerHTML = `
    <div class="stat-label">${label}</div>
    <div class="stat-value">${value}</div>
    ${trend ? `<div class="stat-trend ${trend.direction || ''}">${trend.text || ''}</div>` : ''}
  `;
  return card;
}
