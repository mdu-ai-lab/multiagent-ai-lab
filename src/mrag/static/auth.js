// Login, sign-up and logout. Each form goes to the API with the token of this browser's
// session (header X-CSRF-Token). The texts come from the page settings block, so the server
// and this script use the same translations. Text is always shown with textContent, never
// as HTML
"use strict";

const config = JSON.parse(document.getElementById("page-config").textContent);
const t = config.t;

function errorText(code) {
  return t["err_" + code] || t.err_unknown;
}

// Sends JSON to the API. Returns null when it worked, otherwise an error code
async function post(path, body) {
  let response;
  try {
    response = await fetch(path, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": config.csrf },
      body: JSON.stringify(body),
    });
  } catch {
    return "network";
  }
  if (response.ok) return null;
  if (response.status === 422) return "invalid_input";
  try {
    const data = await response.json();
    if (typeof data.detail === "string") return data.detail;
  } catch {
    // Not JSON: the general error below
  }
  return "unknown";
}

function showError(code) {
  const box = document.querySelector(".alert");
  box.textContent = errorText(code);
  box.hidden = false;
}

// Sends a form once at a time and goes to the chat page when it worked
function handle(form, path, body) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button[type=submit]");
    const data = new FormData(form);
    const problem = body.check ? body.check(data) : null;
    if (problem) {
      showError(problem);
      return;
    }
    button.disabled = true;
    const code = await post(path, body.fields(data));
    if (code === null) {
      window.location.assign("/");
      return;
    }
    showError(code);
    button.disabled = false;
  });
}

// Show or hide a password
for (const button of document.querySelectorAll(".toggle-pw")) {
  button.addEventListener("click", () => {
    const input = button.parentElement.querySelector("input");
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    button.textContent = show ? t.hide : t.show;
  });
}

const loginForm = document.getElementById("login-form");
if (loginForm) {
  handle(loginForm, "/v1/auth/login", {
    fields: (data) => ({
      email: data.get("email"),
      password: data.get("password"),
      remember: data.get("remember") === "on",
    }),
  });
}

const signupForm = document.getElementById("signup-form");
if (signupForm) {
  handle(signupForm, "/v1/auth/signup", {
    check: (data) => (data.get("password") === data.get("confirm") ? null : "password_match"),
    fields: (data) => ({
      name: data.get("name"),
      email: data.get("email"),
      password: data.get("password"),
    }),
  });
}

for (const button of document.querySelectorAll("[data-logout]")) {
  button.addEventListener("click", async () => {
    button.disabled = true;
    await post("/v1/auth/logout", {});
    window.location.assign("/login");
  });
}
