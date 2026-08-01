/**
 * audit.js — GET /api/v1/audit  export CSV/JSON  WebSocket ws:audit_new
 */
const AuditPage = (() => {
  let allLogs = [], filtered = [], page = 1, pageSize = 20, viewMode = 'timeline';
  let filters = { risk: 'all', status: 'all', search: '', dateFrom: '', dateTo: '' };

  async function load() {
    try {
      const params = { limit: 500 };
      if (filters.risk !== 'all')   params.risk_level = filters.risk;
      if (filters.status !== 'all') params.outcome    = filters.status;
      if (filters.search)           params.query      = filters.search;
      if (filters.dateFrom)         params.date_from  = filters.dateFrom;
      if (filters.dateTo)           params.date_to    = filters.dateTo;
      const data = await SentinelAPI.audit.list(params);
      allLogs  = data.items || data || [];
      filtered = allLogs;
      page = 1;
      _render();
      _updateCount();
    } catch (e) { console.error('[Audit]', e.message); }
  }

  function _applyFilters() {
    let logs = [...allLogs];
    if (filters.risk !== 'all')   logs = logs.filter(l => l.risk_level === filters.risk);
    if (filters.status !== 'all') logs = logs.filter(l => (l.outcome || l.status) === filters.status);
    if (filters.search) {
      const q = filters.search.toLowerCase();
      logs = logs.filter(l =>
        (l.action||'').toLowerCase().includes(q) ||
        (l.resource||'').toLowerCase().includes(q) ||
        (l.actor||'').toLowerCase().includes(q)
      );
    }
    if (filters.dateFrom) logs = logs.filter(l => new Date(l.timestamp) >= new Date(filters.dateFrom));
    if (filters.dateTo)   logs = logs.filter(l => new Date(l.timestamp) <= new Date(filters.dateTo + 'T23:59:59'));
    filtered = logs; page = 1; _render(); _updateCount();
  }

  function _render() {
    const start = (page - 1) * pageSize;
    const slice = filtered.slice(start, start + pageSize);
    if (viewMode === 'timeline') _renderTimeline(slice);
    else _renderTable(slice);
    _renderPagination();
  }

  function _renderTimeline(logs) {
    const c = document.getElementById('audit-timeline-container');
    if (!c) return;
    if (!logs.length) { c.innerHTML = `<div class="empty-state" style="padding:48px 0"><div class="empty-state-icon"><i class="fa-solid fa-clock-rotate-left"></i></div><div class="empty-state-title">No audit logs found</div></div>`; return; }
    const riskColor = l => ({ low:'#16A34A', medium:'#F59E0B', high:'#DC2626', critical:'#7C3AED' }[l] || '#94A3B8');
    c.innerHTML = logs.map(log => `
      <div class="audit-timeline-entry" id="audit-entry-${log.id}">
        <div class="audit-timeline-marker">
          <div class="audit-timeline-dot" style="background:${riskColor(log.risk_level)}"></div>
          <div class="audit-timeline-line"></div>
        </div>
        <div class="audit-entry-content">
          <div class="audit-entry-header">
            <span class="audit-entry-title">${_esc(log.action||'—')}</span>
            <span class="audit-entry-time">${_rel(log.timestamp)}</span>
          </div>
          <div class="audit-entry-meta">
            <span class="audit-entry-meta-item"><i class="fa-solid fa-server"></i> ${_esc(log.resource||'—')}</span>
            <span class="audit-entry-meta-item"><i class="fa-solid fa-user"></i> ${_esc(log.reviewer||log.actor||'System')}</span>
            ${_riskBadge(log.risk_level)}
            ${_outcomeBadge(log.outcome||log.status)}
          </div>
          <div class="mt-2">
            <button class="btn btn-ghost btn-sm" data-toggle-details="${log.id}">
              <i class="fa-solid fa-chevron-down"></i> Show Details
            </button>
          </div>
          <div class="audit-entry-details" id="audit-details-${log.id}">
            ${log.description ? `<p class="text-sm text-secondary">${_esc(log.description)}</p>` : ''}
            <div class="mt-2 flex gap-3 flex-wrap text-xs text-tertiary">
              <span><i class="fa-solid fa-id-badge"></i> ${String(log.id||'').slice(0,8)}</span>
              ${log.department ? `<span><i class="fa-solid fa-building"></i> ${_esc(log.department)}</span>` : ''}
              <span><i class="fa-solid fa-bolt"></i> ${_esc(log.event_type||'')}</span>
            </div>
          </div>
        </div>
      </div>`).join('');
    _bindDetailToggles();
  }

  function _renderTable(logs) {
    const tbody = document.getElementById('audit-table-tbody');
    if (!tbody) return;
    if (!logs.length) { tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding:48px 0;color:var(--text-tertiary)">No audit logs found</td></tr>`; return; }
    tbody.innerHTML = logs.map(log => `
      <tr>
        <td class="text-xs font-mono text-tertiary">${_rel(log.timestamp)}</td>
        <td class="text-sm font-medium">${_esc(log.action||'—')}</td>
        <td class="text-sm">${_esc(log.resource||'—')}</td>
        <td>${_riskBadge(log.risk_level)}</td>
        <td class="text-sm">${_esc(log.reviewer||log.actor||'System')}</td>
        <td>${_outcomeBadge(log.outcome||log.status)}</td>
        <td>
          <button class="btn btn-ghost btn-sm" data-toggle-details="${log.id}">
            <i class="fa-solid fa-eye"></i>
          </button>
        </td>
      </tr>
      <tr class="hidden" id="audit-details-row-${log.id}">
        <td colspan="7">
          <div class="audit-entry-details expanded" style="margin:0;border-top:1px solid var(--border-color)">
            ${log.description ? `<p class="text-sm text-secondary">${_esc(log.description)}</p>` : ''}
            <div class="text-xs text-tertiary mt-2">ID: ${log.id} · Dept: ${log.department||'—'}</div>
          </div>
        </td>
      </tr>`).join('');
    _bindDetailToggles();
  }

  function _bindDetailToggles() {
    document.querySelectorAll('[data-toggle-details]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.toggleDetails;
        const d1 = document.getElementById(`audit-details-${id}`);
        const d2 = document.getElementById(`audit-details-row-${id}`);
        const target = d1 || d2;
        if (!target) return;
        const open = d1 ? target.classList.toggle('expanded') : target.classList.toggle('hidden');
        btn.innerHTML = (d1 ? open : !open)
          ? '<i class="fa-solid fa-chevron-up"></i> Hide Details'
          : '<i class="fa-solid fa-chevron-down"></i> Show Details';
      });
    });
  }

  function _renderPagination() {
    const el = document.getElementById('audit-pagination');
    if (!el) return;
    const total = Math.ceil(filtered.length / pageSize);
    if (total <= 1) { el.innerHTML = ''; return; }
    el.innerHTML = Array.from({ length: total }, (_, i) => i + 1)
      .map(p => `<button class="pagination-btn ${p === page ? 'active' : ''}" data-page="${p}">${p}</button>`)
      .join('');
    el.querySelectorAll('[data-page]').forEach(btn => {
      btn.addEventListener('click', () => { page = parseInt(btn.dataset.page); _render(); });
    });
  }

  function _updateCount() {
    const el = document.getElementById('audit-count');
    if (el) el.textContent = `${filtered.length} entries`;
  }

  async function exportCSV() {
    try {
      const params = {};
      if (filters.risk !== 'all')   params.risk_level = filters.risk;
      if (filters.status !== 'all') params.outcome    = filters.status;
      await SentinelAPI.downloadFile(`/api/v1/audit/export/csv?${new URLSearchParams(params)}`,
        `audit_logs_${new Date().toISOString().slice(0,10)}.csv`);
    } catch (e) { if (typeof Toast !== 'undefined') Toast.danger('Export failed', e.message); }
  }

  async function exportJSON() {
    const blob = new Blob([JSON.stringify(filtered, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = `audit_logs_${new Date().toISOString().slice(0,10)}.json`; a.click();
  }

  function _setViewMode(mode) {
    viewMode = mode;
    document.querySelectorAll('.audit-view-btn').forEach(b => b.classList.toggle('active', b.dataset.view === mode));
    document.getElementById('audit-timeline-container')?.classList.toggle('hidden', mode !== 'timeline');
    document.getElementById('audit-table-wrapper')?.classList.toggle('hidden', mode !== 'table');
    _render();
  }

  /* ── WS live ─────────────────────────────────────────────── */
  function _initWS() {
    SentinelWS.on('audit_new', entry => {
      allLogs.unshift(entry);
      _applyFilters();
    });
  }

  /* ── Helpers ─────────────────────────────────────────────── */
  const _esc = s => { const d = document.createElement('div'); d.textContent = String(s||''); return d.innerHTML; };
  const _rel = ts => { if (!ts) return '—'; const m=Math.floor((Date.now()-new Date(ts).getTime())/60000); return m<1?'just now':m<60?`${m}m ago`:m<1440?`${Math.floor(m/60)}h ago`:`${Math.floor(m/1440)}d ago`; };
  const _riskBadge = l => { const m={low:'success',medium:'warning',high:'danger',critical:'danger'}; return `<span class="badge badge-${m[l]||'neutral'} badge-dot">${l||'—'}</span>`; };
  const _outcomeBadge = o => { const m={approved:'success',rejected:'danger',completed:'success',failed:'danger',pending:'warning'}; return `<span class="badge badge-${m[o]||'neutral'}">${o||'—'}</span>`; };

  function init() {
    _initWS(); load();
    document.getElementById('audit-search')?.addEventListener('input', e => { filters.search = e.target.value; _applyFilters(); });
    document.getElementById('filter-risk')?.addEventListener('change', e => { filters.risk = e.target.value; _applyFilters(); });
    document.getElementById('filter-status')?.addEventListener('change', e => { filters.status = e.target.value; _applyFilters(); });
    document.getElementById('filter-date-from')?.addEventListener('change', e => { filters.dateFrom = e.target.value; _applyFilters(); });
    document.getElementById('filter-date-to')?.addEventListener('change', e => { filters.dateTo = e.target.value; _applyFilters(); });
    document.querySelectorAll('.audit-view-btn').forEach(btn => btn.addEventListener('click', () => _setViewMode(btn.dataset.view)));
    document.getElementById('export-csv-btn')?.addEventListener('click', exportCSV);
    document.getElementById('export-json-btn')?.addEventListener('click', exportJSON);
  }

  document.addEventListener('DOMContentLoaded', init);
  return { init, load };
})();
