/* Quick Start Options Component */
function createQuickStartOptions(onSelect) {
  const container = document.createElement('div');
  container.className = 'quick-start-container';
  container.id = 'quick-start-options';
  
  const options = [
    { id: 'info_prodi', label: '📚 Info Program Studi', intent: 'inquiry_prodi', message: 'Saya ingin tahu tentang program studi yang tersedia' },
    { id: 'biaya_beasiswa', label: '💰 Biaya & Beasiswa', intent: 'inquiry_biaya', message: 'Saya ingin bertanya tentang biaya kuliah dan beasiswa' },
    { id: 'cara_daftar', label: '📝 Cara Mendaftar', intent: 'registration', message: 'Saya ingin tahu cara mendaftar' },
  ];
  
  options.forEach(opt => {
    const btn = document.createElement('button');
    btn.className = 'quick-start-btn';
    btn.textContent = opt.label;
    btn.onclick = () => {
      container.remove();
      if (onSelect) onSelect(opt);
    };
    container.appendChild(btn);
  });
  
  return container;
}
