// Chat page logic: messages, file uploads, chat list, guest limits and windows.
// Logged-in users: chats are saved on the server.
// Guests: chats are kept only in this page and are gone after a refresh.
// account.js (logged-in users only) adds the account menu and settings.
// Answers stream from the AI model through the API. Every change sends the token of this
// browser's session (header X-CSRF-Token) against forged requests from other sites.

const config = JSON.parse(document.getElementById("page-config").textContent);
const isGuest = !config.user;
const prefs = config.prefs;

const el = {
  sidebar: document.getElementById("sidebar"),
  backdrop: document.getElementById("backdrop"),
  menuBtn: document.getElementById("menuBtn"),
  history: document.getElementById("history"),
  newChat: document.getElementById("newChat"),
  chat: document.getElementById("chat"),
  welcome: document.getElementById("welcome"),
  messages: document.getElementById("messages"),
  composer: document.getElementById("composer"),
  input: document.getElementById("input"),
  sendBtn: document.getElementById("sendBtn"),
  attachBtn: document.getElementById("attachBtn"),
  fileInput: document.getElementById("fileInput"),
  attachments: document.getElementById("attachments"),
  dropOverlay: document.getElementById("dropOverlay"),
  guestBar: document.getElementById("guestBar"),
  authModal: document.getElementById("authModal"),
  modalTitle: document.getElementById("modalTitle"),
  modalText: document.getElementById("modalText"),
  confirmModal: document.getElementById("confirmModal"),
  confirmTitle: document.getElementById("confirmTitle"),
  confirmText: document.getElementById("confirmText"),
  confirmOk: document.getElementById("confirmOk"),
  confirmCancel: document.getElementById("confirmCancel"),
  toast: document.getElementById("toast"),
};

let chats = [];          // {id, title, updated_at} plus messages for guests
let currentId = null;    // the open chat
let guestLeft = config.guest_left;
let pending = [];        // files attached to the next message
let busy = false;        // true while waiting for a reply

// ---------- Small helpers ----------

// Text in the chosen language. {name} parts are filled in one pass.
function tr(key, values = {}) {
  const text = config.t[key] || key;
  return text.replace(/\{(\w+)\}/g, (m, k) => (k in values ? values[k] : m));
}

function make(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;   // textContent keeps user text safe
  return node;
}

function nowSeconds() {
  return Date.now() / 1000;
}

function formatSize(size) {
  if (size < 1024) return size + " B";
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + " KB";
  return (size / (1024 * 1024)).toFixed(1) + " MB";
}

function extensionOf(name) {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i).toLowerCase() : "";
}

function scrollDown() {
  el.chat.scrollTop = el.chat.scrollHeight;
}

// The text for an error code of the API (its "detail"), in the chosen language
function errorText(code, status) {
  if (status === 422) return tr("err_invalid_input");
  if (typeof code === "string" && config.t["err_" + code]) return tr("err_" + code, { n: config.guest_limit });
  return tr("request_failed");
}

// Every change sends the token of this browser's session
function withToken(options) {
  const method = (options.method || "GET").toUpperCase();
  if (method === "GET" || method === "HEAD") return options;
  return { ...options, headers: { ...(options.headers || {}), "X-CSRF-Token": config.csrf } };
}

// fetch wrapper: returns the JSON or throws an error with the server's message
async function api(path, options = {}) {
  let res;
  try {
    res = await fetch(path, withToken(options));
  } catch (e) {
    throw new Error(tr("err_network"));
  }
  let data = null;
  try {
    data = await res.json();
  } catch (e) {
    // no JSON body
  }
  if (!res.ok) {
    const err = new Error(errorText(data && data.detail, res.status));
    err.status = res.status;
    throw err;
  }
  return data;
}

// Sends a message and reads the answer as it is written (Server-Sent Events): chat (its ID
// and title), delta (a piece of the answer), then done or error
async function streamChat(body, onEvent) {
  let res;
  try {
    res = await fetch("/v1/chat", withToken(jsonBody("POST", body)));
  } catch (e) {
    throw new Error(tr("err_network"));
  }
  if (!res.ok) {
    let data = null;
    try {
      data = await res.json();
    } catch (e) {
      // no JSON body
    }
    const err = new Error(errorText(data && data.detail, res.status));
    err.status = res.status;
    throw err;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let cut;
    while ((cut = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, cut);
      buffer = buffer.slice(cut + 2);
      let name = "message";
      let data = "";
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) name = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (data) onEvent(name, JSON.parse(data));
    }
  }
}

// A saved message from the server in the form this page shows
function fromServer(m) {
  const failed = m.status === "failed";
  return {
    role: m.role,
    text: m.content || (failed ? tr("err_model_error") : ""),
    html: m.html,
    mode: failed ? "error" : null,
  };
}

function jsonBody(method, body) {
  return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

const ICONS = {
  dots: '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><circle cx="5" cy="12" r="1.8"/><circle cx="12" cy="12" r="1.8"/><circle cx="19" cy="12" r="1.8"/></svg>',
  pencil: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>',
  trash: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v6M14 11v6"/></svg>',
};

// ---------- Windows (modals) and the short confirmation message ----------

function openOverlay(overlay) {
  if (!overlay) return;
  overlay.classList.add("show");
  const focusTarget = overlay.querySelector("[autofocus], input:not([disabled]), textarea, .btn-primary, .btn-ghost");
  if (focusTarget) setTimeout(() => focusTarget.focus(), 30);
}

function closeOverlay(overlay) {
  if (!overlay) return;
  overlay.classList.remove("show");
  if (overlay === el.confirmModal) confirmAction = null;
}

function openOverlays() {
  return [...document.querySelectorAll(".modal-overlay.show")];
}

// Close buttons (data-close) and a click outside close every window
for (const overlay of document.querySelectorAll(".modal-overlay")) {
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeOverlay(overlay);
  });
  for (const button of overlay.querySelectorAll("[data-close]")) {
    button.addEventListener("click", () => closeOverlay(overlay));
  }
}

let toastTimer = null;
function showToast(text) {
  el.toast.textContent = text;
  el.toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.toast.classList.remove("show"), 2600);
}

// One confirm window for every delete: title, text and what happens on Delete
let confirmAction = null;
function askConfirm(title, text, okLabel, action) {
  el.confirmTitle.textContent = title;
  el.confirmText.textContent = text;
  el.confirmOk.textContent = okLabel;
  confirmAction = action;
  openOverlay(el.confirmModal);
  setTimeout(() => el.confirmCancel.focus(), 40);
}

el.confirmOk.addEventListener("click", async () => {
  const action = confirmAction;
  closeOverlay(el.confirmModal);
  if (action) await action();
});
el.confirmCancel.addEventListener("click", () => closeOverlay(el.confirmModal));

// ---------- Login prompt for guests ----------

function showAuthModal(reason) {
  if (!el.authModal) return;
  if (reason === "upload") {
    el.modalTitle.textContent = tr("upload_title");
    el.modalText.textContent = tr("upload_text");
  } else {
    el.modalTitle.textContent = tr("limit_title");
    el.modalText.textContent = tr("limit_text", { n: config.guest_limit });
  }
  openOverlay(el.authModal);
}

function renderGuestBar() {
  if (!isGuest || !el.guestBar) return;
  el.guestBar.innerHTML = "";
  if (guestLeft > 0) {
    el.guestBar.classList.remove("empty");
    const text = make("span");
    text.append(tr("guest_bar_label") + " ",
                make("strong", "", tr("guest_bar_count", { left: guestLeft, limit: config.guest_limit })),
                " " + tr("guest_bar_rest"));
    const link = make("a", "", tr("guest_bar_link"));
    link.href = "/login";
    el.guestBar.append(text, link);
    el.input.disabled = false;
    el.input.placeholder = tr("message_placeholder", { app: document.title });
  } else {
    el.guestBar.classList.add("empty");
    const login = make("a", "", tr("log_in"));
    login.href = "/login";
    el.guestBar.append(make("span", "", tr("guest_out")));
    if (config.signup_open) {
      // The sign-up link only when an admin has not turned sign-up off
      const signup = make("a", "", tr("guest_out_signup"));
      signup.href = "/signup";
      el.guestBar.append(signup, make("span", "", tr("or")));
    }
    el.guestBar.append(login);
    el.input.disabled = true;
    el.input.placeholder = tr("guest_out_placeholder");
  }
}

// ---------- Chat list ----------

async function loadChats() {
  if (!isGuest) {
    try {
      // The server sends times as text. The list groups them by seconds
      chats = (await api("/v1/chats")).map((c) => ({ ...c, updated_at: Date.parse(c.updated_at) / 1000 }));
    } catch (err) {
      chats = [];
    }
  }
  renderHistory();
}

// Today, Yesterday, Previous 7 days, Previous 30 days or Older
function groupLabel(seconds) {
  const day = 24 * 3600 * 1000;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const t = seconds * 1000;
  if (t >= today.getTime()) return tr("today");
  if (t >= today.getTime() - day) return tr("yesterday");
  if (t >= today.getTime() - 7 * day) return tr("prev7");
  if (t >= today.getTime() - 30 * day) return tr("prev30");
  return tr("older");
}

function renderHistory() {
  closeChatMenu();
  el.history.innerHTML = "";
  if (!chats.length) {
    el.history.appendChild(make("div", "history-empty", tr("no_chats")));
    return;
  }
  const sorted = [...chats].sort((a, b) => b.updated_at - a.updated_at);
  let lastGroup = null;
  for (const chat of sorted) {
    const group = groupLabel(chat.updated_at);
    if (group !== lastGroup) {
      el.history.appendChild(make("div", "history-group", group));
      lastGroup = group;
    }
    el.history.appendChild(historyItem(chat));
  }
}

function historyItem(chat) {
  const item = make("div", "history-item" + (chat.id === currentId ? " active" : ""));
  item.dataset.id = chat.id;

  const link = make("button", "history-link", chat.title);
  link.type = "button";
  link.title = chat.title;
  link.addEventListener("click", () => openChat(chat.id));

  const dots = make("button", "history-dots");
  dots.type = "button";
  dots.title = tr("options");
  dots.setAttribute("aria-label", tr("chat_options"));
  dots.innerHTML = ICONS.dots;
  dots.addEventListener("click", (e) => {
    e.stopPropagation();
    if (chatMenu.classList.contains("show") && menuChatId === chat.id) closeChatMenu();
    else openChatMenu(chat, dots, item);
  });

  item.append(link, dots);
  return item;
}

async function openChat(id) {
  const chat = chats.find((c) => c.id === id);
  if (!chat) return;
  if (isGuest) {
    currentId = id;
    renderMessages(chat.messages);
  } else {
    try {
      const data = await api("/v1/chats/" + encodeURIComponent(id));
      currentId = id;
      renderMessages(data.messages.map(fromServer));
    } catch (err) {
      await loadChats();
      return;
    }
  }
  renderHistory();
  closeSidebar();
}

function startNewChat() {
  currentId = null;
  pending = [];
  renderAttachments();
  renderMessages([]);
  renderHistory();
  closeSidebar();
  updateSend();
  if (!el.input.disabled) el.input.focus();
}

// Used by Settings > Data > Delete all chats
function clearAllChats() {
  chats = [];
  currentId = null;
  renderMessages([]);
  renderHistory();
}

// ---------- 3-dot menu: Rename and Delete ----------

const chatMenu = make("div", "chat-menu");
document.body.appendChild(chatMenu);
let menuChatId = null;

function menuButton(icon, label, onClick, extraClass) {
  const button = make("button", "chat-menu-item" + (extraClass ? " " + extraClass : ""));
  button.type = "button";
  button.innerHTML = icon;
  button.appendChild(make("span", "", label));
  button.addEventListener("click", (e) => {
    e.stopPropagation();
    onClick();
  });
  return button;
}

function openChatMenu(chat, button, item) {
  closeChatMenu();
  menuChatId = chat.id;
  item.classList.add("menu-open");
  chatMenu.innerHTML = "";
  chatMenu.append(
    menuButton(ICONS.pencil, tr("rename"), () => {
      closeChatMenu();
      startRename(chat.id);
    }),
    menuButton(ICONS.trash, tr("delete"), () => {
      closeChatMenu();
      askConfirm(tr("delete_chat_title"), tr("delete_chat_text", { title: chat.title }), tr("delete"),
                 () => deleteChat(chat.id));
    }, "danger"),
  );
  chatMenu.classList.add("show");

  // Place the menu under the button or above it when there is no room below
  const r = button.getBoundingClientRect();
  const h = chatMenu.offsetHeight;
  const w = chatMenu.offsetWidth;
  const top = r.bottom + 4 + h > window.innerHeight ? r.top - h - 4 : r.bottom + 4;
  chatMenu.style.top = Math.max(8, top) + "px";
  chatMenu.style.left = Math.max(8, Math.min(r.left, window.innerWidth - w - 8)) + "px";
}

function closeChatMenu() {
  chatMenu.classList.remove("show");
  menuChatId = null;
  for (const item of el.history.querySelectorAll(".history-item.menu-open")) item.classList.remove("menu-open");
}

function startRename(id) {
  const chat = chats.find((c) => c.id === id);
  const item = [...el.history.querySelectorAll(".history-item")].find((n) => n.dataset.id === id);
  if (!chat || !item) return;

  // Swap the title for a text box. Enter saves, Escape cancels.
  const input = make("input", "rename-input");
  input.value = chat.title;
  input.maxLength = 80;
  item.querySelector(".history-link").replaceWith(input);
  item.querySelector(".history-dots").remove();
  input.focus();
  input.select();

  let finished = false;
  const finish = async (save) => {
    if (finished) return;
    finished = true;
    const title = input.value.trim();
    if (save && title && title !== chat.title) await renameChat(chat, title);
    renderHistory();
  };
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      finish(true);
    } else if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      finish(false);
    }
  });
  input.addEventListener("blur", () => finish(true));
}

async function renameChat(chat, title) {
  try {
    const data = await api("/v1/chats/" + encodeURIComponent(chat.id), jsonBody("PATCH", { title }));
    chat.title = data.title;
  } catch (err) {
    // keep the old name if the server refused
  }
}

async function deleteChat(id) {
  try {
    await api("/v1/chats/" + encodeURIComponent(id), { method: "DELETE" });
  } catch (err) {
    // already gone on the server: remove it from the list anyway
  }
  chats = chats.filter((c) => c.id !== id);
  if (currentId === id) {
    currentId = null;
    renderMessages([]);
  }
  renderHistory();
}

// ---------- Messages ----------

function fileCard(file, removable) {
  const card = make("div", "file-card " + (file.status || "done"));
  const ext = extensionOf(file.name).replace(".", "").toUpperCase() || "FILE";

  if (file.status === "uploading") {
    const icon = make("div", "file-icon");
    icon.appendChild(make("div", "spinner"));
    card.appendChild(icon);
  } else {
    card.appendChild(make("div", "file-icon", ext.slice(0, 4)));
  }

  const info = make("div", "file-info");
  info.appendChild(make("div", "file-name", file.name));
  let meta = file.size_label;
  if (file.status === "uploading") meta = tr("uploading");
  if (file.status === "error") meta = file.error;
  if (file.status === "done" && removable) meta = file.size_label + " - " + tr("ready");
  info.appendChild(make("div", "file-meta", meta));
  card.appendChild(info);

  if (removable) {
    const remove = make("button", "file-remove", "×");
    remove.type = "button";
    remove.title = tr("remove_file");
    remove.addEventListener("click", () => {
      pending = pending.filter((p) => p.id !== file.id);
      renderAttachments();
      updateSend();
    });
    card.appendChild(remove);
  }
  return card;
}

function messageNode(msg) {
  const row = make("div", "msg " + msg.role + (msg.mode === "error" ? " error" : ""));
  if (msg.role === "assistant") row.appendChild(make("div", "avatar", "M"));

  const body = make("div", "msg-body");
  if (msg.role === "assistant" && msg.mode === "demo") body.appendChild(make("span", "badge", tr("demo_mode")));
  if (msg.role === "assistant" && msg.mode === "error") body.appendChild(make("span", "badge error", tr("notice")));

  if (msg.attachments && msg.attachments.length) {
    const files = make("div", "msg-files");
    for (const a of msg.attachments) files.appendChild(fileCard({ ...a, status: "done" }, false));
    body.appendChild(files);
  }
  if (msg.html) {
    // A finished answer in Markdown. The server made this HTML from the answer with raw
    // HTML turned off, so it holds only formatting and safe links
    const text = make("div", "msg-text md");
    text.innerHTML = msg.html;
    body.appendChild(text);
  } else if (msg.text) {
    body.appendChild(make("div", "msg-text", msg.text));
  }

  row.appendChild(body);
  return row;
}

function typingNode() {
  const row = make("div", "msg assistant");
  row.appendChild(make("div", "avatar", "M"));
  const dots = make("div", "typing");
  dots.append(make("span"), make("span"), make("span"));
  row.appendChild(dots);
  return row;
}

function renderMessages(list) {
  el.messages.innerHTML = "";
  el.welcome.style.display = list.length ? "none" : "";
  for (const msg of list) el.messages.appendChild(messageNode(msg));
  scrollDown();
}

// ---------- Sending ----------

async function sendMessage() {
  if (isGuest && guestLeft <= 0) {
    showAuthModal("limit");
    return;
  }
  const text = el.input.value.trim();
  if (busy || !text) return;

  const userMsg = { role: "user", text, attachments: [] };

  // Clear the message box and show the message straight away
  el.input.value = "";
  autoGrow();
  el.welcome.style.display = "none";
  el.messages.appendChild(messageNode(userMsg));
  const typing = typingNode();
  el.messages.appendChild(typing);
  scrollDown();

  busy = true;
  updateSend();

  // The answer grows piece by piece. The typing dots stay until the first piece arrives
  const reply = { role: "assistant", text: "", mode: null };
  let replyNode = null;
  let opened = null;
  const show = () => {
    const node = messageNode(reply);
    (replyNode || typing).replaceWith(node);
    replyNode = node;
    scrollDown();
  };
  try {
    await streamChat({ message: text, chat_id: currentId }, (name, data) => {
      if (name === "chat") {
        opened = data;
      } else if (name === "delta") {
        reply.text += data.text;
        show();
      } else if (name === "error") {
        reply.mode = "error";
        reply.text = (reply.text ? reply.text + "\n\n" : "") + errorText(data.kind);
        show();
      }
    });
  } catch (err) {
    reply.mode = "error";
    reply.text = err.message;
    if (isGuest && err.status === 403) guestLeft = 0;
  }
  if (!replyNode) show();

  if (opened) {
    // The server saved the question and the answer. Update the list so it moves to the top
    currentId = opened.chat_id;
    if (isGuest) guestLeft = Math.max(0, guestLeft - 1);
    let chat = chats.find((c) => c.id === opened.chat_id);
    if (!chat) {
      chat = { id: opened.chat_id, title: opened.title, messages: [] };
      chats.push(chat);
    }
    chat.updated_at = nowSeconds();
    if (isGuest) chat.messages.push(userMsg, reply);
    renderHistory();
    if (reply.mode !== "error") {
      // The saved answer, shown in Markdown the server made safe
      try {
        const data = await api("/v1/chats/" + encodeURIComponent(opened.chat_id));
        const last = data.messages[data.messages.length - 1];
        if (last && last.role === "assistant" && last.html) {
          reply.html = last.html;
          show();
        }
      } catch (err) {
        // the plain text stays
      }
    }
  }

  renderGuestBar();
  busy = false;
  updateSend();
  if (isGuest && guestLeft === 0) showAuthModal("limit");
}

function updateSend() {
  const hasText = el.input.value.trim().length > 0;
  const hasFiles = pending.some((f) => f.status === "done");
  const uploading = pending.some((f) => f.status === "uploading");
  const blocked = isGuest && guestLeft <= 0;
  el.sendBtn.disabled = busy || uploading || blocked || (!hasText && !hasFiles);
}

function autoGrow() {
  el.input.style.height = "auto";
  el.input.style.height = Math.min(el.input.scrollHeight, 200) + "px";
}

// ---------- File upload (logged-in users) ----------

function renderAttachments() {
  el.attachments.innerHTML = "";
  for (const file of pending) el.attachments.appendChild(fileCard(file, true));
}

function addFiles(fileList) {
  if (isGuest) {
    showAuthModal("upload");
    return;
  }
  // Reading files comes in a later version. Until then the paperclip and a dropped file
  // show this note
  showToast(tr("files_coming"));
}

// ---------- Sidebar on small screens ----------

function closeSidebar() {
  el.sidebar.classList.remove("open");
  el.backdrop.classList.remove("show");
}

el.menuBtn.addEventListener("click", () => {
  el.sidebar.classList.add("open");
  el.backdrop.classList.add("show");
});
el.backdrop.addEventListener("click", closeSidebar);

// ---------- Hide and show the sidebar (wide screens) ----------
// Logged in: saved in the account settings. Guests: saved in a cookie of this browser, so the
// server draws the page with the sidebar already hidden.

const sidebarToggle = document.getElementById("sidebarToggle");

function sidebarCollapsed() {
  return document.documentElement.classList.contains("sb-collapsed");
}

function updateToggleLabel() {
  const label = tr(sidebarCollapsed() ? "show_sidebar" : "hide_sidebar");
  sidebarToggle.title = label + " (" + config.mod + " B)";
  sidebarToggle.setAttribute("aria-label", label);
  sidebarToggle.setAttribute("aria-expanded", String(!sidebarCollapsed()));
}

function toggleSidebar() {
  const collapsed = !sidebarCollapsed();
  document.documentElement.classList.toggle("sb-collapsed", collapsed);
  closeChatMenu();
  document.dispatchEvent(new CustomEvent("close-menus"));
  updateToggleLabel();
  if (isGuest) {
    document.cookie = "sidebar=" + (collapsed ? "collapsed" : "open") + "; path=/; max-age=31536000; samesite=strict";
  } else {
    prefs.sidebar_collapsed = collapsed;
    // Saved quietly. If saving fails, the sidebar still works for this visit.
    api("/v1/me/preferences", jsonBody("PATCH", { sidebar_collapsed: collapsed })).catch(() => {});
  }
}

sidebarToggle.addEventListener("click", toggleSidebar);
updateToggleLabel();

// ---------- Events ----------

el.composer.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage();
});

el.input.addEventListener("keydown", (e) => {
  if (e.key !== "Enter" || e.isComposing) return;
  // Cmd/Ctrl + Enter always sends. Plain Enter sends only when that setting is on.
  if (e.metaKey || e.ctrlKey || (prefs.enter_sends && !e.shiftKey)) {
    e.preventDefault();
    sendMessage();
  }
});

el.input.addEventListener("input", () => {
  autoGrow();
  updateSend();
});

el.newChat.addEventListener("click", startNewChat);

el.attachBtn.addEventListener("click", () => {
  if (isGuest) showAuthModal("upload");
  else el.fileInput.click();
});
el.fileInput.addEventListener("change", () => {
  addFiles(el.fileInput.files);
  el.fileInput.value = "";   // lets the same file be chosen again
});

for (const button of document.querySelectorAll(".example")) {
  button.addEventListener("click", () => {
    if (el.input.disabled) {
      showAuthModal("limit");
      return;
    }
    el.input.value = button.dataset.prompt;
    autoGrow();
    updateSend();
    el.input.focus();
  });
}

// A click anywhere else closes the 3-dot menu
document.addEventListener("click", (e) => {
  if (!chatMenu.contains(e.target)) closeChatMenu();
});
el.history.addEventListener("scroll", closeChatMenu);
window.addEventListener("resize", closeChatMenu);

// Keyboard shortcuts that work for everyone. account.js adds Cmd/Ctrl + /.
document.addEventListener("keydown", (e) => {
  const mod = e.metaKey || e.ctrlKey;
  if (mod && e.shiftKey && e.key.toLowerCase() === "o") {
    e.preventDefault();
    startNewChat();
  } else if (mod && !e.shiftKey && !e.altKey && e.key.toLowerCase() === "b") {
    // Small screens use the menu button instead
    if (window.innerWidth > 820) {
      e.preventDefault();
      toggleSidebar();
    }
  } else if (e.shiftKey && e.key === "Escape") {
    e.preventDefault();
    if (!el.input.disabled) el.input.focus();
  } else if (e.key === "Escape") {
    // Close the top window first, then menus
    const open = openOverlays();
    if (open.length) closeOverlay(open[open.length - 1]);
    closeChatMenu();
    document.dispatchEvent(new CustomEvent("close-menus"));
  }
});

// Drag and drop anywhere on the page
let dragDepth = 0;
const hasFiles = (e) => e.dataTransfer && Array.from(e.dataTransfer.types).includes("Files");

window.addEventListener("dragenter", (e) => {
  if (!hasFiles(e)) return;
  e.preventDefault();
  if (isGuest) return;
  dragDepth++;
  el.dropOverlay.classList.add("show");
});
window.addEventListener("dragover", (e) => {
  if (hasFiles(e)) e.preventDefault();
});
window.addEventListener("dragleave", (e) => {
  if (!hasFiles(e) || isGuest) return;
  dragDepth = Math.max(0, dragDepth - 1);
  if (dragDepth === 0) el.dropOverlay.classList.remove("show");
});
window.addEventListener("drop", (e) => {
  if (!hasFiles(e)) return;
  e.preventDefault();
  dragDepth = 0;
  el.dropOverlay.classList.remove("show");
  addFiles(e.dataTransfer.files);
});

// ---------- Start ----------

renderGuestBar();
renderMessages([]);
loadChats();
if (!el.input.disabled) el.input.focus();
