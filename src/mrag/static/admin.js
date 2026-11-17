// Admin panel: dashboard, users, feedback, settings and activity log.
// The server checks admin rights on every request. This file only shows the data.
// Every change sends the token of this browser's session (header X-CSRF-Token) against forged
// requests from other sites.

const A = JSON.parse(document.getElementById("page-config").textContent);
const me = A.me;
const locale = A.lang === "sv" ? "sv-SE" : "en-GB";

let users = [];
let feedback = [];
let userFilter = "all";
let feedbackFilter = "open";
let createRole = "member";

// ---------- Small helpers ----------

function tr(key, values = {}) {
  const text = A.t[key] || key;
  return text.replace(/\{(\w+)\}/g, (m, k) => (k in values ? values[k] : m));
}

function make(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function $(id) {
  return document.getElementById(id);
}

// The text for an error code of the API (its "detail"), in the chosen language
function errorText(code, status) {
  if (status === 422) return tr("err_invalid_input");
  if (typeof code === "string" && A.t["err_" + code]) return tr("err_" + code);
  return tr("request_failed");
}

async function api(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  if (method !== "GET") {
    options = { ...options, headers: { ...(options.headers || {}), "X-CSRF-Token": A.csrf } };
  }
  let res;
  try {
    res = await fetch(path, options);
  } catch (e) {
    throw new Error(tr("err_network"));
  }
  let data = null;
  try {
    data = await res.json();
  } catch (e) {
    // no JSON body
  }
  if (!res.ok) throw new Error(errorText(data && data.detail, res.status));
  return data;
}

function jsonBody(method, body) {
  return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

// The server sends times as text with their time zone
function formatDate(value) {
  if (!value) return tr("never");
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(new Date(value));
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function initials(name) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]).join("").toUpperCase() || "U";
}

let toastTimer = null;
function showToast(text) {
  const toast = $("toast");
  toast.textContent = text;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

// ---------- Windows ----------

function openOverlay(overlay) {
  overlay.classList.add("show");
  const target = overlay.querySelector("input:not([type=hidden]), .btn-ghost, .btn-primary");
  if (target) setTimeout(() => target.focus(), 30);
}

function closeOverlay(overlay) {
  overlay.classList.remove("show");
}

for (const overlay of document.querySelectorAll(".modal-overlay")) {
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeOverlay(overlay);
  });
  for (const b of overlay.querySelectorAll("[data-close]")) b.addEventListener("click", () => closeOverlay(overlay));
}

function formError(container, message) {
  const box = container.querySelector(".form-error");
  box.textContent = message || "";
  box.hidden = !message;
}

// Confirm window. The action runs on Confirm; an error is shown inside the window.
let confirmAction = null;
function askConfirm(title, text, okLabel, danger, action) {
  const modal = $("confirmModal");
  $("confirmTitle").textContent = title;
  $("confirmText").textContent = text;
  const ok = $("confirmOk");
  ok.textContent = okLabel;
  ok.className = danger ? "btn-danger" : "btn-primary";
  formError(modal, null);
  confirmAction = action;
  openOverlay(modal);
}

$("confirmOk").addEventListener("click", async () => {
  const modal = $("confirmModal");
  if (!confirmAction) return;
  $("confirmOk").disabled = true;
  try {
    await confirmAction();
    closeOverlay(modal);
  } catch (err) {
    formError(modal, err.message);
  } finally {
    $("confirmOk").disabled = false;
  }
});
$("confirmCancel").addEventListener("click", () => closeOverlay($("confirmModal")));

// ---------- Sections ----------

const SECTION_TITLES = {
  dashboard: "admin_dashboard", users: "admin_users", feedback: "admin_feedback",
  settings: "admin_settings", log: "admin_log",
};
const LOADERS = { dashboard: loadDashboard, users: loadUsers, feedback: loadFeedback, settings: loadSettings, log: loadLog };

function showSection(name) {
  for (const b of document.querySelectorAll(".admin-tab")) b.classList.toggle("active", b.dataset.section === name);
  for (const s of document.querySelectorAll(".admin-section")) s.classList.toggle("active", s.dataset.section === name);
  $("sectionTitle").textContent = tr(SECTION_TITLES[name]);
  history.replaceState(null, "", "#" + name);
  LOADERS[name]();
}

for (const b of document.querySelectorAll(".admin-tab")) b.addEventListener("click", () => showSection(b.dataset.section));
for (const b of document.querySelectorAll("[data-goto]")) b.addEventListener("click", () => showSection(b.dataset.goto));

// ---------- Dashboard ----------

async function loadDashboard() {
  try {
    const [stats, userList, fbList] = await Promise.all([
      api("/v1/admin/stats"), api("/v1/admin/users"), api("/v1/admin/feedback"),
    ]);
    users = userList;
    feedback = fbList;
    const fmt = new Intl.NumberFormat(locale);
    $("stUsers").textContent = fmt.format(stats.users);
    $("stChats").textContent = fmt.format(stats.chats);
    $("stMessages").textContent = fmt.format(stats.messages);
    $("stFeedback").textContent = fmt.format(stats.open_feedback);
    $("stAdmins").textContent = fmt.format(stats.admins);
    $("stBlocked").textContent = fmt.format(stats.blocked);
    $("stNew").textContent = fmt.format(stats.new_users);
    $("stGuest").textContent = fmt.format(stats.guest_today);
    updateFeedbackBadge(stats.open_feedback);

    const dashUsers = $("dashUsers");
    dashUsers.replaceChildren();
    for (const u of users.slice(0, 5)) {
      const row = make("div", "mini-row");
      row.append(userCell(u), make("span", "mini-meta", formatDate(u.created_at)));
      dashUsers.appendChild(row);
    }
    if (!users.length) dashUsers.appendChild(make("div", "empty", tr("no_users")));

    const dashFeedback = $("dashFeedback");
    dashFeedback.replaceChildren();
    for (const f of feedback.slice(0, 3)) {
      const row = make("div", "mini-row mini-fb");
      const top = make("div", "mini-fb-top");
      top.append(kindTag(f.kind), make("span", "mini-meta", (f.name || tr("deleted_user")) + " - " + formatDate(f.created_at)));
      row.append(top, make("div", "mini-fb-text", f.message));
      dashFeedback.appendChild(row);
    }
    if (!feedback.length) dashFeedback.appendChild(make("div", "empty", tr("no_feedback")));
  } catch (err) {
    showToast(err.message);
  }
}

function updateFeedbackBadge(count) {
  const badge = $("feedbackBadge");
  badge.textContent = count;
  badge.hidden = !count;
}

// ---------- Users ----------

function userCell(u) {
  const cell = make("div", "user-cell");
  cell.appendChild(make("span", "account-avatar small", initials(u.name)));
  const who = make("div", "user-who");
  const nameLine = make("div", "user-name", u.name);
  if (u.id === me.id) nameLine.appendChild(make("span", "tag tag-you", tr("you")));
  who.append(nameLine, make("div", "user-email", u.email));
  cell.appendChild(who);
  return cell;
}

function kindTag(kind) {
  const labels = { problem: "fb_problem", idea: "fb_idea", other: "fb_other" };
  return make("span", "tag tag-" + kind, tr(labels[kind] || "fb_other"));
}

async function loadUsers() {
  try {
    users = await api("/v1/admin/users");
    renderUsers();
  } catch (err) {
    showToast(err.message);
  }
}

function renderUsers() {
  const q = $("userSearch").value.trim().toLowerCase();
  const list = users.filter((u) => {
    if (userFilter === "admins" && u.role !== "admin") return false;
    if (userFilter === "blocked" && !u.blocked) return false;
    return !q || u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q);
  });

  const body = $("usersBody");
  body.replaceChildren();
  for (const u of list) {
    const tr_ = make("tr");
    const td = (child, cls) => {
      const cell = make("td", cls);
      if (typeof child === "string") cell.textContent = child;
      else cell.appendChild(child);
      tr_.appendChild(cell);
    };
    td(userCell(u));
    td(make("span", "tag " + (u.role === "admin" ? "tag-admin" : "tag-member"), tr(u.role === "admin" ? "role_admin" : "role_member")));
    td(make("span", "tag " + (u.blocked ? "tag-blocked" : "tag-active"), tr(u.blocked ? "status_blocked" : "status_active")));
    td(String(u.chats), "num");
    td(formatDate(u.created_at), "muted");
    td(formatDate(u.last_login), "muted");

    const actions = make("td", "actions");
    if (u.id !== me.id) {
      const dots = make("button", "history-dots row-dots");
      dots.type = "button";
      dots.title = tr("options");
      dots.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><circle cx="5" cy="12" r="1.8"/><circle cx="12" cy="12" r="1.8"/><circle cx="19" cy="12" r="1.8"/></svg>';
      dots.addEventListener("click", (e) => {
        e.stopPropagation();
        openRowMenu(u, dots);
      });
      actions.appendChild(dots);
    }
    tr_.appendChild(actions);
    body.appendChild(tr_);
  }
  $("usersEmpty").hidden = list.length > 0;
}

$("userSearch").addEventListener("input", renderUsers);
for (const b of $("userFilter").querySelectorAll("button")) {
  b.addEventListener("click", () => {
    userFilter = b.dataset.filter;
    for (const x of $("userFilter").querySelectorAll("button")) x.classList.toggle("selected", x === b);
    renderUsers();
  });
}

// Row menu with the actions for one user
const rowMenu = make("div", "chat-menu");
document.body.appendChild(rowMenu);

function menuItem(label, onClick, danger) {
  const b = make("button", "chat-menu-item" + (danger ? " danger" : ""), label);
  b.type = "button";
  b.addEventListener("click", (e) => {
    e.stopPropagation();
    closeRowMenu();
    onClick();
  });
  return b;
}

function openRowMenu(u, button) {
  rowMenu.replaceChildren(
    u.role === "admin"
      ? menuItem(tr("make_member"), () => askConfirm(tr("confirm_member_title"), tr("confirm_member_text", { name: u.name }),
          tr("make_member"), false, () => updateUser(u, { role: "member" })))
      : menuItem(tr("make_admin"), () => askConfirm(tr("confirm_admin_title"), tr("confirm_admin_text", { name: u.name }),
          tr("make_admin"), false, () => updateUser(u, { role: "admin" }))),
    u.blocked
      ? menuItem(tr("unblock"), () => updateUser(u, { blocked: false }).catch((err) => showToast(err.message)))
      : menuItem(tr("block"), () => askConfirm(tr("confirm_block_title"), tr("confirm_block_text", { name: u.name }),
          tr("block"), true, () => updateUser(u, { blocked: true }))),
    menuItem(tr("reset_password"), () => askConfirm(tr("confirm_reset_title"), tr("confirm_reset_text", { name: u.name }),
      tr("reset_password"), true, () => resetPassword(u))),
    menuItem(tr("delete_user"), () => askConfirm(tr("confirm_delete_user_title"), tr("confirm_delete_user_text", { name: u.name }),
      tr("delete"), true, () => deleteUser(u)), true),
  );
  rowMenu.classList.add("show");
  const r = button.getBoundingClientRect();
  const h = rowMenu.offsetHeight;
  const w = rowMenu.offsetWidth;
  const top = r.bottom + 4 + h > window.innerHeight ? r.top - h - 4 : r.bottom + 4;
  rowMenu.style.top = Math.max(8, top) + "px";
  rowMenu.style.left = Math.max(8, r.right - w) + "px";
}

function closeRowMenu() {
  rowMenu.classList.remove("show");
}

document.addEventListener("click", (e) => {
  if (!rowMenu.contains(e.target)) closeRowMenu();
});
window.addEventListener("resize", closeRowMenu);
document.querySelector(".admin-content").addEventListener("scroll", closeRowMenu);

async function updateUser(u, change) {
  await api("/v1/admin/users/" + u.id, jsonBody("PATCH", change));
  showToast(tr("user_updated"));
  await loadUsers();
}

async function resetPassword(u) {
  const data = await api("/v1/admin/users/" + u.id + "/reset-password", { method: "POST" });
  closeOverlay($("confirmModal"));
  $("passwordText").textContent = tr("temp_password_text", { name: u.name });
  $("passwordValue").textContent = data.password;
  $("copyPassword").textContent = tr("copy");
  openOverlay($("passwordModal"));
}

$("copyPassword").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText($("passwordValue").textContent);
    $("copyPassword").textContent = tr("copied");
  } catch (err) {
    // Clipboard blocked: select the text so it can be copied by hand
    const range = document.createRange();
    range.selectNodeContents($("passwordValue"));
    getSelection().removeAllRanges();
    getSelection().addRange(range);
  }
});

async function deleteUser(u) {
  await api("/v1/admin/users/" + u.id, { method: "DELETE" });
  showToast(tr("user_deleted"));
  await loadUsers();
}

// Create user
$("createUserBtn").addEventListener("click", () => {
  const form = $("createUserForm");
  form.reset();
  formError(form, null);
  setCreateRole("member");
  openOverlay($("createUserModal"));
});

function setCreateRole(role) {
  createRole = role;
  for (const b of $("createRole").querySelectorAll("button")) b.classList.toggle("selected", b.dataset.role === role);
}
for (const b of $("createRole").querySelectorAll("button")) b.addEventListener("click", () => setCreateRole(b.dataset.role));

$("createUserForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = $("createUserForm");
  const f = form.elements;
  const button = form.querySelector("button[type=submit]");
  formError(form, null);
  button.disabled = true;
  try {
    await api("/v1/admin/users", jsonBody("POST", {
      name: f.name.value, email: f.email.value, password: f.password.value, role: createRole,
    }));
    closeOverlay($("createUserModal"));
    showToast(tr("user_created"));
    await loadUsers();
  } catch (err) {
    formError(form, err.message);
  } finally {
    button.disabled = false;
  }
});

// ---------- Feedback ----------

async function loadFeedback() {
  try {
    feedback = await api("/v1/admin/feedback");
    renderFeedback();
  } catch (err) {
    showToast(err.message);
  }
}

function renderFeedback() {
  const list = feedback.filter((f) => feedbackFilter === "all" || (feedbackFilter === "done" ? f.done : !f.done));
  const box = $("feedbackList");
  box.replaceChildren();
  for (const f of list) {
    const card = make("div", "card fb-card" + (f.done ? " fb-done" : ""));
    const head = make("div", "fb-head");
    const from = make("div", "fb-from");
    from.append(kindTag(f.kind), make("span", "fb-who", f.name ? f.name + " (" + f.email + ")" : tr("deleted_user")));
    head.append(from, make("span", "mini-meta", formatDateTime(f.created_at)));
    const action = make("button", f.done ? "btn-ghost" : "btn-primary", tr(f.done ? "reopen" : "mark_done"));
    action.type = "button";
    action.addEventListener("click", async () => {
      try {
        await api("/v1/admin/feedback/" + f.id, jsonBody("PATCH", { done: !f.done }));
        f.done = !f.done;
        renderFeedback();
        updateFeedbackBadge(feedback.filter((x) => !x.done).length);
      } catch (err) {
        showToast(err.message);
      }
    });
    const foot = make("div", "fb-foot");
    foot.appendChild(action);
    card.append(head, make("p", "fb-text", f.message), foot);
    box.appendChild(card);
  }
  $("feedbackEmpty").hidden = list.length > 0;
}

for (const b of $("feedbackFilter").querySelectorAll("button")) {
  b.addEventListener("click", () => {
    feedbackFilter = b.dataset.filter;
    for (const x of $("feedbackFilter").querySelectorAll("button")) x.classList.toggle("selected", x === b);
    renderFeedback();
  });
}

// ---------- Settings ----------

async function loadSettings() {
  try {
    const s = await api("/v1/admin/settings");
    $("guestMode").checked = s.guest_mode;
    $("guestLimit").value = s.guest_limit;
    $("signupOpen").checked = s.signup_open;
  } catch (err) {
    showToast(err.message);
  }
}

// Guest mode on or off (added for this project)
$("guestMode").addEventListener("change", async () => {
  try {
    await api("/v1/admin/settings", jsonBody("PATCH", { guest_mode: $("guestMode").checked }));
    showToast(tr("saved_prefs"));
  } catch (err) {
    $("guestMode").checked = !$("guestMode").checked;
    showToast(err.message);
  }
});

$("guestLimitForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const s = await api("/v1/admin/settings", jsonBody("PATCH", { guest_limit: Number($("guestLimit").value) }));
    $("guestLimit").value = s.guest_limit;
    showToast(tr("saved_prefs"));
  } catch (err) {
    showToast(err.message);
  }
});

$("signupOpen").addEventListener("change", async () => {
  try {
    await api("/v1/admin/settings", jsonBody("PATCH", { signup_open: $("signupOpen").checked }));
    showToast(tr("saved_prefs"));
  } catch (err) {
    $("signupOpen").checked = !$("signupOpen").checked;
    showToast(err.message);
  }
});

// ---------- Activity log ----------

async function loadLog() {
  try {
    const rows = await api("/v1/admin/log");
    const body = $("logBody");
    body.replaceChildren();
    for (const r of rows) {
      const row = make("tr");
      row.appendChild(make("td", "muted nowrap", formatDateTime(r.created_at)));
      row.appendChild(make("td", "", r.admin_label));
      const what = make("td");
      what.append(tr("act_" + r.action) + " ");
      if (r.target) what.appendChild(make("strong", "", r.target));
      if (r.details) what.appendChild(make("span", "log-details", r.details));
      row.appendChild(what);
      body.appendChild(row);
    }
    $("logEmpty").hidden = rows.length > 0;
  } catch (err) {
    showToast(err.message);
  }
}

// ---------- Keyboard ----------

document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  closeRowMenu();
  const open = [...document.querySelectorAll(".modal-overlay.show")];
  if (open.length) closeOverlay(open[open.length - 1]);
});

// ---------- Start ----------

const start = location.hash.slice(1);
showSection(LOADERS[start] ? start : "dashboard");
