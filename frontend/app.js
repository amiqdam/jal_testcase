/* App Router — Client-side hash-based routing */
(function() {
  const app = document.getElementById('app');

  function getRoute() {
    return window.location.hash.replace('#', '') || '/';
  }

  function renderAdminShell() {
    const route = getRoute();
    app.innerHTML = `
      <nav class="admin-nav">
        <span class="logo">🎓 JAL Admin</span>
        <a href="#/admin" class="${route === '/admin' ? 'active' : ''}">💬 Chat Monitor</a>
        <a href="#/admin/dashboard" class="${route === '/admin/dashboard' ? 'active' : ''}">📊 Dashboard</a>
        <a href="#/admin/analytics" class="${route === '/admin/analytics' ? 'active' : ''}">📈 Analytics</a>
        <a href="#/" style="margin-left:auto;opacity:0.6">← User View</a>
      </nav>
      <div id="admin-main" style="height:calc(100vh - 52px);overflow:hidden"></div>`;
    return document.getElementById('admin-main');
  }

  function route() {
    const path = getRoute();

    if (path === '/' || path === '') {
      renderChatbot(app);
    } else if (path === '/admin') {
      const container = renderAdminShell();
      renderAdminChat(container);
    } else if (path === '/admin/dashboard') {
      const container = renderAdminShell();
      container.style.overflow = 'auto';
      renderDashboard(container);
    } else if (path === '/admin/analytics') {
      const container = renderAdminShell();
      container.style.overflow = 'auto';
      renderAnalytics(container);
    } else if (path.startsWith('/admin/lead/')) {
      const leadId = path.split('/admin/lead/')[1];
      const container = renderAdminShell();
      renderLeadDetail(container, leadId);
    } else {
      renderChatbot(app);
    }
  }

  window.addEventListener('hashchange', route);
  window.addEventListener('DOMContentLoaded', route);
  
  // Initial route
  route();
})();
