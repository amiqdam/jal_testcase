/* Quick Start Options Component */
function createQuickStartOptions(options, onSelect) {
  const container = document.createElement('div');
  container.className = 'quick-start-container';

  const label = document.createElement('div');
  label.style.cssText = 'font-size: 13px; color: var(--text-secondary); margin-bottom: 4px;';
  label.textContent = 'Pilih topik untuk memulai:';
  container.appendChild(label);

  options.forEach(opt => {
    const btn = document.createElement('button');
    btn.className = 'quick-start-btn';
    btn.textContent = opt.label;
    btn.onclick = () => onSelect(opt);
    container.appendChild(btn);
  });
  return container;
}
