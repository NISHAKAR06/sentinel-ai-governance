/**
 * governance.js — GET /api/v1/governance/assess/{id}  POST /decide
 * Reads action_id from URL param ?action_id=...
 */
const GovernancePage = (() => {
  const STAGES = ['intake','risk','policy','decision','execution','audit'];
  let currentActionId = null;

  /* ── Stepper ─────────────────────────────────────────────── */
  function _setStep(active) {
    const idx = STAGES.indexOf(active);
    STAGES.forEach((s, i) => {
      const el = document.querySelector(`.workflow-step[data-stage="${s}"]`);
      if (!el) return;
      el.classList.remove('completed','active','error');
      const circle = el.querySelector('.step-circle');
      if (i < idx) {
        el.classList.add('completed');
        if (circle) circle.innerHTML = '<i class="fa-solid fa-check"></i>';
      } else if (i === idx) {
        el.classList.add('active');
        if (circle) circle.textContent = String(i + 1);
      } else if (circle) circle.textContent = String(i + 1);
    });
    const txt = document.getElementById('current-stage-text');
    if (txt) txt.textContent = active.charAt(0).toUpperCase() + active.slice(1);
  }

  /* ── Risk gauge ──────────────────────────────────────────── */
  function _drawGauge(score) {
    const valEl = document.getElementById('gauge-score-value');
    if (valEl) valEl.textContent = Math.round(score);
    const fill  = document.querySelector('#risk-gauge-svg .gauge-fill');
    const track = document.querySelector('#risk-gauge-svg .gauge-track');
    if (!fill || !track) return;
    const color = score >= 80 ? '#7C3AED' : score >= 60 ? '#DC2626' : score >= 30 ? '#F59E0B' : '#16A34A';
    const circumference = Math.PI * 64;
    const offset = circumference * (1 - score / 100);
    fill.setAttribute('stroke', color);
    fill.setAttribute('stroke-dasharray', String(circumference));
    fill.setAttribute('stroke-dashoffset', String(offset));

    const badge = document.getElementById('risk-level-badge');
    if (badge) {
      const labels = { low:'Low Risk', medium:'Medium Risk', high:'High Risk', critical:'Critical' };
      const classes = { low:'badge-success', medium:'badge-warning', high:'badge-danger', critical:'badge-danger' };
      const level = score >= 80 ? 'critical' : score >= 60 ? 'high' : score >= 30 ? 'medium' : 'low';
      badge.className = `badge ${classes[level]}`;
      badge.textContent = labels[level];
    }
  }

  /* ── Risk breakdown ──────────────────────────────────────── */
  function _renderBreakdown(factors = []) {
    const list = document.getElementById('risk-breakdown-list');
    if (!list) return;
    if (!factors.length) { list.innerHTML = '<div class="text-xs text-tertiary">No breakdown available</div>'; return; }
    const color = s => s >= 60 ? '#DC2626' : s >= 30 ? '#F59E0B' : '#16A34A';
    list.innerHTML = factors.map(f => `
      <div class="risk-factor-row">
        <div class="risk-factor-header">
          <span class="risk-factor-name">
            <i class="fa-solid ${f.icon||'fa-circle'}" style="color:${color(f.score)};font-size:11px"></i>
            ${_esc(f.factor)}
          </span>
          <span class="risk-factor-score font-mono" style="color:${color(f.score)}">${Math.round(f.score)}</span>
        </div>
        <div class="progress-bar-wrap mt-1">
          <div class="progress-bar-fill" style="width:${f.score}%;background:${color(f.score)}"></div>
        </div>
      </div>`).join('');
  }

  /* ── Metadata ────────────────────────────────────────────── */
  function _renderMeta(data) {
    const set = (id, html) => { const el = document.getElementById(id); if (el) el.innerHTML = html; };
    const rev = data.reversible;
    set('meta-reversibility',
      `<span class="reversibility-badge ${rev ? 'reversible' : 'irreversible'}">
         <i class="fa-solid ${rev ? 'fa-rotate-left' : 'fa-ban'}"></i>
         ${rev ? 'Reversible' : 'Irreversible'}
       </span>`);
    set('meta-data-scope', `<span class="badge badge-info">${_esc(data.data_scope || '—')}</span>`);
    const regs = (data.regulations || []).filter(r => r && r !== 'none');
    set('meta-regulation', regs.length
      ? regs.map(r => `<span class="regulation-tag">${_esc(r)}</span>`).join('')
      : '<span class="text-tertiary text-xs">None</span>');
    const confPct = Math.round((data.confidence || 0) * 100);
    set('meta-confidence', `
      <div class="confidence-bar-wrap">
        <div class="progress-bar-wrap flex-1">
          <div class="progress-bar-fill success" style="width:${confPct}%"></div>
        </div>
        <span class="confidence-value">${confPct}%</span>
      </div>`);
  }

  /* ── Policy rules ────────────────────────────────────────── */
  function _renderPolicies(rules = []) {
    const list = document.getElementById('policy-rules-list');
    if (!list) return;
    const count = document.getElementById('policy-count');
    if (count) count.textContent = rules.length;
    list.innerHTML = rules.map(r => {
      const passed = r.status === 'pass';
      return `
        <div class="policy-rule-item">
          <div class="policy-rule-icon text-${passed ? 'success' : r.status === 'block' ? 'danger' : 'warning'}">
            <i class="fa-solid ${r.icon || (passed ? 'fa-shield-check' : 'fa-shield-exclamation')}"></i>
          </div>
          <div>
            <div class="policy-rule-name">${_esc(r.name)}</div>
            ${r.message ? `<div class="policy-rule-desc">${_esc(r.message)}</div>` : ''}
          </div>
          <div class="policy-rule-status ml-auto">
            <span class="badge badge-${passed ? 'success' : r.status === 'block' ? 'danger' : 'warning'}">${r.status}</span>
          </div>
        </div>`;
    }).join('');
  }

  /* ── Decision card ───────────────────────────────────────── */
  function _renderDecision(decision) {
    document.querySelectorAll('.decision-option').forEach(opt => {
      opt.classList.remove('selected-auto','selected-confirm','selected-review');
      const chk = opt.querySelector('.decision-option-check');
      if (chk) chk.innerHTML = '';
    });
    const map = { auto: 'auto', confirm: 'confirm', review: 'review', require_confirmation: 'confirm', human_review: 'review' };
    const key = map[decision] || 'review';
    const opt = document.querySelector(`.decision-option[data-decision="${key}"]`);
    if (opt) {
      opt.classList.add(`selected-${key}`);
      const chk = opt.querySelector('.decision-option-check');
      if (chk) chk.innerHTML = '<i class="fa-solid fa-check" style="font-size:9px;color:#fff"></i>';
    }
  }

  /* ── Timeline ────────────────────────────────────────────── */
  function _renderTimeline(events = []) {
    const list = document.getElementById('workflow-timeline');
    if (!list) return;
    list.innerHTML = events.map(e => {
      const typeMap = { primary:'primary', success:'success', warning:'warning', danger:'danger', info:'info' };
      const cls = typeMap[e.type] || 'primary';
      return `
        <div class="timeline-item">
          <div class="timeline-dot ${cls}"><i class="fa-solid ${e.icon || 'fa-circle'}"></i></div>
          <div class="timeline-content">
            <div class="timeline-content-title">${_esc(e.label)}</div>
            <div class="timeline-content-meta">${e.timestamp ? _rel(e.timestamp) : ''}</div>
            ${e.detail ? `<div class="timeline-content-body">${_esc(e.detail)}</div>` : ''}
          </div>
        </div>`;
    }).join('');
  }

  /* ── Load assessment ─────────────────────────────────────── */
  async function loadAssessment(actionId) {
    currentActionId = actionId;
    try {
      const data = await SentinelAPI.governance.assess(actionId);
      _setStep(data.current_stage || 'intake');
      _drawGauge(data.risk_score || 0);
      _renderBreakdown(data.risk_factors || []);
      _renderMeta(data);
      _renderPolicies(data.policy_rules || []);
      _renderDecision(data.decision);
      _renderTimeline(data.timeline || []);
    } catch (e) {
      console.error('[Governance]', e.message);
      if (typeof Toast !== 'undefined') Toast.danger('Failed to load governance data', e.message);
    }
  }

  /* ── Decision override ───────────────────────────────────── */
  function _initDecisionOptions() {
    document.querySelectorAll('.decision-option').forEach(opt => {
      opt.addEventListener('click', () => {
        if (!currentActionId) return;
        const decision = opt.dataset.decision;
        const label = { auto:'AUTO APPROVE', confirm:'REQUIRE CONFIRMATION', review:'HUMAN REVIEW' }[decision] || decision;
        if (typeof Modal !== 'undefined') {
          Modal.confirm({
            title: 'Override Decision',
            message: `Set decision to: ${label}?`,
            type: decision === 'auto' ? 'success' : decision === 'confirm' ? 'warning' : 'danger',
            onConfirm: async () => {
              try {
                await SentinelAPI.governance.decide({ action_id: currentActionId, decision });
                _renderDecision(decision);
                if (typeof Toast !== 'undefined') Toast.success('Decision updated');
              } catch (e) { if (typeof Toast !== 'undefined') Toast.danger('Error', e.message); }
            },
          });
        }
      });
    });
  }

  /* ── Helpers ─────────────────────────────────────────────── */
  function _esc(s) { const d = document.createElement('div'); d.textContent = String(s||''); return d.innerHTML; }
  function _rel(ts) {
    if (!ts) return '';
    const d = new Date(ts), diff = Date.now() - d.getTime();
    const m = Math.floor(diff/60000);
    if (m < 1) return 'just now';
    if (m < 60) return `${m}m ago`;
    return d.toLocaleTimeString(undefined, { hour:'2-digit', minute:'2-digit' });
  }

  /* ── Init ────────────────────────────────────────────────── */
  function init() {
    _initDecisionOptions();
    // Read action_id from URL
    const params = new URLSearchParams(location.search);
    const actionId = params.get('action_id');
    if (actionId) loadAssessment(actionId);
    else _setStep('intake');
  }

  document.addEventListener('DOMContentLoaded', init);
  return { init, loadAssessment };
})();
