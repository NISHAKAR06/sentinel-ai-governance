/**
 * app.js — Sentinel AI Governance Platform
 * Core application bootstrap: Theme · i18n · Sidebar · Navbar ·
 * Toast · Modal · Dropdown · Notification Panel · Keyboard nav
 */

/* ═══════════════════════════════════════════════════════════
   1. THEME MANAGER
═══════════════════════════════════════════════════════════ */
const ThemeManager = (() => {
  const KEY = 'sentinel_theme';
  const DARK = 'dark';
  const LIGHT = 'light';

  function get() { return localStorage.getItem(KEY) ?? LIGHT; }

  function apply(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(KEY, theme);
    _updateToggle(theme);
    document.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  }

  function toggle() { apply(get() === DARK ? LIGHT : DARK); }

  function init() {
    apply(get());
    document.querySelectorAll('[data-action="theme-toggle"]').forEach(btn => {
      btn.addEventListener('click', toggle);
    });
  }

  function _updateToggle(theme) {
    document.querySelectorAll('[data-action="theme-toggle"]').forEach(btn => {
      const icon  = btn.querySelector('i, .theme-icon');
      const label = btn.querySelector('.theme-label');
      if (icon) {
        icon.className = theme === DARK ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
      }
      if (label) {
        label.textContent = theme === DARK
          ? I18n.t('theme.light')
          : I18n.t('theme.dark');
      }
      btn.setAttribute('aria-label',
        theme === DARK ? I18n.t('theme.light') : I18n.t('theme.dark'));
    });
  }

  return { get, apply, toggle, init };
})();


/* ═══════════════════════════════════════════════════════════
   2. I18N MANAGER
═══════════════════════════════════════════════════════════ */
const I18n = (() => {
  const KEY = 'sentinel_lang';
  let translations = {};
  let currentLang  = 'en';

  async function load(lang) {
    try {
      const res  = await fetch(`/static/i18n/${lang}.json`);
      if (!res.ok) throw new Error(`i18n fetch failed: ${res.status}`);
      const data = await res.json();
      translations = data;
      currentLang  = lang;
      localStorage.setItem(KEY, lang);
      _applyAll();
      document.documentElement.lang = lang;
      document.dispatchEvent(new CustomEvent('langchange', { detail: { lang } }));
    } catch (e) {
      console.error('[i18n] Failed to load language:', lang, e);
    }
  }

  /* Dot-notation key lookup: t('nav.dashboard') */
  function t(key, fallback = '') {
    const parts = key.split('.');
    let cur = translations;
    for (const p of parts) {
      if (cur == null || typeof cur !== 'object') return fallback || key;
      cur = cur[p];
    }
    return cur ?? fallback ?? key;
  }

  /* Apply all [data-i18n] elements */
  function _applyAll() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      const val = t(key);
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        if (el.placeholder !== undefined) el.placeholder = val;
      } else {
        el.textContent = val;
      }
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      el.placeholder = t(el.dataset.i18nPlaceholder);
    });
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      el.title = t(el.dataset.i18nTitle);
    });
    document.querySelectorAll('[data-i18n-aria]').forEach(el => {
      el.setAttribute('aria-label', t(el.dataset.i18nAria));
    });
  }

  function getLang() { return currentLang; }

  async function init() {
    const saved = localStorage.getItem(KEY) ?? 'en';
    await load(saved);

    /* Wire language selector */
    document.querySelectorAll('[data-action="lang-change"]').forEach(sel => {
      sel.value = currentLang;
      sel.addEventListener('change', e => load(e.target.value));
    });
  }

  return { load, t, getLang, init };
})();


/* ═══════════════════════════════════════════════════════════
   3. SIDEBAR MANAGER
═══════════════════════════════════════════════════════════ */
const SidebarManager = (() => {
  const KEY     = 'sentinel_sidebar';
  let sidebar   = null;
  let overlay   = null;
  let collapsed = false;

  function init() {
    sidebar = document.getElementById('app-sidebar');
    overlay = document.getElementById('sidebar-overlay');
    if (!sidebar) return;

    /* Restore state */
    collapsed = localStorage.getItem(KEY) === 'collapsed';
    if (collapsed) sidebar.classList.add('collapsed');

    /* Toggle button */
    document.querySelectorAll('[data-action="sidebar-toggle"]').forEach(btn => {
      btn.addEventListener('click', toggle);
    });

    /* Mobile overlay */
    if (overlay) overlay.addEventListener('click', closeMobile);

    /* Mobile hamburger */
    document.querySelectorAll('[data-action="sidebar-open"]').forEach(btn => {
      btn.addEventListener('click', openMobile);
    });

    /* Active nav item */
    _setActiveNavItem();
  }

  function toggle() {
    if (window.innerWidth <= 700) {
      sidebar.classList.toggle('mobile-open');
      overlay?.classList.toggle('active');
      return;
    }
    collapsed = !collapsed;
    sidebar.classList.toggle('collapsed', collapsed);
    localStorage.setItem(KEY, collapsed ? 'collapsed' : 'expanded');
    _updateCollapseBtn();
  }

  function openMobile() {
    sidebar.classList.add('mobile-open');
    overlay?.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeMobile() {
    sidebar.classList.remove('mobile-open');
    overlay?.classList.remove('active');
    document.body.style.overflow = '';
  }

  function _updateCollapseBtn() {
    const btn = sidebar.querySelector('[data-action="sidebar-toggle"]');
    if (!btn) return;
    const icon = btn.querySelector('i');
    if (icon) icon.className = collapsed
      ? 'fa-solid fa-chevron-right'
      : 'fa-solid fa-chevron-left';
    btn.setAttribute('aria-label', collapsed
      ? I18n.t('nav.expand_sidebar')
      : I18n.t('nav.collapse_sidebar'));
  }

  function _setActiveNavItem() {
    const path = window.location.pathname;
    sidebar?.querySelectorAll('.nav-item[href]').forEach(link => {
      link.classList.toggle('active', path.startsWith(link.getAttribute('href')));
    });
  }

  return { init, toggle, openMobile, closeMobile };
})();


/* ═══════════════════════════════════════════════════════════
   4. TOAST MANAGER
═══════════════════════════════════════════════════════════ */
const Toast = (() => {
  let container = null;

  function _getContainer() {
    if (!container) {
      container = document.getElementById('toast-container');
      if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-atomic', 'false');
        document.body.appendChild(container);
      }
    }
    return container;
  }

  function show(type = 'info', title = '', message = '', duration = 4000) {
    const c = _getContainer();
    const icons = { success: 'fa-check', danger: 'fa-xmark', warning: 'fa-triangle-exclamation', info: 'fa-circle-info' };
    const icon  = icons[type] ?? icons.info;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
      <div class="toast-icon" aria-hidden="true"><i class="fa-solid ${icon}"></i></div>
      <div class="toast-content">
        <div class="toast-title">${_esc(title)}</div>
        ${message ? `<div class="toast-message">${_esc(message)}</div>` : ''}
      </div>
      <button class="toast-dismiss" aria-label="${I18n.t('common.close')}">
        <i class="fa-solid fa-xmark"></i>
      </button>`;

    toast.querySelector('.toast-dismiss').addEventListener('click', () => remove(toast));
    c.appendChild(toast);

    if (duration > 0) setTimeout(() => remove(toast), duration);
    return toast;
  }

  function remove(toast) {
    if (!toast || !toast.parentNode) return;
    toast.classList.add('removing');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
  }

  function success(title, msg, dur) { return show('success', title, msg, dur); }
  function danger(title, msg, dur)   { return show('danger',  title, msg, dur); }
  function warning(title, msg, dur)  { return show('warning', title, msg, dur); }
  function info(title, msg, dur)     { return show('info',    title, msg, dur); }

  function _esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  return { show, remove, success, danger, warning, info };
})();


/* ═══════════════════════════════════════════════════════════
   5. MODAL MANAGER
═══════════════════════════════════════════════════════════ */
const Modal = (() => {
  let activeModal = null;
  let focusTrap   = null;

  function open(idOrEl) {
    const backdrop = typeof idOrEl === 'string'
      ? document.getElementById(idOrEl)
      : idOrEl;
    if (!backdrop) return;

    activeModal = backdrop;
    backdrop.classList.add('open');
    document.body.style.overflow = 'hidden';

    /* Focus first focusable element */
    requestAnimationFrame(() => {
      const focusable = backdrop.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      focusable?.focus();
    });

    /* Trap focus */
    focusTrap = e => _trapFocus(e, backdrop);
    document.addEventListener('keydown', focusTrap);
  }

  function close(idOrEl) {
    const backdrop = idOrEl
      ? (typeof idOrEl === 'string' ? document.getElementById(idOrEl) : idOrEl)
      : activeModal;
    if (!backdrop) return;

    backdrop.classList.remove('open');
    document.body.style.overflow = '';
    if (focusTrap) document.removeEventListener('keydown', focusTrap);
    activeModal = null;
  }

  function confirm({ title = '', message = '', confirmText = '', cancelText = '', onConfirm, onCancel, type = 'danger' } = {}) {
    const t = I18n.t.bind(I18n);
    const id = `confirm-modal-${Date.now()}`;
    const el = document.createElement('div');
    el.id = id;
    el.className = 'modal-backdrop';
    el.innerHTML = `
      <div class="modal modal-sm" role="dialog" aria-modal="true" aria-labelledby="${id}-title">
        <div class="modal-header">
          <span class="modal-title" id="${id}-title">${_esc(title || t('common.confirm'))}</span>
          <button class="modal-close" aria-label="${t('common.close')}"><i class="fa-solid fa-xmark"></i></button>
        </div>
        <div class="modal-body">
          <p class="text-sm text-secondary">${_esc(message)}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary btn-cancel">${_esc(cancelText || t('common.cancel'))}</button>
          <button class="btn btn-${type} btn-confirm">${_esc(confirmText || t('common.confirm'))}</button>
        </div>
      </div>`;
    document.body.appendChild(el);

    el.querySelector('.modal-close').onclick  = () => { close(el); el.remove(); onCancel?.(); };
    el.querySelector('.btn-cancel').onclick   = () => { close(el); el.remove(); onCancel?.(); };
    el.querySelector('.btn-confirm').onclick  = () => { close(el); el.remove(); onConfirm?.(); };
    el.addEventListener('click', e => { if (e.target === el) { close(el); el.remove(); onCancel?.(); } });

    open(el);
  }

  function _trapFocus(e, container) {
    if (e.key !== 'Tab') return;
    const focusable = [...container.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')].filter(el => !el.disabled);
    if (!focusable.length) return;
    const first = focusable[0], last = focusable[focusable.length - 1];
    if (e.shiftKey ? document.activeElement === first : document.activeElement === last) {
      e.preventDefault();
      (e.shiftKey ? last : first).focus();
    }
  }

  function _esc(s) {
    const d = document.createElement('div'); d.textContent = s; return d.innerHTML;
  }

  function init() {
    /* Close button wiring */
    document.querySelectorAll('[data-modal-close]').forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.modalClose || btn.closest('.modal-backdrop')?.id;
        close(target);
      });
    });
    /* Open button wiring */
    document.querySelectorAll('[data-modal-open]').forEach(btn => {
      btn.addEventListener('click', () => open(btn.dataset.modalOpen));
    });
    /* Click outside to close */
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
      backdrop.addEventListener('click', e => { if (e.target === backdrop) close(backdrop); });
    });
    /* Escape to close */
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && activeModal) close(activeModal);
    });
  }

  return { open, close, confirm, init };
})();


/* ═══════════════════════════════════════════════════════════
   6. DROPDOWN MANAGER
═══════════════════════════════════════════════════════════ */
const Dropdown = (() => {
  let openDropdown = null;

  function open(triggerEl) {
    const menu = triggerEl.nextElementSibling ?? document.getElementById(triggerEl.dataset.dropdownTarget);
    if (!menu) return;
    closeAll();
    menu.classList.add('open');
    openDropdown = menu;
    triggerEl.setAttribute('aria-expanded', 'true');
  }

  function closeAll() {
    document.querySelectorAll('.dropdown-menu.open').forEach(m => {
      m.classList.remove('open');
      const trigger = m.previousElementSibling;
      if (trigger) trigger.setAttribute('aria-expanded', 'false');
    });
    openDropdown = null;
  }

  function init() {
    document.querySelectorAll('[data-dropdown-toggle]').forEach(btn => {
      btn.setAttribute('aria-expanded', 'false');
      btn.addEventListener('click', e => {
        e.stopPropagation();
        const menu = btn.nextElementSibling;
        if (menu?.classList.contains('open')) closeAll();
        else open(btn);
      });
    });
    document.addEventListener('click', closeAll);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAll(); });
  }

  return { open, closeAll, init };
})();


/* ═══════════════════════════════════════════════════════════
   7. NOTIFICATION PANEL
═══════════════════════════════════════════════════════════ */
const NotificationPanel = (() => {
  let panel    = null;
  let bell     = null;
  let open     = false;
  let count    = 0;

  function init() {
    panel = document.getElementById('notification-panel');
    bell  = document.getElementById('notification-bell');
    if (!bell || !panel) return;

    bell.addEventListener('click', e => { e.stopPropagation(); toggle(); });
    document.addEventListener('click', e => {
      if (open && !panel.contains(e.target) && e.target !== bell) close();
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && open) close(); });
    document.querySelector('[data-action="mark-all-read"]')?.addEventListener('click', markAllRead);
  }

  function toggle() { open ? close() : _open(); }

  function _open() {
    panel?.classList.add('open');
    bell?.setAttribute('aria-expanded', 'true');
    open = true;
  }

  function close() {
    panel?.classList.remove('open');
    bell?.setAttribute('aria-expanded', 'false');
    open = false;
  }

  function setCount(n) {
    count = n;
    const badge = document.querySelector('#notification-bell .badge');
    if (!badge) return;
    badge.style.display = n > 0 ? '' : 'none';
  }

  function markAllRead() {
    document.querySelectorAll('.notification-item.unread').forEach(el => el.classList.remove('unread'));
    setCount(0);
  }

  function addNotification({ title, time, icon = 'fa-bell', iconClass = 'notif-info', unread = true }) {
    const list = panel?.querySelector('.notification-list');
    if (!list) return;
    const item = document.createElement('div');
    item.className = `notification-item${unread ? ' unread' : ''}`;
    item.innerHTML = `
      <div class="notif-icon ${iconClass}"><i class="fa-solid ${icon}"></i></div>
      <div class="notif-content">
        <div class="notif-content-title">${_esc(title)}</div>
        <div class="notif-content-time">${_esc(time)}</div>
      </div>`;
    list.prepend(item);
    if (unread) setCount(count + 1);
  }

  function _esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

  return { init, toggle, close, setCount, markAllRead, addNotification };
})();


/* ═══════════════════════════════════════════════════════════
   8. SEARCH BAR
═══════════════════════════════════════════════════════════ */
const NavSearch = (() => {
  function init() {
    const input = document.getElementById('navbar-search');
    if (!input) return;
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') _handleSearch(input.value.trim());
      if (e.key === 'Escape') input.blur();
    });
    /* Global shortcut: '/' to focus search */
    document.addEventListener('keydown', e => {
      if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
        e.preventDefault();
        input.focus();
      }
    });
  }

  function _handleSearch(query) {
    if (!query) return;
    window.location.href = `/search?q=${encodeURIComponent(query)}`;
  }

  return { init };
})();


/* ═══════════════════════════════════════════════════════════
   9. SKELETON HELPERS
═══════════════════════════════════════════════════════════ */
const Skeleton = (() => {
  function show(containerSelector) {
    document.querySelectorAll(containerSelector).forEach(el => {
      el.dataset.originalContent = el.innerHTML;
      el.innerHTML = `<div class="skeleton skeleton-card"></div>`;
    });
  }

  function hide(containerSelector) {
    document.querySelectorAll(containerSelector).forEach(el => {
      if (el.dataset.originalContent !== undefined) {
        el.innerHTML = el.dataset.originalContent;
        delete el.dataset.originalContent;
      }
    });
  }

  return { show, hide };
})();


/* ═══════════════════════════════════════════════════════════
   10. PROGRESS BAR HELPER
═══════════════════════════════════════════════════════════ */
const ProgressBar = (() => {
  function set(el, percent, type = '') {
    if (typeof el === 'string') el = document.querySelector(el);
    if (!el) return;
    const fill = el.querySelector('.progress-bar-fill') ?? el;
    fill.style.width = `${Math.min(100, Math.max(0, percent))}%`;
    if (type) fill.className = `progress-bar-fill ${type}`;
  }
  function animate(el, from, to, duration = 800) {
    let start = null;
    function step(ts) {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      set(el, from + (to - from) * eased);
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  return { set, animate };
})();


/* ═══════════════════════════════════════════════════════════
   11. TABS
═══════════════════════════════════════════════════════════ */
const Tabs = (() => {
  function init(containerSelector = '[data-tabs]') {
    document.querySelectorAll(containerSelector).forEach(container => {
      const items  = container.querySelectorAll('.tab-item');
      const panels = document.querySelectorAll(`.tab-panel[data-tab-container="${container.id}"]`);

      items.forEach((item, i) => {
        item.setAttribute('role', 'tab');
        item.setAttribute('tabindex', item.classList.contains('active') ? '0' : '-1');
        item.addEventListener('click', () => activate(container, item, panels));
        item.addEventListener('keydown', e => {
          if (e.key === 'ArrowRight') items[(i + 1) % items.length].click();
          if (e.key === 'ArrowLeft')  items[(i - 1 + items.length) % items.length].click();
        });
      });
    });
  }

  function activate(container, activeItem, panels) {
    container.querySelectorAll('.tab-item').forEach(item => {
      const isActive = item === activeItem;
      item.classList.toggle('active', isActive);
      item.setAttribute('tabindex', isActive ? '0' : '-1');
    });
    const targetId = activeItem.dataset.tabTarget;
    panels.forEach(panel => panel.classList.toggle('active', panel.id === targetId));
  }

  return { init, activate };
})();


/* ═══════════════════════════════════════════════════════════
   12. TIMESTAMP FORMATTER
═══════════════════════════════════════════════════════════ */
const TimeFormatter = (() => {
  function relative(date) {
    const d = typeof date === 'string' ? new Date(date) : date;
    const diff = Date.now() - d.getTime();
    const secs  = Math.floor(diff / 1000);
    const mins  = Math.floor(secs / 60);
    const hours = Math.floor(mins / 60);
    const days  = Math.floor(hours / 24);
    if (secs < 60)   return 'just now';
    if (mins < 60)   return `${mins}m ago`;
    if (hours < 24)  return `${hours}h ago`;
    if (days < 7)    return `${days}d ago`;
    return absolute(d);
  }

  function absolute(date) {
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' })
      + ' ' + d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  }

  function applyAll() {
    document.querySelectorAll('[data-timestamp]').forEach(el => {
      const ts = el.dataset.timestamp;
      el.textContent = relative(ts);
      el.title = absolute(ts);
    });
  }

  return { relative, absolute, applyAll };
})();


/* ═══════════════════════════════════════════════════════════
   13. WEBSOCKET LISTENERS (app-level)
═══════════════════════════════════════════════════════════ */
function _initWSListeners() {
  SentinelWS.on('notification', data => {
    NotificationPanel.addNotification({
      title: data.message ?? data.title,
      time: TimeFormatter.relative(data.timestamp ?? new Date()),
      icon: data.icon ?? 'fa-bell',
      iconClass: `notif-${data.type ?? 'info'}`,
    });
    Toast.info(data.title ?? I18n.t('notifications.system_alert'), data.message);
  });

  SentinelWS.on('review_assigned', data => {
    const badge = document.querySelector('.nav-item[href="/review"] .nav-item-badge');
    if (badge) badge.textContent = parseInt(badge.textContent || '0') + 1;
    Toast.warning(I18n.t('notifications.review_assigned'), data?.action ?? '');
  });
}


/* ═══════════════════════════════════════════════════════════
   14. COPY TO CLIPBOARD
═══════════════════════════════════════════════════════════ */
function initCopyButtons() {
  document.querySelectorAll('[data-copy-target]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const target = document.querySelector(btn.dataset.copyTarget);
      if (!target) return;
      try {
        await navigator.clipboard.writeText(target.textContent);
        const orig = btn.textContent;
        btn.textContent = I18n.t('assistant.copied');
        setTimeout(() => { btn.textContent = orig; }, 2000);
      } catch { /* fallback */ }
    });
  });
}


/* ═══════════════════════════════════════════════════════════
   15. LOADER OVERLAY
═══════════════════════════════════════════════════════════ */
const Loader = (() => {
  let overlay = null;

  function show() {
    overlay = document.getElementById('loader-overlay');
    overlay?.classList.add('active');
  }

  function hide() {
    overlay?.classList.remove('active');
  }

  return { show, hide };
})();


/* ═══════════════════════════════════════════════════════════
   16. GLOBAL INIT
═══════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  /* Boot order matters */
  await I18n.init();
  ThemeManager.init();
  SidebarManager.init();
  Modal.init();
  Dropdown.init();
  NotificationPanel.init();
  NavSearch.init();
  Tabs.init();
  TimeFormatter.applyAll();
  initCopyButtons();
  _initWSListeners();

  /* Page transition */
  document.querySelector('.app-content')?.classList.add('page-transition-enter');

  /* Update timestamps every minute */
  setInterval(TimeFormatter.applyAll, 60_000);
});
