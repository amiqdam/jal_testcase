/* Settings Page — Scenario Adaptation + Knowledge Base Editor */
function renderSettings() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <nav class="admin-nav">
      <span class="logo">JAL Admin</span>
      <a href="#/admin">💬 Chat Monitor</a>
      <a href="#/admin/dashboard">📊 Dashboard</a>
      <a href="#/admin/analytics">📈 Analytics</a>
      <a href="#/admin/database">📋 Database</a>
      <a href="#/admin/settings" class="active">⚙️ Settings</a>
    </nav>
    <div class="settings-page">
      <div class="settings-tabs">
        <button class="settings-tab active" data-tab="scenario">🔄 Scenario Adaptation</button>
        <button class="settings-tab" data-tab="knowledge">📚 Knowledge Base</button>
      </div>
      <div id="settingsContent"></div>
    </div>
  `;

  startNotificationPolling();

  // Tab switching
  document.querySelectorAll('.settings-tab').forEach(tab => {
    tab.onclick = () => {
      document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      if (tab.dataset.tab === 'scenario') renderScenarioTab();
      else renderKnowledgeTab();
    };
  });

  renderScenarioTab();
}

/* ========== Scenario Adaptation Tab ========== */
async function renderScenarioTab() {
  const container = document.getElementById('settingsContent');
  container.innerHTML = '<div class="settings-loading">Loading...</div>';

  try {
    const res = await fetch('/api/admin/scenarios/config');
    const config = await res.json();

    container.innerHTML = `
      <div class="settings-grid">
        <!-- Lead Sources Card -->
        <div class="settings-card">
          <div class="settings-card-header">
            <h3>📡 Kanal / Lead Sources</h3>
            <p>Kelola sumber leads yang tersedia di chatbot onboarding</p>
          </div>
          <div class="settings-card-body">
            <div id="sourcesList" class="settings-list"></div>
            <div class="settings-add-row">
              <input type="text" id="newSourceInput" placeholder="Nama kanal baru (contoh: tiktok)" class="settings-input">
              <button class="settings-btn-add" id="addSourceBtn">+ Tambah</button>
            </div>
          </div>
        </div>

        <!-- Quick Start Options Card -->
        <div class="settings-card">
          <div class="settings-card-header">
            <h3>⚡ Quick Start Options</h3>
            <p>Opsi cepat yang ditampilkan di awal chat</p>
          </div>
          <div class="settings-card-body">
            <div id="quickStartList" class="settings-list"></div>
            <button class="settings-btn-add" id="addQuickStartBtn" style="width:100%;margin-top:8px;">+ Tambah Quick Start</button>
          </div>
        </div>

        <!-- Beasiswa Link Card -->
        <div class="settings-card settings-card-link">
          <div class="settings-card-header">
            <h3>🎓 Kriteria Beasiswa</h3>
            <p>Edit kriteria beasiswa langsung di Knowledge Base</p>
          </div>
          <div class="settings-card-body" style="text-align:center;padding:24px;">
            <button class="settings-btn-primary" onclick="document.querySelector('[data-tab=knowledge]').click(); setTimeout(()=>selectKBSection('scholarships'),300);">
              Edit di Knowledge Base →
            </button>
          </div>
        </div>
      </div>
    `;

    // Render lead sources
    renderSourcesList(config.lead_sources);

    // Render quick start
    renderQuickStartList(config.quick_start_options);

    // Add source handler
    document.getElementById('addSourceBtn').onclick = async () => {
      const input = document.getElementById('newSourceInput');
      const val = input.value.trim().toLowerCase().replace(/\s+/g, '_');
      if (!val) return;
      const current = Array.from(document.querySelectorAll('#sourcesList .settings-list-item')).map(el => el.dataset.id);
      current.push(val);
      await saveLeadSources(current);
      input.value = '';
    };

    // Add quick start handler
    document.getElementById('addQuickStartBtn').onclick = () => {
      showQuickStartModal();
    };

  } catch(e) {
    container.innerHTML = '<div class="settings-error">Failed to load config</div>';
    console.error(e);
  }
}

function renderSourcesList(sources) {
  const list = document.getElementById('sourcesList');
  list.innerHTML = '';
  sources.forEach(src => {
    const item = document.createElement('div');
    item.className = 'settings-list-item';
    item.dataset.id = src;
    item.innerHTML = `
      <span class="settings-list-icon">📌</span>
      <span class="settings-list-label">${src.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
      <button class="settings-list-remove" title="Hapus">✕</button>
    `;
    item.querySelector('.settings-list-remove').onclick = async () => {
      const current = Array.from(document.querySelectorAll('#sourcesList .settings-list-item'))
        .map(el => el.dataset.id).filter(id => id !== src);
      await saveLeadSources(current);
    };
    list.appendChild(item);
  });
}

async function saveLeadSources(sources) {
  try {
    const res = await fetch('/api/admin/scenarios/lead-sources', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sources }),
    });
    const data = await res.json();
    renderSourcesList(data.lead_sources);
    ToastManager.show('Lead sources updated!', 'success');
  } catch(e) {
    ToastManager.show('Failed to update', 'error');
  }
}

function renderQuickStartList(options) {
  const list = document.getElementById('quickStartList');
  list.innerHTML = '';
  options.forEach((opt, idx) => {
    const item = document.createElement('div');
    item.className = 'settings-list-item';
    item.innerHTML = `
      <span class="settings-list-icon">${opt.label.split(' ')[0]}</span>
      <div class="settings-list-details">
        <span class="settings-list-label">${opt.label}</span>
        <span class="settings-list-sub">${opt.macro_intent}/${opt.micro_intent}</span>
      </div>
      <button class="settings-list-remove" title="Hapus">✕</button>
    `;
    item.querySelector('.settings-list-remove').onclick = async () => {
      options.splice(idx, 1);
      await saveQuickStart(options);
    };
    list.appendChild(item);
  });
}

async function saveQuickStart(options) {
  try {
    const res = await fetch('/api/admin/scenarios/quick-start', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ options }),
    });
    const data = await res.json();
    renderQuickStartList(data.quick_start_options);
    ToastManager.show('Quick start options updated!', 'success');
  } catch(e) {
    ToastManager.show('Failed to update', 'error');
  }
}

function showQuickStartModal() {
  const overlay = document.createElement('div');
  overlay.className = 'log-modal-overlay';
  overlay.innerHTML = `
    <div class="log-modal" style="max-width:500px;">
      <div class="modal-header">
        <h2>Tambah Quick Start Option</h2>
        <button class="modal-close" id="closeQSModal">✕</button>
      </div>
      <div class="form-group" style="margin-bottom:12px;">
        <label style="display:block;font-size:12px;color:var(--text-muted);margin-bottom:4px;">Label (contoh: 📚 Info Program Studi)</label>
        <input type="text" id="qsLabel" class="settings-input" style="width:100%;">
      </div>
      <div class="form-group" style="margin-bottom:12px;">
        <label style="display:block;font-size:12px;color:var(--text-muted);margin-bottom:4px;">Pesan yang dikirim</label>
        <input type="text" id="qsMessage" class="settings-input" style="width:100%;">
      </div>
      <div style="display:flex;gap:8px;margin-bottom:12px;">
        <div style="flex:1;">
          <label style="display:block;font-size:12px;color:var(--text-muted);margin-bottom:4px;">Macro Intent</label>
          <select id="qsMacro" class="settings-input" style="width:100%;">
            <option value="INQUIRY">INQUIRY</option>
            <option value="TRANSACTIONAL">TRANSACTIONAL</option>
            <option value="SUPPORT">SUPPORT</option>
          </select>
        </div>
        <div style="flex:1;">
          <label style="display:block;font-size:12px;color:var(--text-muted);margin-bottom:4px;">Micro Intent</label>
          <select id="qsMicro" class="settings-input" style="width:100%;">
            <option value="academic_inquiry">academic_inquiry</option>
            <option value="financial_inquiry">financial_inquiry</option>
            <option value="general_inquiry">general_inquiry</option>
            <option value="registration_process">registration_process</option>
            <option value="status_follow_up">status_follow_up</option>
            <option value="technical_issue">technical_issue</option>
            <option value="general_complaint">general_complaint</option>
          </select>
        </div>
      </div>
      <button class="settings-btn-primary" id="saveQSBtn" style="width:100%;">Simpan</button>
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.querySelector('#closeQSModal').onclick = () => overlay.remove();
  overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };

  overlay.querySelector('#saveQSBtn').onclick = async () => {
    const label = document.getElementById('qsLabel').value.trim();
    const message = document.getElementById('qsMessage').value.trim();
    const macro = document.getElementById('qsMacro').value;
    const micro = document.getElementById('qsMicro').value;
    if (!label || !message) return;

    const id = label.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_');
    const currentItems = Array.from(document.querySelectorAll('#quickStartList .settings-list-item'));
    // Re-fetch
    const res = await fetch('/api/admin/scenarios/config');
    const config = await res.json();
    config.quick_start_options.push({ id, label, macro_intent: macro, micro_intent: micro, message });
    await saveQuickStart(config.quick_start_options);
    overlay.remove();
  };
}

/* ========== Knowledge Base Editor Tab ========== */
let _kbSections = [];
let _kbCurrentSection = '';

async function renderKnowledgeTab() {
  const container = document.getElementById('settingsContent');
  container.innerHTML = '<div class="settings-loading">Loading Knowledge Base...</div>';

  try {
    const sectionsRes = await fetch('/api/admin/knowledge/sections');
    const sectionsData = await sectionsRes.json();
    _kbSections = sectionsData.sections;

    container.innerHTML = `
      <div class="kb-layout">
        <div class="kb-sidebar">
          <div class="kb-sidebar-title">Sections</div>
          <div id="kbSectionNav"></div>
        </div>
        <div class="kb-editor">
          <div class="kb-editor-header" id="kbEditorHeader">
            <h3>Pilih section untuk mulai editing</h3>
          </div>
          <div class="kb-editor-body" id="kbEditorBody">
            <div class="kb-empty-state">← Pilih section dari sidebar</div>
          </div>
        </div>
      </div>
    `;

    const nav = document.getElementById('kbSectionNav');
    _kbSections.forEach(sec => {
      const item = document.createElement('button');
      item.className = 'kb-nav-item';
      item.dataset.section = sec.key;
      item.innerHTML = `
        <span class="kb-nav-icon">${sec.icon}</span>
        <span class="kb-nav-label">${sec.label}</span>
        ${sec.item_count !== null ? `<span class="kb-nav-count">${sec.item_count}</span>` : ''}
      `;
      item.onclick = () => selectKBSection(sec.key);
      nav.appendChild(item);
    });

  } catch(e) {
    container.innerHTML = '<div class="settings-error">Failed to load Knowledge Base</div>';
    console.error(e);
  }
}

async function selectKBSection(sectionKey) {
  _kbCurrentSection = sectionKey;

  // Highlight nav
  document.querySelectorAll('.kb-nav-item').forEach(n => n.classList.remove('active'));
  document.querySelector(`.kb-nav-item[data-section="${sectionKey}"]`)?.classList.add('active');

  const sec = _kbSections.find(s => s.key === sectionKey);
  const header = document.getElementById('kbEditorHeader');
  const body = document.getElementById('kbEditorBody');

  header.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <h3>${sec.icon} ${sec.label}</h3>
      <div style="display:flex;gap:8px;">
        <button class="settings-btn-secondary" id="kbPreviewBtn">👁️ Preview</button>
        <button class="settings-btn-primary" id="kbSaveBtn">💾 Simpan</button>
      </div>
    </div>
  `;

  body.innerHTML = '<div class="settings-loading">Loading...</div>';

  try {
    const res = await fetch(`/api/admin/knowledge/${sectionKey}`);
    const data = await res.json();

    body.innerHTML = `
      <textarea id="kbEditor" class="kb-json-editor" spellcheck="false">${JSON.stringify(data.data, null, 2)}</textarea>
      <div id="kbPreviewPane" class="kb-preview-pane" style="display:none;"></div>
    `;

    document.getElementById('kbSaveBtn').onclick = async () => {
      const editor = document.getElementById('kbEditor');
      try {
        const parsed = JSON.parse(editor.value);
        const saveRes = await fetch(`/api/admin/knowledge/${sectionKey}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ data: parsed }),
        });
        if (saveRes.ok) {
          ToastManager.show(`Section "${sec.label}" berhasil disimpan!`, 'success');
        } else {
          const err = await saveRes.json();
          ToastManager.show(`Error: ${err.detail}`, 'error');
        }
      } catch(e) {
        ToastManager.show('Invalid JSON! Periksa format.', 'error');
      }
    };

    document.getElementById('kbPreviewBtn').onclick = () => {
      const editor = document.getElementById('kbEditor');
      const preview = document.getElementById('kbPreviewPane');
      if (preview.style.display === 'none') {
        try {
          const parsed = JSON.parse(editor.value);
          preview.innerHTML = formatKBPreview(sectionKey, parsed);
          preview.style.display = 'block';
          editor.style.display = 'none';
        } catch(e) {
          ToastManager.show('Invalid JSON — cannot preview', 'error');
        }
      } else {
        preview.style.display = 'none';
        editor.style.display = 'block';
      }
    };

  } catch(e) {
    body.innerHTML = '<div class="settings-error">Failed to load section</div>';
  }
}

function formatKBPreview(section, data) {
  if (section === 'programs' && Array.isArray(data)) {
    return data.map(p => `
      <div class="kb-preview-card">
        <h4>${p.name} (${p.degree})</h4>
        <p>Fakultas: ${p.faculty} | Akreditasi: ${p.accreditation}</p>
        <p>Biaya: Rp ${(p.tuition_per_semester||0).toLocaleString('id-ID')}/semester</p>
        <p>Karir: ${(p.career_prospects||[]).join(', ')}</p>
      </div>
    `).join('');
  }
  if (section === 'scholarships' && Array.isArray(data)) {
    return data.map(s => `
      <div class="kb-preview-card">
        <h4>${s.name}</h4>
        <p>Tipe: ${s.type} | Potongan: ${s.discount_range}</p>
        <p>Kuota: ${s.quota} mahasiswa</p>
        <p>Syarat: ${(s.requirements||[]).slice(0,2).join('; ')}</p>
      </div>
    `).join('');
  }
  if (section === 'faq' && Array.isArray(data)) {
    return data.map(f => `
      <div class="kb-preview-card">
        <h4>Q: ${f.question}</h4>
        <p>A: ${f.answer}</p>
      </div>
    `).join('');
  }
  // Default: formatted JSON
  return `<pre class="kb-preview-json">${JSON.stringify(data, null, 2)}</pre>`;
}
