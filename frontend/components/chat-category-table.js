/* Chat Category Table Component — Sortable/Filterable */
function createCategoryTable(container, onFilterChange) {
  let currentSort = { by: 'timestamp', order: 'desc' };
  let currentFilters = {};
  let currentPage = 1;

  async function fetchData() {
    const params = new URLSearchParams();
    if (currentFilters.intent) params.set('intent', currentFilters.intent);
    if (currentFilters.funnel_stage) params.set('funnel_stage', currentFilters.funnel_stage);
    if (currentFilters.urgency) params.set('urgency', currentFilters.urgency);
    if (currentFilters.sentiment) params.set('sentiment', currentFilters.sentiment);
    if (currentFilters.search) params.set('search', currentFilters.search);
    params.set('sort_by', currentSort.by);
    params.set('sort_order', currentSort.order);
    params.set('page', currentPage);
    params.set('limit', 20);

    const res = await fetch(`/api/admin/categorization?${params}`);
    return await res.json();
  }

  function renderFilters() {
    const filterBar = document.createElement('div');
    filterBar.className = 'filter-bar';
    filterBar.innerHTML = `
      <select id="filter-intent"><option value="">Semua Intent</option>
        <option value="inquiry_prodi">Inquiry Prodi</option><option value="inquiry_biaya">Inquiry Biaya</option>
        <option value="registration">Registration</option><option value="scholarship">Scholarship</option>
        <option value="followup_status">Follow-up</option><option value="complaint">Complaint</option>
        <option value="ambiguous">Ambiguous</option><option value="partnership">Partnership</option></select>
      <select id="filter-funnel"><option value="">Semua Funnel</option>
        <option value="awareness">Awareness</option><option value="interest">Interest</option>
        <option value="consideration">Consideration</option><option value="decision">Decision</option>
        <option value="enrolled">Enrolled</option></select>
      <select id="filter-urgency"><option value="">Semua Urgency</option>
        <option value="low">Low</option><option value="medium">Medium</option>
        <option value="high">High</option><option value="critical">Critical</option></select>
      <input type="text" id="filter-search" placeholder="🔍 Cari sender/pesan..." />
    `;

    filterBar.querySelectorAll('select, input').forEach(el => {
      el.addEventListener('change', () => {
        currentFilters = {
          intent: filterBar.querySelector('#filter-intent').value,
          funnel_stage: filterBar.querySelector('#filter-funnel').value,
          urgency: filterBar.querySelector('#filter-urgency').value,
          search: filterBar.querySelector('#filter-search').value,
        };
        currentPage = 1;
        refresh();
      });
      if (el.tagName === 'INPUT') {
        let timeout;
        el.addEventListener('input', () => {
          clearTimeout(timeout);
          timeout = setTimeout(() => { el.dispatchEvent(new Event('change')); }, 400);
        });
      }
    });

    return filterBar;
  }

  function renderTable(data) {
    const columns = [
      { key: 'timestamp', label: 'Waktu', sortable: true },
      { key: 'sender', label: 'Sender', sortable: true },
      { key: 'message_preview', label: 'Pesan', sortable: false },
      { key: 'intent', label: 'Intent', sortable: true },
      { key: 'funnel_stage', label: 'Funnel', sortable: true },
      { key: 'urgency', label: 'Urgency', sortable: true },
      { key: 'sentiment', label: 'Sentiment', sortable: true },
      { key: 'confidence', label: 'Confidence', sortable: true },
    ];

    const wrapper = document.createElement('div');
    wrapper.className = 'data-table-wrapper';

    const table = document.createElement('table');
    table.className = 'data-table';

    // Header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    columns.forEach(col => {
      const th = document.createElement('th');
      const isSorted = currentSort.by === col.key;
      th.className = isSorted ? 'sorted' : '';
      th.innerHTML = `${col.label}${col.sortable ? `<span class="sort-icon">${isSorted ? (currentSort.order === 'asc' ? '↑' : '↓') : '⇕'}</span>` : ''}`;
      if (col.sortable) {
        th.onclick = () => {
          if (currentSort.by === col.key) {
            currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
          } else {
            currentSort = { by: col.key, order: 'asc' };
          }
          refresh();
        };
      }
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Body
    const tbody = document.createElement('tbody');
    (data.data || []).forEach(row => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${row.timestamp ? new Date(row.timestamp).toLocaleString('id-ID', {dateStyle:'short',timeStyle:'short'}) : '-'}</td>
        <td>${row.sender || '-'}</td>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${(row.message_preview||'').replace(/"/g,'&quot;')}">${row.message_preview || '-'}</td>
        <td><span class="funnel-badge ${row.intent || ''}">${row.intent || '-'}</span></td>
        <td><span class="funnel-badge ${row.funnel_stage || ''}">${row.funnel_stage || '-'}</span></td>
        <td>${createUrgencyBadge(row.urgency).outerHTML}</td>
        <td>${row.sentiment || '-'}</td>
        <td>${row.confidence != null ? (row.confidence * 100).toFixed(0) + '%' : '-'}</td>
      `;
      tr.style.cursor = 'pointer';
      tr.onclick = () => { if (row.lead_id) window.location.hash = `#/admin/lead/${row.lead_id}`; };
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrapper.appendChild(table);

    // Pagination
    if (data.total_pages > 1) {
      const pag = document.createElement('div');
      pag.className = 'pagination';
      for (let p = 1; p <= Math.min(data.total_pages, 10); p++) {
        const btn = document.createElement('button');
        btn.textContent = p;
        btn.className = p === currentPage ? 'active' : '';
        btn.onclick = () => { currentPage = p; refresh(); };
        pag.appendChild(btn);
      }
      wrapper.appendChild(pag);
    }

    return wrapper;
  }

  async function refresh() {
    const data = await fetchData();
    const tableEl = container.querySelector('.data-table-wrapper');
    const newTable = renderTable(data);
    if (tableEl) tableEl.replaceWith(newTable);
    else container.appendChild(newTable);
    if (onFilterChange) onFilterChange(currentFilters);
  }

  // Initial render
  container.appendChild(renderFilters());
  refresh();
  return { refresh, getFilters: () => currentFilters };
}
