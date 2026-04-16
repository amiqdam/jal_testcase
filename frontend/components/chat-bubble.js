/* Chat Bubble Component — User right, Bot left */
function createChatBubble(message) {
  const bubble = document.createElement('div');
  const dir = message.direction || message.sender;
  const isUser = (dir === 'inbound' || dir === 'user');
  const isAdmin = (dir === 'admin' || message.sender === 'admin');

  bubble.className = `chat-bubble ${isAdmin ? 'admin-reply' : isUser ? 'user' : 'bot'}`;

  let html = '';
  if (isAdmin) {
    html += '<div class="admin-badge">👨‍💼 Admin</div>';
  }
  html += `<div class="bubble-content">${formatContent(message.content || '')}</div>`;
  if (message.created_at) {
    const t = new Date(message.created_at);
    html += `<span class="timestamp">${t.toLocaleTimeString('id-ID', {hour:'2-digit',minute:'2-digit'})}</span>`;
  }
  bubble.innerHTML = html;
  return bubble;
}

function formatContent(text) {
  // Bold **text**
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Links
  text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" style="color:var(--accent-secondary)">$1</a>');
  return text;
}
