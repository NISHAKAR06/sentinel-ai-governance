/**
 * websocket.js — Sentinel AI Governance Platform
 * Manages WebSocket connections for all four channels.
 * Auto-reconnect, heartbeat, typed event dispatch to page handlers.
 */

const SentinelWS = (() => {
  /* ── State ───────────────────────────────────────────────── */
  const sockets     = {};          // channel → WebSocket
  const listeners   = {};          // eventType → [handler]
  const retryCount  = {};          // channel → int
  const retryTimers = {};          // channel → timer id
  const MAX_RETRY   = 10;
  const BASE_DELAY  = 3000;        // ms

  /* ── Channels ────────────────────────────────────────────── */
  const CHANNELS = {
    global:        '/ws',
    dashboard:     '/ws/dashboard',
    review:        '/ws/review',
    audit:         '/ws/audit',
    notifications: '/ws/notifications',
  };

  /* ── Public API ──────────────────────────────────────────── */
  function on(event, handler) {
    if (!listeners[event]) listeners[event] = [];
    listeners[event].push(handler);
    return () => off(event, handler);
  }

  function off(event, handler) {
    listeners[event] = (listeners[event] || []).filter(h => h !== handler);
  }

  function emit(event, data) {
    (listeners[event]   || []).forEach(h => { try { h(data); } catch {} });
    (listeners['*']     || []).forEach(h => { try { h({ event, data }); } catch {} });
  }

  /* ── Connect a channel ───────────────────────────────────── */
  function connect(channel = 'global') {
    if (sockets[channel]?.readyState <= WebSocket.OPEN) return;

    const path  = CHANNELS[channel] || '/ws';
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const token = SentinelAPI.getToken();
    const url   = `${proto}://${location.host}${path}${token ? `?token=${encodeURIComponent(token)}` : ''}`;

    let ws;
    try { ws = new WebSocket(url); }
    catch (e) { _scheduleRetry(channel); return; }

    sockets[channel] = ws;

    ws.onopen = () => {
      retryCount[channel] = 0;
      _updateStatusDot('online');
      emit('ws:open', { channel });
      _startHeartbeat(channel);
      console.debug(`[WS] ${channel} connected`);
    };

    ws.onmessage = ({ data }) => {
      let payload;
      try { payload = JSON.parse(data); } catch { payload = { type: 'raw', data }; }
      const type = payload.type || 'message';
      emit(type, payload.data ?? payload);
      emit('ws:message', payload);
    };

    ws.onclose = ({ code, reason }) => {
      delete sockets[channel];
      _updateStatusDot('offline');
      emit('ws:close', { channel, code });
      if (code !== 1000) _scheduleRetry(channel);
    };

    ws.onerror = () => emit('ws:error', { channel });
  }

  function connectAll() {
    Object.keys(CHANNELS).forEach(ch => connect(ch));
  }

  function disconnect(channel) {
    clearTimeout(retryTimers[channel]);
    const ws = sockets[channel];
    if (ws) { ws.close(1000, 'Explicit disconnect'); delete sockets[channel]; }
  }

  function send(payload, channel = 'global') {
    const ws = sockets[channel];
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload));
      return true;
    }
    return false;
  }

  /* ── Heartbeat ───────────────────────────────────────────── */
  const _heartbeatTimers = {};
  function _startHeartbeat(channel) {
    _heartbeatTimers[channel] = setInterval(() => {
      if (sockets[channel]?.readyState === WebSocket.OPEN) {
        send({ type: 'ping', ts: Date.now() }, channel);
      }
    }, 25000);
  }

  /* ── Retry ───────────────────────────────────────────────── */
  function _scheduleRetry(channel) {
    const count = (retryCount[channel] || 0) + 1;
    if (count > MAX_RETRY) { emit('ws:max_retry', { channel }); return; }
    retryCount[channel] = count;
    const delay = Math.min(BASE_DELAY * Math.pow(1.5, count - 1), 30000);
    _updateStatusDot('reconnecting');
    emit('ws:reconnecting', { channel, attempt: count, delay });
    retryTimers[channel] = setTimeout(() => connect(channel), delay);
  }

  /* ── Status indicator ────────────────────────────────────── */
  function _updateStatusDot(status) {
    const el  = document.getElementById('ws-status');
    const dot = el?.querySelector('.ws-dot');
    const lbl = el?.querySelector('.ws-label');
    const colors = { online: '#16A34A', offline: '#DC2626', reconnecting: '#F59E0B' };
    const labels = { online: 'Live', offline: 'Disconnected', reconnecting: 'Reconnecting…' };
    if (dot) dot.style.background = colors[status] || '#94A3B8';
    if (lbl) lbl.textContent = labels[status] || status;
    if (el) el.dataset.status = status;
  }

  /* ── Helpers ─────────────────────────────────────────────── */
  function isConnected(channel = 'global') {
    return sockets[channel]?.readyState === WebSocket.OPEN;
  }

  /* ── Auto-connect when DOM ready ─────────────────────────── */
  document.addEventListener('DOMContentLoaded', () => {
    // Only connect if not on login page
    if (!window.location.pathname.includes('/login')) connectAll();
  });

  return { on, off, connect, connectAll, disconnect, send, isConnected };
})();
