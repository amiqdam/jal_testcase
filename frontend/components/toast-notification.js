/* Toast Notification Component */
const ToastManager = {
  container: null,
  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  },
  show(message, type = 'info', duration = 5000) {
    this.init();
    const icons = { info: '💬', warning: '⚠️', error: '🚨', success: '✅' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || '💬'}</span>
      <span class="toast-message">${message}</span>
      <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;
    this.container.appendChild(toast);
    setTimeout(() => { if (toast.parentElement) toast.remove(); }, duration);
  }
};

/* Polling for new events (admin only) */
let _lastEventCheck = new Date().toISOString();
let _notifInterval = null;
function startNotificationPolling() {
  if (_notifInterval) clearInterval(_notifInterval);
  _notifInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/admin/chat/events?since=${_lastEventCheck}`);
      const data = await res.json();
      if (data.new_leads > 0) ToastManager.show(`${data.new_leads} lead baru!`, 'info');
      if (data.new_complaints > 0) ToastManager.show(`${data.new_complaints} keluhan baru!`, 'error');
      _lastEventCheck = new Date().toISOString();
    } catch(e) {}
  }, 15000);
}
function stopNotificationPolling() {
  if (_notifInterval) { clearInterval(_notifInterval); _notifInterval = null; }
}
