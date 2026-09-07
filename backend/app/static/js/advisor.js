const chatWindow = document.getElementById("chat-window");

function timeNow() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Turn a plain-text advisor reply into safe, readable HTML.
function formatReply(text) {
  let s = escapeHtml(text);
  // Linkify URLs
  s = s.replace(/(https?:\/\/[^\s)]+)(?![^<]*>)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
  // Bold **text**
  s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

  // If the reply has "(1) ... (2) ..." style steps, render them as an ordered list.
  if (/\(1\)/.test(s) && /\(2\)/.test(s)) {
    const intro = s.slice(0, s.indexOf("(1)")).trim();
    const rest = s.slice(s.indexOf("(1)"));
    const items = rest
      .split(/\((\d+)\)\s*/)
      .filter((chunk) => chunk && !/^\d+$/.test(chunk))
      .map((chunk) => `<li>${chunk.replace(/[,;]\s*$/, "").trim()}</li>`)
      .join("");
    return (intro ? `<p>${intro}</p>` : "") + `<ol>${items}</ol>`;
  }

  // Otherwise split into paragraphs on blank lines, and honor single newlines.
  return s
    .split(/\n{2,}/)
    .map((para) => `<p>${para.replace(/\n/g, "<br>")}</p>`)
    .join("");
}

function appendBubble(role, text, animate = true) {
  const row = document.createElement("div");
  row.className = `chat-row ${role}`;
  if (!animate) row.style.animation = "none";

  const avatar = document.createElement("div");
  avatar.className = "chat-mini-avatar";
  avatar.textContent = role === "user" ? "🧑" : "🤖";

  const stack = document.createElement("div");
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role}`;
  if (role === "assistant") bubble.innerHTML = formatReply(text);
  else bubble.textContent = text;

  const time = document.createElement("div");
  time.className = "chat-time";
  time.textContent = timeNow();

  stack.appendChild(bubble);
  stack.appendChild(time);
  row.appendChild(avatar);
  row.appendChild(stack);
  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return row;
}

function showTyping() {
  const row = document.createElement("div");
  row.className = "chat-row assistant";
  row.innerHTML =
    '<div class="chat-mini-avatar">🤖</div>' +
    '<div class="chat-bubble assistant"><div class="typing-dots"><span></span><span></span><span></span></div></div>';
  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return row;
}

async function ask(message) {
  appendBubble("user", message);
  const typing = showTyping();
  try {
    const res = await api("/api/chatbot/message", { method: "POST", body: JSON.stringify({ message }) });
    typing.remove();
    appendBubble("assistant", res.reply);
  } catch (err) {
    typing.remove();
    appendBubble("assistant", "Sorry, something went wrong: " + err.message);
  }
}

document.getElementById("chat-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  if (!input.value.trim()) return;
  ask(input.value.trim());
  input.value = "";
  input.focus();
});

async function loadHistory() {
  const { history } = await api("/api/chatbot/history");
  if (!history.length) {
    appendBubble(
      "assistant",
      "Hi! I'm your AI Career Advisor. Ask me anything about your career path, skills to learn, CV tips, or interview prep — or tap a suggestion below to get started."
    );
    return;
  }
  history.forEach((h) => appendBubble(h.role, h.message, false));
}

loadHistory();
