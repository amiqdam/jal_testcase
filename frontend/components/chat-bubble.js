/* Chat Bubble Component */
function createChatBubble(message) {
  const bubble = document.createElement('div');
  const isInbound = message.direction === 'inbound';
  const isAdmin = message.sender === 'admin' || 
    (message.processing_log && typeof message.processing_log === 'object' && message.processing_log.source === 'admin_manual');
  
  bubble.className = `chat-bubble ${isInbound ? 'inbound' : isAdmin ? 'admin-reply' : 'outbound'}`;
  
  let badgeHtml = '';
  if (isAdmin && !isInbound) {
    badgeHtml = '<span class="admin-badge">👤 Admin</span><br>';
  }
  
  const time = message.created_at ? new Date(message.created_at).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) : '';
  
  // Convert markdown-like bold
  let content = (message.content || '').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  content = content.replace(/\n/g, '<br>');
  
  bubble.innerHTML = `${badgeHtml}<span class="bubble-content">${content}</span><span class="timestamp">${time}</span>`;
  return bubble;
}

function createTypingIndicator() {
  const el = document.createElement('div');
  el.className = 'typing-indicator';
  el.id = 'typing-indicator';
  el.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
  return el;
}
