/**
 * assistant.js — AI Assistant: POST /api/v1/chat/send
 * Live action preview, approve/reject/modify via review/execution APIs.
 */
const AssistantPage = (() => {
  let convId = null, isThinking = false;
  const messages = [];

  /* ── DOM refs ────────────────────────────────────────────── */
  const $ = id => document.getElementById(id);
  const r = () => ({
    msgs:    $('chat-messages'),
    ta:      $('chat-textarea'),
    send:    $('chat-send-btn'),
    clear:   $('chat-clear-btn'),
    newConv: $('new-conversation-btn'),
    previewCard:  $('action-preview-card'),
    previewEmpty: $('action-preview-empty'),
    previewBody:  $('action-preview-body'),
    previewFooter:$('action-preview-footer'),
    histList: $('conversation-history-list'),
    charCount:$('char-count'),
  });

  /* ── Append bubble ───────────────────────────────────────── */
  function _appendMsg(role, content, ts) {
    const refs = r();
    if (!refs.msgs) return;
    refs.msgs.querySelector('.chat-welcome')?.remove();
    const time = _rel(ts || new Date());
    const isUser = role === 'user';
    const div = document.createElement('div');
    div.className = `message-row ${isUser ? 'user' : 'sentinel'}`;
    div.innerHTML = `
      <div class="message-avatar ${isUser ? 'user' : 'sentinel'}">${isUser ? '<i class="fa-solid fa-user"></i>' : 'AI'}</div>
      <div class="message-content">
        <div class="message-bubble ${isUser ? 'user' : 'sentinel'}">${_fmt(content)}</div>
        <div class="message-meta">
          <span class="message-time">${isUser ? 'You' : 'Sentinel AI'} · ${time}</span>
        </div>
      </div>`;
    refs.msgs.appendChild(div);
    refs.msgs.scrollTop = refs.msgs.scrollHeight;
  }

  /* ── Thinking indicator ──────────────────────────────────── */
  function _showThinking() {
    const refs = r();
    if (!refs.msgs) return;
    const div = document.createElement('div');
    div.id = 'thinking-row';
    div.className = 'message-row sentinel';
    div.innerHTML = `
      <div class="message-avatar sentinel">AI</div>
      <div class="message-content">
        <div class="thinking-bubble">
          <div class="loading-dots"><span></span><span></span><span></span></div>
          <span class="thinking-text text-sm">Sentinel is analysing your request…</span>
        </div>
      </div>`;
    refs.msgs.appendChild(div);
    refs.msgs.scrollTop = refs.msgs.scrollHeight;
  }

  /* ── Action preview ──────────────────────────────────────── */
  function _renderPreview(preview) {
    const refs = r();
    if (!refs.previewBody || !preview) return;

    refs.previewEmpty?.classList.add('hidden');
    refs.previewBody.style.display = '';
    if (refs.previewFooter) refs.previewFooter.style.display = '';

    const confPct = Math.round((preview.confidence || 0) * 100);
    const riskColor = { low:'success', medium:'warning', high:'danger', critical:'danger' }[preview.risk_level] || 'neutral';

    refs.previewBody.innerHTML = `
      <div class="action-preview-body" style="padding:var(--space-5)">
        <div class="action-field">
          <span class="action-field-label">Intent</span>
          <span class="action-field-value">${_esc(preview.intent||'—')}</span>
        </div>
        <div class="action-field">
          <span class="action-field-label">Operation</span>
          <span class="action-field-value font-mono text-sm">${_esc(preview.operation||preview.operation_type||'—')}</span>
        </div>
        <div class="action-field">
          <span class="action-field-label">Target Resource</span>
          <span class="action-field-value">${_esc(preview.target_resource||'—')}</span>
        </div>
        <div class="action-field">
          <span class="action-field-label">Affected Records</span>
          <span class="action-field-value"><span class="badge badge-${riskColor}">${preview.affected_records ?? 0} records</span></span>
        </div>
        <div class="action-field">
          <span class="action-field-label">Confidence</span>
          <div class="confidence-bar-wrap">
            <div class="progress-bar-wrap flex-1">
              <div class="progress-bar-fill ${confPct >= 80 ? 'success' : confPct >= 50 ? '' : 'danger'}" style="width:${confPct}%"></div>
            </div>
            <span class="confidence-value">${confPct}%</span>
          </div>
        </div>
        <div class="action-field">
          <span class="action-field-label">Risk Level</span>
          <span class="badge badge-${riskColor} badge-dot">${preview.risk_level||'—'}</span>
        </div>
        ${preview.action_json ? `
        <div class="action-field mt-3">
          <span class="action-field-label">Generated Action JSON</span>
          <div class="code-block-wrap mt-2">
            <pre class="code-block" id="action-json-pre">${_esc(JSON.stringify(preview.action_json, null, 2))}</pre>
            <button class="code-copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('action-json-pre').textContent)">Copy</button>
          </div>
        </div>` : ''}
      </div>`;

    if (refs.previewFooter && preview.action_id) {
      refs.previewFooter.innerHTML = `
        <button class="btn btn-success btn-sm" onclick="AssistantPage.approveAction('${preview.action_id}')">
          <i class="fa-solid fa-check"></i> Approve
        </button>
        <button class="btn btn-outline-danger btn-sm" onclick="AssistantPage.rejectAction('${preview.action_id}')">
          <i class="fa-solid fa-xmark"></i> Reject
        </button>
        <button class="btn btn-secondary btn-sm" onclick="AssistantPage.viewGovernance('${preview.action_id}')">
          <i class="fa-solid fa-scale-balanced"></i> Governance
        </button>`;
    }
  }

  function _clearPreview() {
    const refs = r();
    if (refs.previewBody) { refs.previewBody.innerHTML = ''; refs.previewBody.style.display = 'none'; }
    if (refs.previewFooter) { refs.previewFooter.innerHTML = ''; refs.previewFooter.style.display = 'none'; }
    refs.previewEmpty?.classList.remove('hidden');
  }

  /* ── Send message ────────────────────────────────────────── */
  async function send() {
    const refs = r();
    if (isThinking || !refs.ta) return;
    const text = refs.ta.value.trim();
    if (!text) return;

    refs.ta.value = '';
    _autoResize(refs.ta);
    if (refs.send) refs.send.disabled = true;

    messages.push({ role: 'user', content: text });
    _appendMsg('user', text);
    isThinking = true;
    _showThinking();

    try {
      const res = await SentinelAPI.chat.send({
        message:         text,
        conversation_id: convId,
      });
      convId = res.conversation_id || convId;
      $('thinking-row')?.remove();
      _appendMsg('assistant', res.response || res.message || '…');
      messages.push({ role: 'assistant', content: res.response || '' });
      if (res.action_preview) _renderPreview(res.action_preview);
      _addHistory(convId, text);
    } catch (e) {
      $('thinking-row')?.remove();
      _appendMsg('assistant', `Error: ${e.message}`);
    } finally {
      isThinking = false;
      if (refs.send) refs.send.disabled = false;
      refs.ta?.focus();
    }
  }

  /* ── Approve / reject ────────────────────────────────────── */
  async function approveAction(actionId) {
    try {
      await SentinelAPI.review.approve(actionId, 'Approved from AI Assistant');
      if (typeof Toast !== 'undefined') Toast.success('Action approved');
      _clearPreview();
    } catch (e) { if (typeof Toast !== 'undefined') Toast.danger('Approval failed', e.message); }
  }

  async function rejectAction(actionId) {
    if (typeof Modal !== 'undefined') {
      Modal.confirm({
        title: 'Reject Action',
        message: 'Are you sure you want to reject this action?',
        type: 'danger',
        onConfirm: async () => {
          try {
            await SentinelAPI.review.reject(actionId, 'Rejected from AI Assistant');
            if (typeof Toast !== 'undefined') Toast.danger('Action rejected');
            _clearPreview();
          } catch (e) { if (typeof Toast !== 'undefined') Toast.danger('Error', e.message); }
        },
      });
    } else {
      if (!confirm('Reject this action?')) return;
      await SentinelAPI.review.reject(actionId, 'Rejected from AI Assistant').catch(() => {});
      _clearPreview();
    }
  }

  function viewGovernance(actionId) {
    window.location.href = `/governance?action_id=${actionId}`;
  }

  /* ── Conversation history list ───────────────────────────── */
  function _addHistory(id, text) {
    const list = r().histList;
    if (!list) return;
    list.querySelector('.empty-state')?.remove();
    const existing = list.querySelector(`[data-conv-id="${id}"]`);
    if (existing) return;
    const item = document.createElement('div');
    item.className = 'history-item';
    item.dataset.convId = id;
    item.innerHTML = `
      <div class="history-item-title">${_esc(text.substring(0, 50))}${text.length > 50 ? '…' : ''}</div>
      <div class="history-item-meta">${_rel(new Date())}</div>`;
    list.prepend(item);
  }

  /* ── Suggested prompts ───────────────────────────────────── */
  function _initSuggested() {
    document.querySelectorAll('.suggested-prompt-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const refs = r();
        if (!refs.ta) return;
        refs.ta.value = btn.dataset.prompt || btn.textContent.trim();
        _autoResize(refs.ta);
        if (refs.send) refs.send.disabled = !refs.ta.value.trim();
        refs.ta.focus();
      });
    });
  }

  /* ── Helpers ─────────────────────────────────────────────── */
  function _autoResize(ta) {
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
  }
  function _esc(s) { const d = document.createElement('div'); d.textContent = String(s||''); return d.innerHTML; }
  function _rel(ts) {
    if (!ts) return 'now';
    const diff = Date.now() - new Date(ts).getTime();
    const m = Math.floor(diff / 60000);
    return m < 1 ? 'just now' : m < 60 ? `${m}m ago` : `${Math.floor(m/60)}h ago`;
  }
  function _fmt(content) {
    let s = _esc(content);
    s = s.replace(/`([^`]+)`/g, '<code class="font-mono text-xs" style="background:var(--bg-surface-2);padding:1px 5px;border-radius:4px">$1</code>');
    s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\n/g, '<br>');
    return s;
  }

  /* ── Init ────────────────────────────────────────────────── */
  function init() {
    const refs = r();
    refs.send?.addEventListener('click', send);
    refs.ta?.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } });
    refs.ta?.addEventListener('input', () => {
      _autoResize(refs.ta);
      if (refs.send) refs.send.disabled = !refs.ta.value.trim();
      if (refs.charCount) refs.charCount.textContent = refs.ta.value.length;
    });
    refs.clear?.addEventListener('click', async () => {
      await SentinelAPI.chat.clear().catch(() => {});
      convId = null;
      messages.length = 0;
      if (refs.msgs) refs.msgs.innerHTML = `
        <div class="chat-welcome">
          <div class="chat-welcome-icon"><i class="fa-solid fa-robot"></i></div>
          <h2 class="chat-welcome-title">Start a conversation to get started</h2>
          <p class="chat-welcome-desc">Ask Sentinel AI to perform governed operations on your infrastructure</p>
        </div>`;
      _clearPreview();
    });
    refs.newConv?.addEventListener('click', () => {
      convId = null; messages.length = 0;
      if (refs.msgs) refs.msgs.innerHTML = '';
      _clearPreview();
    });
    _initSuggested();
  }

  document.addEventListener('DOMContentLoaded', init);
  return { send, approveAction, rejectAction, viewGovernance };
})();
