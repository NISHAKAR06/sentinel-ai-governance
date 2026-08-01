/**
 * api.js — Sentinel AI Governance Platform
 * Centralised async Fetch client with:
 *   - Automatic JWT injection
 *   - Retry logic (exponential backoff)
 *   - Loading state management
 *   - Toast error notifications
 *   - All real FastAPI /api/v1/* endpoints
 */

const SentinelAPI = (() => {
  /* ── Config ──────────────────────────────────────────────── */
  const BASE    = '/api/v1';
  const MAX_RETRY = 2;
  const RETRY_DELAY_MS = 500;

  /* ── Token helpers ───────────────────────────────────────── */
  const getToken  = () => localStorage.getItem('sentinel_token') || sessionStorage.getItem('sentinel_token');
  const setToken  = (t, remember = false) => (remember ? localStorage : sessionStorage).setItem('sentinel_token', t);
  const clearToken = () => { localStorage.removeItem('sentinel_token'); sessionStorage.removeItem('sentinel_token'); };

  /* ── Loading state ───────────────────────────────────────── */
  let _pending = 0;
  const _showLoading = () => { _pending++; document.getElementById('loader-overlay')?.classList.add('active'); };
  const _hideLoading = () => { if (--_pending <= 0) { _pending = 0; document.getElementById('loader-overlay')?.classList.remove('active'); } };

  /* ── Core request ────────────────────────────────────────── */
  async function request(method, path, body = null, opts = {}) {
    const { silent = false, retry = MAX_RETRY, timeout = 30000, raw = false } = opts;
    const url = path.startsWith('http') ? path : `${BASE}${path}`;

    if (!silent) _showLoading();

    const headers = { 'Content-Type': 'application/json' };
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);

    let lastErr;
    for (let attempt = 0; attempt <= retry; attempt++) {
      try {
        const res = await fetch(url, {
          method: method.toUpperCase(),
          headers,
          body: body !== null ? JSON.stringify(body) : undefined,
          signal: controller.signal,
          credentials: 'same-origin',
        });

        clearTimeout(timer);

        if (res.status === 401) {
          clearToken();
          if (!path.includes('/auth/')) window.location.href = '/login';
          throw new APIError('Unauthorised', 401);
        }

        if (raw) return res;

        const ct = res.headers.get('content-type') || '';
        const data = ct.includes('application/json') ? await res.json() : await res.text();

        if (!res.ok) {
          const msg = (typeof data === 'object' && data?.detail?.message) ? data.detail.message
                    : (typeof data === 'object' && data?.detail) ? JSON.stringify(data.detail)
                    : (typeof data === 'string' ? data : `HTTP ${res.status}`);
          throw new APIError(msg, res.status, data);
        }

        if (!silent) _hideLoading();
        return data;

      } catch (err) {
        lastErr = err;
        if (err instanceof APIError && err.status < 500) break;
        if (err.name === 'AbortError') { lastErr = new APIError('Request timed out', 408); break; }
        if (attempt < retry) await _sleep(RETRY_DELAY_MS * Math.pow(2, attempt));
      }
    }

    if (!silent) _hideLoading();

    // Surface error via toast unless caller opts out
    if (!silent && typeof Toast !== 'undefined') {
      Toast.danger('Request failed', lastErr?.message || 'Unknown error');
    }
    throw lastErr;
  }

  const get    = (p, o)    => request('GET',    p, null, o);
  const post   = (p, b, o) => request('POST',   p, b, o);
  const put    = (p, b, o) => request('PUT',    p, b, o);
  const patch  = (p, b, o) => request('PATCH',  p, b, o);
  const del    = (p, o)    => request('DELETE', p, null, o);

  /* ── Auth ────────────────────────────────────────────────── */
  const auth = {
    login:   (creds)  => post('/auth/login', creds, { silent: true, retry: 0 }),
    me:      ()       => get('/auth/me'),
    logout:  ()       => { clearToken(); window.location.href = '/logout'; },
  };

  /* ── Dashboard ───────────────────────────────────────────── */
  const dashboard = {
    stats:    () => get('/dashboard/stats',    { silent: true }),
    health:   () => get('/dashboard/health',   { silent: true }),
    activity: (limit = 10) => get(`/dashboard/activity?limit=${limit}`, { silent: true }),
  };

  /* ── Chat / AI Assistant ─────────────────────────────────── */
  const chat = {
    send:    (payload)       => post('/chat/send', payload, { retry: 0, timeout: 60000 }),
    history: (limit = 20)   => get(`/chat/history?limit=${limit}`, { silent: true }),
    clear:   ()              => del('/chat/history', { silent: true }),
  };

  /* ── Governance ──────────────────────────────────────────── */
  const governance = {
    assess:   (actionId)  => get(`/governance/assess/${actionId}`, { silent: true }),
    decide:   (payload)   => post('/governance/decide', payload),
    policies: ()          => get('/governance/policies', { silent: true }),
  };

  /* ── Review ──────────────────────────────────────────────── */
  const review = {
    list:    (params = {}) => get(`/review?${new URLSearchParams(params)}`, { silent: true }),
    get:     (id)          => get(`/review/${id}`, { silent: true }),
    approve: (id, reason)  => post(`/review/${id}/approve`, { reason }),
    reject:  (id, reason)  => post(`/review/${id}/reject`,  { reason }),
    modify:  (id, payload) => put(`/review/${id}`, payload),
  };

  /* ── Execution ───────────────────────────────────────────── */
  const execution = {
    status:   (id) => get(`/execution/${id}`, { silent: true }),
    execute:  (id) => post(`/execution/${id}/execute`, {}),
    rollback: (id) => post(`/execution/${id}/rollback`, {}),
    logs:     (id) => get(`/execution/${id}/logs`, { silent: true }),
  };

  /* ── Audit ───────────────────────────────────────────────── */
  const audit = {
    list:       (params = {}) => get(`/audit?${new URLSearchParams(params)}`, { silent: true }),
    exportCSV:  (params = {}) => get(`/audit/export/csv?${new URLSearchParams(params)}`, { silent: true, raw: true }),
    exportJSON: (params = {}) => get(`/audit/export/json?${new URLSearchParams(params)}`, { silent: true, raw: true }),
  };

  /* ── Analytics ───────────────────────────────────────────── */
  const analytics = {
    summary:    (period) => get(`/analytics/summary?period=${period}`,    { silent: true }),
    daily:      (period) => get(`/analytics/daily?period=${period}`,      { silent: true }),
    risk:       (period) => get(`/analytics/risk?period=${period}`,       { silent: true }),
    operations: (period) => get(`/analytics/operations?period=${period}`, { silent: true }),
    trend:      (period) => get(`/analytics/trend?period=${period}`,      { silent: true }),
    export:     (period) => get(`/analytics/export?period=${period}`,     { silent: true }),
  };

  /* ── Settings ────────────────────────────────────────────── */
  const settings = {
    get:  ()        => get('/settings', { silent: true }),
    save: (payload) => put('/settings', payload),
  };

  /* ── Profile ─────────────────────────────────────────────── */
  const profile = {
    get:    ()        => get('/profile', { silent: true }),
    update: (payload) => put('/profile', payload),
  };

  /* ── Utilities ───────────────────────────────────────────── */
  class APIError extends Error {
    constructor(msg, status, data = null) {
      super(msg); this.name = 'APIError'; this.status = status; this.data = data;
    }
  }
  const _sleep = ms => new Promise(r => setTimeout(r, ms));

  /* ── Download helper ─────────────────────────────────────── */
  async function downloadFile(url, filename) {
    const res = await fetch(url, {
      headers: getToken() ? { 'Authorization': `Bearer ${getToken()}` } : {},
    });
    if (!res.ok) throw new APIError('Download failed', res.status);
    const blob = await res.blob();
    const a    = document.createElement('a');
    a.href     = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  return {
    get, post, put, patch, del,
    getToken, setToken, clearToken,
    auth, dashboard, chat, governance,
    review, execution, audit, analytics,
    settings, profile,
    downloadFile, APIError,
  };
})();
