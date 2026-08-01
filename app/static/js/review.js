/**
 * review.js — GET /api/v1/review  approve/reject/modify
 * WebSocket live updates via ws:review_new / ws:review_update events.
 */
const ReviewPage = (() => {
  let allRows = [], filtered = [], page = 1, pageSize = 15;
  let filters = { status: 'all', search: '', priority: 'all' };
  let selected = new Set();

  /* ── Load from API ───────────────────────────────────────── */
  async function load() {
    try {
      const params = { limit: 200 };
      if (filters.status !== 'all')   params.status = filters.status;
      if (filters.search)             params.query  = filters.search;
      if (filters.priority !== 'all') params.priority = filters.priority;
      const data = await SentinelAPI.review.list(params);
      allRows = data.items || data || [];
      _applyFilters();
      _updateStats();
    } catch (e) {
      console.error('[Review]', e.message);
    }
  }

  /* ── Stats row ───────────────────────────────────────────── */
  function _updateStats() {
    const counts = { pending:0, critical:0, approved:0, rejected:0 };
    allRows.forEach(r => {
      if (r.status === 'pending')  counts.pending++;
      if (r.status === 'approved') counts.approved++;
      if (r.status === 'rejected') counts.rejected++;
      if (r.priority === 'critical') counts.critical++;
    });
    Object.entries(counts).forEach(([k,v]) => {
      const el = document.getElementById(`stat-${k}`);
      if (el) el.textContent = v;
    });
  }

  /* ── Filter & sort ───────────────────────────────────────── */
  function _applyFilters() {
    let rows = [...allRows];
    if (filters.status !== 'all')   rows = rows.filter(r => r.status === filters.status);
    if (filters.priority !== 'all') rows = rows.filter(r => r.priority === filters.priority);
    if (filters.search) {
      const q = filters.search.toLowerCase();
      rows = rows.filter(r =>
        (r.action_type||'').toLowerCase().includes(q) ||
        (r.action_description||'').toLowerCase().includes(q) ||
        (r.target_resource||'').toLowerCase().includes(q) ||
        String(r.id||'').toLowerCase().includes(q)
      );
    }
    filtered = rows;
    page = 1;
    _renderPage();
    _updateTableInfo();
  }

  /* ── Render table ────────────────────────────────────────── */
  function _renderPage() {
    const tbody = document.getElementById('review-tbody');
    if (!tbody) return;
    const start = (page - 1) * pageSize;
    const rows  = filtered.slice(start, start + pageSize);

    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="10">
        <div class="empty-state" style="padding:48px 0">
          <div class="empty-state-icon"><i class="fa-solid fa-inbox"></i></div>
          <div class="empty-state-title">No reviews match your filters</div>
        </div></td></tr>`;
      _renderPagination();
      return;
    }

    tbody.innerHTML = rows.map(r => `
      <tr data-id="${r.id}" class="${selected.has(r.id) ? 'row-selected' : ''}">
        <td><input type="checkbox" class="row-checkbox" data-id="${r.id}" ${selected.has(r.id) ? 'checked' : ''}></td>
        <td>
          <button class="expand-toggle" data-id="${r.id}">
            <i class="fa-solid fa-chevron-right"></i>
          </button>
        </td>
        <td class="font-mono text-xs text-tertiary">${String(r.id||'').slice(0,8)}</td>
        <td>
          <div class="text-sm font-medium">${_esc(r.action_type||'—')}</div>
          <div class="text-xs text-tertiary mt-1">${_esc(r.target_resource||'')}</div>
        </td>
        <td>${_riskBadge(r.risk_level)}</td>
        <td class="text-sm">${_esc(r.department||'—')}</td>
        <td>${_priorityCell(r.priority)}</td>
        <td>${_statusBadge(r.status)}</td>
        <td class="text-xs text-tertiary">${_rel(r.created_at)}</td>
        <td>
          <div class="flex gap-2">
            <button class="btn btn-success btn-sm" data-action="approve" data-id="${r.id}" title="Approve"><i class="fa-solid fa-check"></i></button>
            <button class="btn btn-outline-danger btn-sm" data-action="reject" data-id="${r.id}" title="Reject"><i class="fa-solid fa-xmark"></i></button>
            <button class="btn btn-secondary btn-sm" data-action="modify" data-id="${r.id}" title="Modify"><i class="fa-solid fa-pen"></i></button>
          </div>
        </td>
      </tr>
      <tr class="expanded-row hidden" id="expand-${r.id}">
        <td colspan="10"><div class="expanded-content" id="expand-content-${r.id}"></div></td>
      </tr>`).join('');

    _renderPagination();
    _bindRowEvents();
  }

  /* ── Expanded row ────────────────────────────────────────── */
  function _renderExpanded(row) {
    const el = document.getElementById(`expand-content-${row.id}`);
    if (!el) return;
    const confPct = Math.round((row.confidence || 0) * 100);
    el.innerHTML = `
      <div class="expanded-detail-grid">
        <div class="expanded-detail-item">
          <span class="expanded-detail-label">Intent</span>
          <span class="expanded-detail-value">${_esc(row.intent||'—')}</span>
        </div>
        <div class="expanded-detail-item">
          <span class="expanded-detail-label">Reversibility</span>
          <span class="expanded-detail-value">
            <span class="reversibility-badge ${row.reversibility === 'reversible' ? 'reversible' : 'irreversible'}">
              ${row.reversibility === 'reversible' ? 'Reversible' : 'Irreversible'}
            </span>
          </span>
        </div>
        <div class="expanded-detail-item">
          <span class="expanded-detail-label">Affected Records</span>
          <span class="expanded-detail-value">${row.affected_records ?? 0}</span>
        </div>
        <div class="expanded-detail-item">
          <span class="expanded-detail-label">Risk Score</span>
          <span class="expanded-detail-value font-bold">${row.risk_score ?? 0}</span>
        </div>
        <div class="expanded-detail-item">
          <span class="expanded-detail-label">Confidence</span>
          <span class="expanded-detail-value">${confPct}%</span>
        </div>
        <div class="expanded-detail-item">
          <span class="expanded-detail-label">Requested By</span>
          <span class="expanded-detail-value">${_esc(row.requested_by||'—')}</span>
        </div>
      </div>
      ${row.action_json ? `
        <pre class="expanded-json">${_esc(JSON.stringify(row.action_json, null, 2))}</pre>` : ''}
      <div class="expanded-actions">
        <button class="btn btn-success" data-action="approve" data-id="${row.id}">
          <i class="fa-solid fa-check"></i> Approve
        </button>
        <button class="btn btn-outline-danger" data-action="reject" data-id="${row.id}">
          <i class="fa-solid fa-xmark"></i> Reject
        </button>
        <button class="btn btn-secondary" data-action="modify" data-id="${row.id}">
          <i class="fa-solid fa-pen"></i> Modify
        </button>
      </div>`;
    // Re-bind buttons inside expanded row
    el.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', () => _handleAction(btn.dataset.action, btn.dataset.id));
    });
  }

  /* ── Row events ──────────────────────────────────────────── */
  function _bindRowEvents() {
    document.querySelectorAll('.row-checkbox').forEach(cb => {
      cb.addEventListener('change', e => {
        const id = e.target.dataset.id;
        e.target.checked ? selected.add(id) : selected.delete(id);
        document.querySelector(`tr[data-id="${id}"]`)?.classList.toggle('row-selected', e.target.checked);
        _updateBulkBar();
      });
    });
    document.querySelectorAll('.expand-toggle').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.id;
        const expandRow = document.getElementById(`expand-${id}`);
        if (!expandRow) return;
        const isOpen = !expandRow.classList.contains('hidden');
        expandRow.classList.toggle('hidden', isOpen);
        btn.classList.toggle('expanded', !isOpen);
        if (!isOpen) {
          const rowData = allRows.find(r => r.id === id);
          if (rowData) _renderExpanded(rowData);
        }
      });
    });
    document.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', () => _handleAction(btn.dataset.action, btn.dataset.id));
    });
  }

  /* ── Action handlers ─────────────────────────────────────── */
  function _handleAction(action, id) {
    if (action === 'approve') _approve(id);
    else if (action === 'reject') _reject(id);
    else if (action === 'modify') _modify(id);
  }

  async function _approve(id) {
    try {
      await SentinelAPI.review.approve(id, '');
      allRows = allRows.filter(r => r.id !== id);
      selected.delete(id);
      _applyFilters(); _updateStats(); _updateBulkBar();
      if (typeof Toast !== 'undefined') Toast.success('Action approved');
    } catch (e) { if (typeof Toast !== 'undefined') Toast.danger('Error', e.message); }
  }

  function _reject(id) {
    // Open reject modal if available, else confirm dialog
    const modal = document.getElementById('reject-modal');
    if (modal) {
      const targetEl = document.getElementById('reject-target-id');
      if (targetEl) targetEl.value = id;
      if (typeof Modal !== 'undefined') Modal.open('reject-modal');
    } else {
      const reason = prompt('Reason for rejection:');
      if (reason === null) return;
      SentinelAPI.review.reject(id, reason || 'Rejected')
        .then(() => {
          allRows = allRows.filter(r => r.id !== id);
          _applyFilters(); _updateStats();
          if (typeof Toast !== 'undefined') Toast.danger('Action rejected');
        })
        .catch(e => { if (typeof Toast !== 'undefined') Toast.danger('Error', e.message); });
    }
  }

  function _modify(id) {
    const modal = document.getElementById('modify-modal');
    if (modal) {
      const targetEl = document.getElementById('modify-target-id');
      if (targetEl) targetEl.value = id;
      if (typeof Modal !== 'undefined') Modal.open('modify-modal');
    }
  }

  /* ── Reject modal form ───────────────────────────────────── */
  function _initRejectForm() {
    document.getElementById('reject-form')?.addEventListener('submit', async e => {
      e.preventDefault();
      const id     = document.getElementById('reject-target-id')?.value;
      const reason = document.getElementById('reject-reason')?.value.trim();
      if (!id || !reason) return;
      try {
        await SentinelAPI.review.reject(id, reason);
        if (typeof Modal !== 'undefined') Modal.close('reject-modal');
        allRows = allRows.filter(r => r.id !== id);
        _applyFilters(); _updateStats();
        if (typeof Toast !== 'undefined') Toast.danger('Action rejected');
        document.getElementById('reject-reason').value = '';
      } catch (err) { if (typeof Toast !== 'undefined') Toast.danger('Error', err.message); }
    });
  }

  /* ── Bulk bar ────────────────────────────────────────────── */
  function _updateBulkBar() {
    const bar = document.getElementById('bulk-actions-bar');
    if (!bar) return;
    bar.classList.toggle('hidden', selected.size === 0);
    const c = bar.querySelector('.bulk-selected-count');
    if (c) c.textContent = `${selected.size} items`;
  }

  /* ── Pagination ──────────────────────────────────────────── */
  function _renderPagination() {
    const el = document.getElementById('review-pagination');
    if (!el) return;
    const total = Math.ceil(filtered.length / pageSize);
    if (total <= 1) { el.innerHTML = ''; return; }
    el.innerHTML = Array.from({ length: total }, (_, i) => i + 1)
      .map(p => `<button class="pagination-btn ${p === page ? 'active' : ''}" data-page="${p}">${p}</button>`)
      .join('');
    el.querySelectorAll('[data-page]').forEach(btn => {
      btn.addEventListener('click', () => { page = parseInt(btn.dataset.page); _renderPage(); });
    });
  }

  /* ── Table info ──────────────────────────────────────────── */
  function _updateTableInfo() {
    const el = document.getElementById('table-info');
    if (el) el.textContent = `${filtered.length} items`;
  }

  /* ── Export CSV ──────────────────────────────────────────── */
  async function exportCSV() {
    try {
      const params = {};
      if (filters.status !== 'all') params.status = filters.status;
      await SentinelAPI.downloadFile(`/api/v1/review/export?${new URLSearchParams(params)}`,
        `review_queue_${new Date().toISOString().slice(0,10)}.csv`);
    } catch {
      // fallback: build CSV client-side
      const headers = ['ID','Action','Risk','Department','Priority','Status','Created'];
      const rows    = filtered.map(r => [r.id, r.action_type, r.risk_level, r.department, r.priority, r.status, r.created_at]);
      const csv     = [headers, ...rows].map(r => r.map(v => `"${v||''}"`).join(',')).join('\n');
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
      a.download = 'review_queue.csv';
      a.click();
    }
  }

  /* ── WebSocket live ──────────────────────────────────────── */
  function _initWS() {
    SentinelWS.on('review_new', async () => {
      await load();
      if (typeof Toast !== 'undefined') Toast.info('New review assigned');
    });
    SentinelWS.on('review_update', data => {
      const idx = allRows.findIndex(r => r.id === data.review_id);
      if (idx !== -1) {
        allRows[idx].status = data.status;
        _applyFilters(); _updateStats();
      }
    });
  }

  /* ── Helpers ─────────────────────────────────────────────── */
  const _esc   = s => { const d = document.createElement('div'); d.textContent = String(s||''); return d.innerHTML; };
  const _rel   = ts => { if (!ts) return '—'; const m = Math.floor((Date.now()-new Date(ts).getTime())/60000); return m < 1 ? 'just now' : m < 60 ? `${m}m ago` : `${Math.floor(m/60)}h ago`; };
  const _riskBadge = l => { const m={low:'success',medium:'warning',high:'danger',critical:'danger'}; return `<span class="badge badge-${m[l]||'neutral'} badge-dot">${l||'—'}</span>`; };
  const _statusBadge = s => { const m={pending:'warning',approved:'success',rejected:'danger',modified:'info'}; return `<span class="badge badge-${m[s]||'neutral'}">${s||'—'}</span>`; };
  const _priorityCell = p => {
    const colors = { critical:'#7C3AED', high:'var(--color-danger)', medium:'var(--color-warning)', low:'var(--color-success)' };
    return `<span style="display:flex;align-items:center;gap:6px;font-size:var(--font-size-xs);font-weight:600;color:${colors[p]||'#94A3B8'}">
      <span style="width:3px;height:16px;border-radius:2px;background:${colors[p]||'#94A3B8'}"></span>${p||'—'}
    </span>`;
  };

  /* ── Init ────────────────────────────────────────────────── */
  function init() {
    _initWS();
    _initRejectForm();
    load();

    // Status filter chips
    document.querySelectorAll('[data-filter-status]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-filter-status]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        filters.status = btn.dataset.filterStatus;
        _applyFilters();
      });
    });
    // Search
    document.getElementById('review-search')?.addEventListener('input', e => {
      filters.search = e.target.value;
      _applyFilters();
    });
    // Select all
    document.getElementById('select-all')?.addEventListener('change', e => {
      const checked = e.target.checked;
      document.querySelectorAll('.row-checkbox').forEach(cb => {
        cb.checked = checked;
        checked ? selected.add(cb.dataset.id) : selected.delete(cb.dataset.id);
        document.querySelector(`tr[data-id="${cb.dataset.id}"]`)?.classList.toggle('row-selected', checked);
      });
      _updateBulkBar();
    });
    // Bulk approve
    document.getElementById('bulk-approve-selected')?.addEventListener('click', async () => {
      const ids = [...selected];
      await Promise.all(ids.map(id => SentinelAPI.review.approve(id, 'Bulk approval').catch(() => {})));
      ids.forEach(id => { allRows = allRows.filter(r => r.id !== id); selected.delete(id); });
      _applyFilters(); _updateStats(); _updateBulkBar();
      if (typeof Toast !== 'undefined') Toast.success(`${ids.length} items approved`);
    });
    // Export CSV
    document.getElementById('export-csv-btn')?.addEventListener('click', exportCSV);
  }

  document.addEventListener('DOMContentLoaded', init);
  return { init, load };
})();
