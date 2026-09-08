/**
 * Interactive Carbon Agent chat controller.
 * Manages message stream, real tool execution traces, markdown formatting,
 * and quick-inquiry prompt chips.
 */

let conversationHistory = [];

const chatMessagesContainer = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const btnClearChat = document.getElementById('btn-clear-chat');

function initChat() {
  // Render welcome message
  renderWelcomeMessage();

  // Attach submit handler
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    chatInput.value = '';
    await handleUserMessage(query);
  });

  // Attach quick prompt chips
  document.querySelectorAll('.prompt-chips .chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const q = chip.getAttribute('data-query');
      if (q) handleUserMessage(q);
    });
  });

  // Clear chat button
  btnClearChat.addEventListener('click', () => {
    conversationHistory = [];
    chatMessagesContainer.innerHTML = '';
    renderWelcomeMessage();
  });
}

function renderWelcomeMessage() {
  appendAgentMessage(
    `Hello Administrator! I am your **Campus Carbon Management Agent**.\n\n` +
    `I can calculate your emissions, analyze 6-month historical trends, identify your largest emission sources, model What-If reduction scenarios, and generate prioritized sustainability action plans.\n\n` +
    `*Try clicking a quick prompt below or asking a question!*`
  );
}

async function handleUserMessage(text) {
  // Append user message
  appendUserMessage(text);
  conversationHistory.push({ role: 'user', content: text });

  // Show typing indicator
  const typingBubble = appendTypingIndicator();
  chatInput.disabled = true;

  try {
    const res = await window.API.sendChatMessage(text, conversationHistory);
    typingBubble.remove();

    // Append agent response with tool execution traces
    appendAgentMessage(res.response, res.tool_calls || []);
    conversationHistory.push({ role: 'assistant', content: res.response });
  } catch (err) {
    typingBubble.remove();
    appendAgentMessage(`⚠️ **Error:** Unable to process request. (${err.message})`);
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
    scrollToBottom();
  }
}

function appendUserMessage(text) {
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble user';
  bubble.innerHTML = `
    <div class="msg-avatar user-avatar">
      <i data-lucide="user"></i>
    </div>
    <div class="msg-content">
      <div class="msg-body">${escapeHtml(text)}</div>
    </div>
  `;
  chatMessagesContainer.appendChild(bubble);
  if (window.lucide) window.lucide.createIcons();
  scrollToBottom();
}

function appendAgentMessage(markdownText, toolCalls = []) {
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble agent';

  let toolTraceHtml = '';
  if (toolCalls && toolCalls.length > 0) {
    const traceCount = toolCalls.length;
    const toolNames = toolCalls.map(tc => tc.tool).join(', ');

    toolTraceHtml = `
      <div class="tool-trace-card">
        <div class="tool-trace-header" onclick="this.nextElementSibling.classList.toggle('hidden')">
          <span>🛠️ <strong>Agent Tool Trace:</strong> ${traceCount} tool(s) invoked (${toolNames})</span>
          <span style="font-size: 0.7rem;">[Inspect JSON]</span>
        </div>
        <div class="tool-trace-details hidden">
${escapeHtml(JSON.stringify(toolCalls, null, 2))}
        </div>
      </div>
    `;
  }

  const parsedBody = parseSimpleMarkdown(markdownText);

  bubble.innerHTML = `
    <div class="msg-avatar agent-avatar-sm">
      <i data-lucide="bot"></i>
    </div>
    <div class="msg-content">
      ${toolTraceHtml}
      <div class="msg-body">${parsedBody}</div>
    </div>
  `;

  chatMessagesContainer.appendChild(bubble);
  if (window.lucide) window.lucide.createIcons();
  scrollToBottom();
}

function appendTypingIndicator() {
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble agent';
  bubble.id = 'typing-indicator';
  bubble.innerHTML = `
    <div class="msg-avatar agent-avatar-sm">
      <i data-lucide="bot"></i>
    </div>
    <div class="msg-content">
      <div class="msg-body" style="font-style: italic; color: #34d399;">
        <span class="pulse-dot" style="display:inline-block; margin-right:6px;"></span>
        Determining tools & analyzing campus data...
      </div>
    </div>
  `;
  chatMessagesContainer.appendChild(bubble);
  if (window.lucide) window.lucide.createIcons();
  scrollToBottom();
  return bubble;
}

function scrollToBottom() {
  chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
}

function escapeHtml(str) {
  return (str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/**
 * Lightweight markdown parser for chat formatting.
 * Handles headings, tables, bullet points, bold, italics, and blockquotes.
 */
function parseSimpleMarkdown(md) {
  if (!md) return '';

  let html = md;

  // Tables
  html = html.replace(/((?:\|[^\n]+\|\r?\n)+)/g, (match) => {
    const lines = match.trim().split(/\r?\n/);
    if (lines.length < 2) return match;

    const headers = lines[0].split('|').slice(1, -1).map(h => h.trim());
    // skip separator line lines[1]
    const rows = lines.slice(2).map(line => {
      const cells = line.split('|').slice(1, -1).map(c => c.trim());
      return `<tr>${cells.map(c => `<td>${parseInlineMarkdown(c)}</td>`).join('')}</tr>`;
    });

    return `<table><thead><tr>${headers.map(h => `<th>${parseInlineMarkdown(h)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table>`;
  });

  // Headers
  html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

  // Blockquotes
  html = html.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');

  // Bullet Lists
  html = html.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');
  html = html.replace(/((?:<li>.*<\/li>\s*)+)/g, '<ul>$1</ul>');

  // Inline formatting
  html = parseInlineMarkdown(html);

  // Newlines to paragraph breaks (except inside tables and lists)
  html = html.replace(/\n{2,}/g, '<br/><br/>');

  return html;
}

function parseInlineMarkdown(str) {
  return str
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.1);padding:1px 4px;border-radius:4px;">$1</code>');
}

window.triggerAgentChat = function(promptText) {
  handleUserMessage(promptText);
};

document.addEventListener('DOMContentLoaded', () => {
  initChat();
});
