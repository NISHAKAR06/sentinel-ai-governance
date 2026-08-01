/**
 * settings.js — GET/PUT /api/v1/settings
 * Theme cards, sliders, toggles all call the backend on save.
 */
const SettingsPage = (() => {
  let isDirty = false;

  /* ── Load ────────────────────────────────────────────────── */
  async function load() {
    try {
      const data = await SentinelAPI.settings.get();
      _populate(data);
    } catch (e) {
      console.warn('[Settings] Using defaults:', e.message);
      _populate(_defaults());
    }
  }

  /* ── Defaults ────────────────────────────────────────────── */
  const _defaults = () => ({
    theme:'light', language:'en',
    auto_threshold:30, confirm_threshold:60, review_threshold:80,
    notifications_enabled:true, notify_high_risk:true, notify_completion:true, notify_review:true,
    adaptive_learning:true, learning_rate:0.1,
    ws_url:`ws://${location.host}/ws`, ws_reconnect:true, ws_interval:3000,
    audit_retention:90, audit_level:'standard',
  });

  /* ── Populate ────────────────────────────────────────────── */
  function _populate(data) {
    // Theme
    _selectThemeCard(data.theme || 'light');
    // Language
    const lang = document.getElementById('setting-language');
    if (lang) { lang.value = data.language || 'en'; }
    // Sliders
    _setSlider('auto-threshold-slider',    data.auto_threshold    ?? 30);
    _setSlider('confirm-threshold-slider', data.confirm_threshold ?? 60);
    _setSlider('review-threshold-slider',  data.review_threshold  ?? 80);
    // Toggles
    _setToggle('notifications-enabled', data.notifications_enabled !== false);
    _setToggle('notify-high-risk',       data.notify_high_risk !== false);
    _setToggle('notify-completion',      data.notify_completion !== false);
    _setToggle('notify-review',          data.notify_review !== false);
    _setToggle('adaptive-learning',      data.adaptive_learning !== false);
    _setToggle('ws-reconnect',           data.ws_reconnect !== false);
    // Inputs
    _setVal('ws-url',         data.ws_url || '');
    _setVal('ws-interval',    data.ws_interval ?? 3000);
    _setVal('audit-retention',data.audit_retention ?? 90);
    _setVal('learning-rate',  data.learning_rate ?? 0.1);
    // Audit level
    _selectAuditLevel(data.audit_level || 'standard');
  }

  /* ── Helpers ─────────────────────────────────────────────── */
  const _setSlider = (id, val) => {
    const el = document.getElementById(id); if (!el) return;
    el.value = val;
    const disp = document.getElementById(`${id}-value`);
    if (disp) disp.textContent = val;
  };
  const _setToggle = (id, checked) => { const el = document.getElementById(id); if (el) el.checked = checked; };
  const _setVal    = (id, val)     => { const el = document.getElementById(id); if (el) el.value = val; };

  const _selectThemeCard = theme => {
    document.querySelectorAll('.theme-option-card').forEach(c => {
      const active = c.dataset.theme === theme;
      c.classList.toggle('selected', active);
      const chk = c.querySelector('.theme-option-check');
      if (chk) chk.innerHTML = active ? '<i class="fa-solid fa-check" style="font-size:9px"></i>' : '';
    });
  };
  const _selectAuditLevel = level => {
    document.querySelectorAll('.audit-level-btn').forEach(b => b.classList.toggle('active', b.dataset.level === level));
  };

  /* ── Collect ─────────────────────────────────────────────── */
  function _collect() {
    return {
      theme:                  document.querySelector('.theme-option-card.selected')?.dataset.theme || 'light',
      language:               document.getElementById('setting-language')?.value || 'en',
      auto_threshold:         Number(document.getElementById('auto-threshold-slider')?.value    ?? 30),
      confirm_threshold:      Number(document.getElementById('confirm-threshold-slider')?.value ?? 60),
      review_threshold:       Number(document.getElementById('review-threshold-slider')?.value  ?? 80),
      notifications_enabled:  document.getElementById('notifications-enabled')?.checked ?? true,
      notify_high_risk:       document.getElementById('notify-high-risk')?.checked ?? true,
      notify_completion:      document.getElementById('notify-completion')?.checked ?? true,
      notify_review:          document.getElementById('notify-review')?.checked ?? true,
      adaptive_learning:      document.getElementById('adaptive-learning')?.checked ?? true,
      learning_rate:          Number(document.getElementById('learning-rate')?.value ?? 0.1),
      ws_url:                 document.getElementById('ws-url')?.value || '',
      ws_reconnect:           document.getElementById('ws-reconnect')?.checked ?? true,
      ws_interval:            Number(document.getElementById('ws-interval')?.value ?? 3000),
      audit_retention:        Number(document.getElementById('audit-retention')?.value ?? 90),
      audit_level:            document.querySelector('.audit-level-btn.active')?.dataset.level || 'standard',
    };
  }

  /* ── Save ────────────────────────────────────────────────── */
  async function save() {
    const btn = document.getElementById('settings-save-btn') || document.getElementById('settings-save-btn-bar');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner spinner-sm"></span> Saving…'; }
    try {
      const payload = _collect();
      await SentinelAPI.settings.save(payload);
      // Apply immediately
      if (typeof ThemeManager !== 'undefined') ThemeManager.apply(payload.theme);
      if (typeof I18n !== 'undefined') await I18n.load(payload.language);
      isDirty = false;
      _updateSaveBar(false);
      if (typeof Toast !== 'undefined') Toast.success('Settings saved');
    } catch (e) {
      if (typeof Toast !== 'undefined') Toast.danger('Save failed', e.message);
    } finally {
      if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Save Settings'; }
    }
  }

  /* ── Reset ───────────────────────────────────────────────── */
  function reset() {
    if (typeof Modal !== 'undefined') {
      Modal.confirm({ title:'Reset Defaults', message:'Reset all settings to defaults?', type:'warning',
        onConfirm: () => { _populate(_defaults()); _markDirty(); }
      });
    } else if (confirm('Reset all settings?')) {
      _populate(_defaults()); _markDirty();
    }
  }

  /* ── Dirty tracking ──────────────────────────────────────── */
  const _markDirty = () => { isDirty = true; _updateSaveBar(true); };
  const _updateSaveBar = dirty => {
    const hint = document.getElementById('settings-dirty-hint');
    if (hint) hint.classList.toggle('hidden', !dirty);
  };

  /* ── Init ────────────────────────────────────────────────── */
  function init() {
    load();
    // Theme cards
    document.querySelectorAll('.theme-option-card').forEach(c => {
      c.addEventListener('click', () => { _selectThemeCard(c.dataset.theme); if(typeof ThemeManager!=='undefined') ThemeManager.apply(c.dataset.theme); _markDirty(); });
    });
    // Sliders
    document.querySelectorAll('.form-range[id$="-slider"]').forEach(s => {
      s.addEventListener('input', () => {
        const d = document.getElementById(`${s.id}-value`); if (d) d.textContent = s.value;
        _markDirty();
      });
    });
    // Audit level
    document.querySelectorAll('.audit-level-btn').forEach(b => {
      b.addEventListener('click', () => { _selectAuditLevel(b.dataset.level); _markDirty(); });
    });
    // Language
    document.getElementById('setting-language')?.addEventListener('change', async e => {
      if (typeof I18n !== 'undefined') await I18n.load(e.target.value);
      _markDirty();
    });
    // Any input change
    document.querySelectorAll('#settings-form input, #settings-form select').forEach(el => {
      el.addEventListener('change', _markDirty);
    });
    // Save buttons
    document.getElementById('settings-save-btn')?.addEventListener('click', save);
    document.getElementById('settings-save-btn-bar')?.addEventListener('click', save);
    // Reset
    document.querySelectorAll('#settings-reset-btn, #settings-reset-btn-bar').forEach(btn => {
      btn.addEventListener('click', reset);
    });
    // Warn on unload
    window.addEventListener('beforeunload', e => { if (isDirty) { e.preventDefault(); e.returnValue = ''; } });
    // Settings nav
    document.querySelectorAll('.settings-nav-item').forEach(item => {
      item.addEventListener('click', e => {
        e.preventDefault();
        document.querySelectorAll('.settings-nav-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        const sec = document.getElementById(`section-${item.dataset.section}`);
        if (sec) sec.scrollIntoView({ behavior:'smooth', block:'start' });
      });
    });
  }

  document.addEventListener('DOMContentLoaded', init);
  return { init, save, load };
})();
