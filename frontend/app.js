/* App Router — Hash-based client-side routing */
(function() {
  function route() {
    const hash = window.location.hash || '#/';
    stopNotificationPolling();

    if (hash === '#/' || hash === '' || hash === '#') {
      renderChatbot();
    } else if (hash === '#/admin' || hash === '#/admin/chat') {
      renderAdminChat();
    } else if (hash === '#/admin/dashboard') {
      renderDashboard();
    } else if (hash === '#/admin/analytics') {
      renderAnalytics();
    } else if (hash === '#/admin/database') {
      renderDatabase();
    } else if (hash === '#/admin/settings') {
      renderSettings();
    } else if (hash.startsWith('#/admin/lead/')) {
      const leadId = hash.replace('#/admin/lead/', '');
      renderLeadDetail(leadId);
    } else {
      renderChatbot();
    }
  }

  window.addEventListener('hashchange', route);
  window.addEventListener('DOMContentLoaded', route);
})();
