// Account menu, settings, keyboard shortcuts, help, feedback and About.
// Loaded only for logged-in users, after app.js (it uses its helpers).

const acc = {
  root: document.getElementById("account"),
  button: document.getElementById("accountBtn"),
  menu: document.getElementById("accountMenu"),
  name: document.getElementById("accountName"),
  initials: document.getElementById("accountInitials"),
  themeValue: document.getElementById("themeValue"),
  welcomeTitle: document.getElementById("welcomeTitle"),
  examples: document.getElementById("examples"),
  settings: document.getElementById("settingsModal"),
  shortcuts: document.getElementById("shortcutsModal"),
  help: document.getElementById("helpModal"),
  feedback: document.getElementById("feedbackModal"),
  about: document.getElementById("aboutModal"),
  deleteAccount: document.getElementById("deleteAccountModal"),
  nameForm: document.getElementById("nameForm"),
  passwordForm: document.getElementById("passwordForm"),
  deleteAccountForm: document.getElementById("deleteAccountForm"),
  feedbackForm: document.getElementById("feedbackForm"),
  languageSelect: document.getElementById("languageSelect"),
  enterSends: document.getElementById("enterSendsToggle"),
  showExamples: document.getElementById("showExamplesToggle"),
};

// ---------- Account menu ----------

function openAccountMenu() {
  acc.root.classList.add("open");
  acc.button.setAttribute("aria-expanded", "true");
}

function closeAccountMenu() {
  acc.root.classList.remove("open");
  acc.button.setAttribute("aria-expanded", "false");
  for (const sub of acc.menu.querySelectorAll(".has-sub.open")) sub.classList.remove("open");
}

acc.button.addEventListener("click", (e) => {
  e.stopPropagation();
  if (acc.root.classList.contains("open")) closeAccountMenu();
  else openAccountMenu();
});

document.addEventListener("click", (e) => {
  if (!acc.root.contains(e.target)) closeAccountMenu();
});
document.addEventListener("close-menus", closeAccountMenu);

// Appearance and Language open a small menu on mouse-over or click
for (const item of acc.menu.querySelectorAll(".has-sub")) {
  const open = () => {
    for (const other of acc.menu.querySelectorAll(".has-sub.open")) if (other !== item) other.classList.remove("open");
    item.classList.add("open");
  };
  item.addEventListener("mouseenter", open);
  item.addEventListener("mouseleave", () => item.classList.remove("open"));
  item.addEventListener("click", (e) => {
    if (e.target.closest(".am-sub")) return;
    e.stopPropagation();
    item.classList.toggle("open");
  });
  item.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " " || e.key === "ArrowRight") {
      e.preventDefault();
      open();
      const first = item.querySelector(".am-sub .am-item");
      if (first) first.focus();
    }
  });
}

// Plain menu items open their window
const ACTIONS = {
  settings: () => openSettings("general"),
  shortcuts: () => openOverlay(acc.shortcuts),
  help: () => openOverlay(acc.help),
  feedback: () => openFeedback(),
  about: () => openOverlay(acc.about),
};

for (const button of document.querySelectorAll("[data-action]")) {
  button.addEventListener("click", () => {
    closeAccountMenu();
    // The help window has its own "Send feedback" button
    if (button.closest("#helpModal")) closeOverlay(acc.help);
    ACTIONS[button.dataset.action]();
  });
}

// Log out ends this browser's session on the server, then the page opens as a guest
for (const button of document.querySelectorAll("[data-logout]")) {
  button.addEventListener("click", async () => {
    try {
      await api("/v1/auth/logout", { method: "POST" });
    } catch (err) {
      // The session ends with its time limit anyway
    }
    window.location.href = "/";
  });
}

// ---------- Saving settings ----------

async function savePrefs(change, quiet) {
  const saved = await api("/v1/me/preferences", jsonBody("PATCH", change));
  Object.assign(prefs, saved);
  if (!quiet) showToast(tr("saved_prefs"));
  return saved;
}

// Theme: change the page at once, then save
async function setTheme(value) {
  document.documentElement.dataset.theme = value;
  for (const b of document.querySelectorAll("[data-set-theme]")) {
    b.classList.toggle("selected", b.dataset.setTheme === value);
  }
  acc.themeValue.textContent = tr(value);
  try {
    await savePrefs({ theme: value });
  } catch (err) {
    showToast(err.message);
  }
}

for (const button of document.querySelectorAll("[data-set-theme]")) {
  button.addEventListener("click", (e) => {
    e.stopPropagation();
    setTheme(button.dataset.setTheme);
  });
}

// Language: save, then reload so every text on the page changes
async function setLanguage(code) {
  if (code === prefs.language) {
    closeAccountMenu();
    return;
  }
  try {
    await savePrefs({ language: code }, true);
    window.location.reload();
  } catch (err) {
    showToast(err.message);
  }
}

for (const button of document.querySelectorAll("[data-set-lang]")) {
  button.addEventListener("click", (e) => {
    e.stopPropagation();
    setLanguage(button.dataset.setLang);
  });
}
acc.languageSelect.addEventListener("change", () => setLanguage(acc.languageSelect.value));

// ---------- Settings window ----------

function openSettings(tab) {
  showTab(tab);
  openOverlay(acc.settings);
}

function showTab(tab) {
  for (const b of acc.settings.querySelectorAll(".settings-tab")) b.classList.toggle("active", b.dataset.tab === tab);
  for (const p of acc.settings.querySelectorAll(".settings-panel")) p.classList.toggle("active", p.dataset.panel === tab);
  for (const err of acc.settings.querySelectorAll(".form-error")) err.hidden = true;
}

for (const button of acc.settings.querySelectorAll(".settings-tab")) {
  button.addEventListener("click", () => showTab(button.dataset.tab));
}

function formError(form, message) {
  const box = form.querySelector(".form-error");
  box.textContent = message || "";
  box.hidden = !message;
}

// Runs a form request with the button disabled and shows errors inside the form
async function submitForm(form, request) {
  const button = form.querySelector("button[type=submit]");
  formError(form, null);
  button.disabled = true;
  try {
    return await request();
  } catch (err) {
    formError(form, err.message);
    return null;
  } finally {
    button.disabled = false;
  }
}

acc.nameForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = acc.nameForm.elements.name.value.trim();
  const data = await submitForm(acc.nameForm, () => api("/v1/me", jsonBody("PATCH", { name })));
  if (!data) return;
  acc.name.textContent = data.name;
  acc.initials.textContent = data.initials;
  config.user.name = data.name;
  if (acc.welcomeTitle) acc.welcomeTitle.textContent = tr("welcome_user", { name: data.name.split(/\s+/)[0] });
  showToast(tr("saved_name"));
});

acc.passwordForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = acc.passwordForm.elements;
  const body = {
    current_password: f.current_password.value,
    new_password: f.new_password.value,
    confirm_password: f.confirm_password.value,
  };
  const data = await submitForm(acc.passwordForm, () => api("/v1/me/password", jsonBody("POST", body)));
  if (!data) return;
  acc.passwordForm.reset();
  showToast(tr("saved_password"));
});

// Chat preferences
acc.enterSends.addEventListener("change", async () => {
  try {
    await savePrefs({ enter_sends: acc.enterSends.checked });
    updateShortcutKeys();
  } catch (err) {
    acc.enterSends.checked = !acc.enterSends.checked;
    showToast(err.message);
  }
});

acc.showExamples.addEventListener("change", async () => {
  acc.examples.hidden = !acc.showExamples.checked;
  try {
    await savePrefs({ show_examples: acc.showExamples.checked });
  } catch (err) {
    acc.showExamples.checked = !acc.showExamples.checked;
    acc.examples.hidden = !acc.showExamples.checked;
    showToast(err.message);
  }
});

// Data
document.getElementById("exportBtn").addEventListener("click", () => {
  // The server sends the file as a download, so the page stays open
  window.location.href = "/v1/me/export";
  showToast(tr("export_started"));
});

document.getElementById("deleteAllBtn").addEventListener("click", () => {
  askConfirm(tr("delete_all_title"), tr("delete_all_text"), tr("delete_all"), async () => {
    try {
      await api("/v1/chats", { method: "DELETE" });
      clearAllChats();
      showToast(tr("chats_deleted"));
    } catch (err) {
      showToast(err.message);
    }
  });
});

// Delete account: needs the password, then goes back to the guest page
document.getElementById("deleteAccountBtn").addEventListener("click", () => {
  acc.deleteAccountForm.reset();
  formError(acc.deleteAccountForm, null);
  openOverlay(acc.deleteAccount);
});

acc.deleteAccountForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const password = acc.deleteAccountForm.elements.password.value;
  const data = await submitForm(acc.deleteAccountForm,
                                () => api("/v1/me/delete", jsonBody("POST", { password })));
  if (data) window.location.href = "/";
});

// ---------- Keyboard shortcuts window ----------

function keys(list) {
  const span = make("span", "keys");
  for (const k of list) span.appendChild(make("kbd", "", k));
  return span;
}

// The Send and New line rows follow the "Enter sends the message" setting
function updateShortcutKeys() {
  const send = document.getElementById("sendKeys");
  const newline = document.getElementById("newlineKeys");
  send.replaceChildren(...keys(prefs.enter_sends ? ["Enter"] : [config.mod, "Enter"]).childNodes);
  newline.replaceChildren(...keys(prefs.enter_sends ? ["Shift", "Enter"] : ["Enter"]).childNodes);
}
updateShortcutKeys();

document.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "/") {
    e.preventDefault();
    closeAccountMenu();
    openOverlay(acc.shortcuts);
  }
});

// ---------- Send feedback ----------

let feedbackKind = "problem";

function openFeedback() {
  acc.feedbackForm.reset();
  formError(acc.feedbackForm, null);
  setFeedbackKind("problem");
  openOverlay(acc.feedback);
}

function setFeedbackKind(kind) {
  feedbackKind = kind;
  for (const b of acc.feedbackForm.querySelectorAll("[data-kind]")) b.classList.toggle("selected", b.dataset.kind === kind);
}

for (const button of acc.feedbackForm.querySelectorAll("[data-kind]")) {
  button.addEventListener("click", () => setFeedbackKind(button.dataset.kind));
}

acc.feedbackForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = acc.feedbackForm.elements.message.value.trim();
  const data = await submitForm(acc.feedbackForm,
                                () => api("/v1/feedback", jsonBody("POST", { kind: feedbackKind, message })));
  if (!data) return;
  closeOverlay(acc.feedback);
  showToast(tr("feedback_sent"));
});
