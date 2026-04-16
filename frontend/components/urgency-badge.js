/* Urgency Badge Component */
function createUrgencyBadge(urgency) {
  const badge = document.createElement('span');
  badge.className = `urgency-badge ${urgency || 'low'}`;
  badge.textContent = (urgency || 'low').toUpperCase();
  return badge;
}

function createFunnelBadge(stage) {
  const badge = document.createElement('span');
  badge.className = `funnel-badge ${stage || 'awareness'}`;
  badge.textContent = (stage || 'awareness').replace('_', ' ');
  return badge;
}
