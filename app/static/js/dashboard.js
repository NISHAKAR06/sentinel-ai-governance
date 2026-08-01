/**
 * dashboard.js — Live dashboard data from GET /api/v1/dashboard/stats
 * WebSocket auto-refresh on ws:dashboard_update event.
 */
const DashboardPage = (() => {
  let riskChart = null, approvalChart = null;
  let refreshTimer = null;

  /* ── Chart defaults ──────────────────────────────────────── */
  function _cd() {
    const dark = document.documentElement.dataset.theme === 'dark';
    return {
      grid:    dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
      text:    dark ? '#94A3B8' : '#64748B',
      bg:      dark ? '#1E293B' : '#FFFFFF',
      border:  dark ? '#334155' : '#E2E8F0',
    };
  }

  /* ── Stat cards ──────────────────────────────────────────── */
  function _renderStats(data) {
    const setCard = (id, value, trendVal, trendDir) => {
      const el = document.getElementById(id);
      if (!el) return;
      const v = el.querySelector('.stat-card-value');
      const t = el.querySelector('.stat-card-trend');
      if (v) v.textContent = value ?? '—';
      if (t && trendVal != null) {
        const up = trendDir !== 'down';
        t.className = `stat-card-trend ${up ? 'trend-up' : 'trend-down'}`;
        t.innerHTML = `<i class="fa-solid fa-arrow-${up ? 'up' : 'down'}"></i> ${Math.abs(trendVal)}% <span data-i18n="dashboard.vs_yesterday">vs yesterday</span>`;
        if (typeof I18n !== 'undefined') I18n.init && I18n._applyAll && I18n._applyAll();
      }
    };
    setCard('stat-total-requests',   data.total_requests ?? 0,      data.requests_trend, data.requests_trend >= 0 ? 'up' : 'down');
    setCard('stat-autonomous',       data.autonomous_actions ?? 0,  data.autonomous_trend, 'up');
    setCard('stat-confirmations',    data.pending_confirmations ?? 0, null);
    setCard('stat-reviews',          data.pending_reviews ?? 0,     null);
    setCard('stat-avg-risk',         `${data.avg_risk ?? 0}%`,      data.risk_trend, data.risk_trend <= 0 ? 'up' : 'down');
    setCard('stat-health',           data.system_health_label ?? 'Healthy', null);
  }

  /* ── Mini bar chart ──────────────────────────────────────── */
  function _renderMiniBar(hourly = []) {
    const c = document.getElementById('today-activity-bars');
    if (!c) return;
    const max = Math.max(...hourly, 1);
    c.innerHTML = hourly.map((v, i) =>
      `<div class="mini-bar" style="height:${Math.max(6, Math.round(v / max * 100))}%" title="Hour ${i}: ${v} requests"></div>`
    ).join('');
  }

  /* ── Risk Distribution chart ─────────────────────────────── */
  function _renderRiskChart(dist) {
    const ctx = document.getElementById('risk-distribution-chart');
    if (!ctx) return;
    riskChart?.destroy();
    const d = _cd();
    riskChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Low', 'Medium', 'High', 'Critical'],
        datasets: [{
          data: [dist.low ?? 0, dist.medium ?? 0, dist.high ?? 0, dist.critical ?? 0],
          backgroundColor: ['#16A34A','#F59E0B','#DC2626','#7C3AED'],
          borderColor: d.bg, borderWidth: 3, hoverOffset: 6,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '72%',
        plugins: {
          legend: { display: false },
          tooltip: { backgroundColor: d.bg, borderColor: d.border, borderWidth: 1, titleColor: d.text, bodyColor: d.text },
        },
      },
    });
  }

  /* ── Approval Trends chart ───────────────────────────────── */
  function _renderApprovalChart(trends) {
    const ctx = document.getElementById('approval-trends-chart');
    if (!ctx) return;
    approvalChart?.destroy();
    const d = _cd();
    approvalChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: trends.labels ?? [],
        datasets: [
          { label: 'Auto Approved', data: trends.auto ?? [],     backgroundColor: 'rgba(37,99,235,0.80)',  borderRadius: 4, borderSkipped: false },
          { label: 'Reviewed',      data: trends.reviewed ?? [], backgroundColor: 'rgba(245,158,11,0.80)', borderRadius: 4, borderSkipped: false },
          { label: 'Rejected',      data: trends.rejected ?? [], backgroundColor: 'rgba(220,38,38,0.70)',  borderRadius: 4, borderSkipped: false },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { color: d.text, boxWidth: 12, padding: 16, font: { size: 12 } } },
          tooltip: { backgroundColor: d.bg, borderColor: d.border, borderWidth: 1, titleColor: d.text, bodyColor: d.text },
        },
        scales: {
          x: { stacked: true, grid: { color: d.grid }, ticks: { color: d.text, font: { size: 11 } } },
          y: { stacked: true, grid: { color: d.grid }, ticks: { color: d.text, font: { size: 11 } }, beginAtZero: true },
        },
      },
    });
  }

  /* ── Recent Actions table ────────────────────────────────── */
  function _renderActions(actions = []) {
    const tbody = document.getElementById('recent-actions-tbody');
    if (!tbody) return;
    if (!actions.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center text-tertiary" style="padding:32px 0">No recent actions</td></tr>`;
      return;
    }
    const riskBadge = l => {
      const m = { low:'success', medium:'warning', high:'danger', critical:'danger' };
      return `<span class="badge badge-${m[l]||'neutral'} badge-dot">${l||'—'}</span>`;
    };
    const statusBadge = s => {
      const m = { approved:'success', rejected:'danger', pending:'warning', completed:'success', failed:'danger' };
      return `<span class="badge badge-${m[s]||'neutral'}">${s||'—'}</span>`;
    };
    tbody.innerHTML = actions.map(a => `
      <tr>
        <td class="font-mono text-xs text-tertiary">${String(a.id||'').slice(0,8)}</td>
        <td class="text-sm font-medium">${_esc(a.action||a.intent||'—')}</td>
        <td>${riskBadge(a.risk_level)}</td>
        <td>${statusBadge(a.status)}</td>
        <td class="text-xs text-tertiary">${_rel(a.created_at)}</td>
      </tr>`).join('');
  }

  /* ── Audit timeline ──────────────────────────────────────── */
  function _renderAuditTimeline(entries = []) {
    const list = document.getElementById('audit-mini-list');
    if (!list) return;
    if (!entries.length) {
      list.innerHTML = `<div class="text-sm text-tertiary text-center" style="padding:24px 0">No recent audit entries</div>`;
      return;
    }
    const riskColor = l => ({ low:'#16A34A', medium:'#F59E0B', high:'#DC2626', critical:'#7C3AED' }[l] || '#94A3B8');
    list.innerHTML = entries.map(e => `
      <div class="audit-mini-item">
        <div class="audit-mini-dot" style="background:${riskColor(e.risk_level)}15;border:1.5px solid ${riskColor(e.risk_level)}">
          <i class="fa-solid fa-bolt" style="color:${riskColor(e.risk_level)};font-size:10px"></i>
        </div>
        <div class="audit-mini-content">
          <div class="audit-mini-title">${_esc(e.action||'—')}</div>
          <div class="audit-mini-sub">${_esc(e.resource||'')} · ${_esc(e.reviewer||e.actor||'System')}</div>
        </div>
        <div class="audit-mini-time">${_rel(e.timestamp)}</div>
      </div>`).join('');
  }

  /* ── System health ───────────────────────────────────────── */
  function _renderHealth(data) {
    const list = document.getElementById('health-indicators');
    if (!list) return;
    const services = data?.services || [];
    if (!services.length) return;
    list.innerHTML = services.map(s => `
      <div class="health-row">
        <div class="health-row-left">
          <div class="health-dot ${s.status}"></div>
          <div>
            <div class="health-service-name">${_esc(s.name)}</div>
            <div class="health-service-desc">${_esc(s.description||'')}</div>
          </div>
        </div>
        <div class="health-latency">${s.latency != null ? s.latency + 'ms' : '—'}</div>
      </div>`).join('');

    const badge = document.getElementById('health-overall-badge');
    if (badge) badge.textContent = data?.overall || 'Healthy';
  }

  /* ── Load all dashboard data ─────────────────────────────── */
  async function loadAll() {
    try {
      const [stats, health] = await Promise.all([
        SentinelAPI.dashboard.stats(),
        SentinelAPI.dashboard.health(),
      ]);
      _renderStats(stats);
      _renderMiniBar(stats.hourly_activity || Array(24).fill(0));
      _renderRiskChart(stats.risk_distribution || {});
      _renderApprovalChart(stats.approval_trends || {});
      _renderActions(stats.recent_actions || []);
      _renderAuditTimeline(stats.audit_timeline || []);
      _renderHealth(health);
      _updateLastUpdated();
    } catch (e) {
      console.error('[Dashboard]', e.message);
    }
  }

  function _updateLastUpdated() {
    const el = document.getElementById('last-updated');
    if (el) el.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
  }

  /* ── WebSocket live updates ──────────────────────────────── */
  function _initWS() {
    SentinelWS.on('dashboard_update', data => {
      if (data?.stats)       _renderStats(data.stats);
      if (data?.risk)        _renderRiskChart(data.risk);
      if (data?.approval)    _renderApprovalChart(data.approval);
      if (data?.hourly)      _renderMiniBar(data.hourly);
      if (data?.audit)       _renderAuditTimeline(data.audit);
      _updateLastUpdated();
    });

    SentinelWS.on('review_new', () => {
      const badge = document.querySelector('.nav-item[href="/review"] .nav-item-badge');
      if (badge) badge.textContent = parseInt(badge.textContent || '0') + 1;
    });
  }

  /* ── Theme rerender ──────────────────────────────────────── */
  document.addEventListener('themechange', () => {
    riskChart?.destroy();    riskChart = null;
    approvalChart?.destroy(); approvalChart = null;
    loadAll();
  });

  /* ── Helpers ─────────────────────────────────────────────── */
  function _esc(s) { const d = document.createElement('div'); d.textContent = String(s||''); return d.innerHTML; }
  function _rel(ts) {
    if (!ts) return '—';
    const diff = Date.now() - new Date(ts).getTime();
    const m = Math.floor(diff/60000);
    if (m < 1) return 'just now';
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m/60);
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h/24)}d ago`;
  }

  /* ── Init ────────────────────────────────────────────────── */
  function init() {
    _initWS();
    loadAll();
    document.getElementById('dashboard-refresh')?.addEventListener('click', loadAll);
    // Auto-refresh every 60s
    refreshTimer = setInterval(loadAll, 60000);
    // Set today's date
    const dateEl = document.getElementById('activity-date');
    if (dateEl) dateEl.textContent = new Date().toLocaleDateString(undefined, { weekday:'long', month:'long', day:'numeric' });
  }

  document.addEventListener('DOMContentLoaded', init);
  return { init, loadAll };
})();
