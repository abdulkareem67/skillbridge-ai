const API = "";

const _escapeEl = document.createElement("div");
function escapeHtml(str) {
  _escapeEl.textContent = str == null ? "" : String(str);
  return _escapeEl.innerHTML;
}

const API_TIMEOUT_MS = 20000;

// Client-side translation. The page injects window.__I18N__ (the "js" namespace
// of the active locale, see i18n.js_bundle); this looks a key up there and falls
// back to the English text passed as the second argument, so a missing key is
// never a blank string.
function t(key, fallback) {
  const table = window.__I18N__ || {};
  return (Object.prototype.hasOwnProperty.call(table, key) && table[key]) || fallback || key;
}

// FastAPI reports validation failures as a list of {loc, msg}. Turn that into
// one readable sentence instead of showing "[object Object]".
function describeError(detail, fallback) {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (d && d.msg ? d.msg.replace(/^Value error, /, "") : "")).filter(Boolean).join(" ") || fallback;
  }
  return fallback;
}

async function api(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), options.timeout || API_TIMEOUT_MS);
  let res;
  try {
    res = await fetch(API + path, {
      credentials: "include",
      headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
      signal: controller.signal,
      ...options,
    });
  } catch (e) {
    const err = new Error(
      e.name === "AbortError"
        ? t("err_timeout", "That took too long to respond. Check your connection and try again.")
        : t("err_network", "Couldn't reach the server. Check your connection and try again.")
    );
    err.network = true;
    throw err;
  } finally {
    clearTimeout(timer);
  }

  if (!res.ok) {
    let detail = null;
    try { detail = (await res.json()).detail; } catch (e) {}
    const err = new Error(describeError(detail, res.status >= 500 ? t("err_server", "Something went wrong on our side. Please try again.") : t("err_generic", "Something went wrong.")));
    err.status = res.status;
    err.detail = detail;
    // An expired session on a normal page means "sign in again". But the auth
    // endpoints answer 401 for a *wrong password* — redirecting there reloaded
    // the login page and threw away the very error the user needed to see.
    if (res.status === 401 && !path.startsWith("/api/auth/")) {
      window.location.href = "/login?next=" + encodeURIComponent(location.pathname);
    }
    throw err;
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res;
}

/* ---------------------------------------------------------------------------
   Loading, empty and error states.

   Every async region renders one of three things while it isn't showing data,
   so no page ever sits blank or silently shows zeros after a failure. They are
   live regions, so a screen reader hears "Loading…" and then the outcome.
   ------------------------------------------------------------------------- */
function _stateBox(kind, message, extra = "") {
  const iconName = { loading: null, empty: "compass", error: "alert-triangle" }[kind];
  const lead = kind === "loading" ? '<span class="spinner" aria-hidden="true"></span>' : icon(iconName, 20);
  return `<div class="state-box state-${kind}" role="${kind === "error" ? "alert" : "status"}">${lead}<div class="state-text"><p>${escapeHtml(message)}</p>${extra}</div></div>`;
}

function showLoading(el, message = t("loading", "Loading…")) {
  if (!el) return;
  el.setAttribute("aria-busy", "true");
  el.innerHTML = _stateBox("loading", message);
}

// `action` is optional trusted HTML (a link or button we wrote ourselves).
function showEmpty(el, message, action = "") {
  if (!el) return;
  el.removeAttribute("aria-busy");
  el.innerHTML = _stateBox("empty", message, action ? `<div class="state-actions">${action}</div>` : "");
}

function showError(el, message, onRetry) {
  if (!el) return;
  el.removeAttribute("aria-busy");
  el.innerHTML = _stateBox("error", message, onRetry ? `<div class="state-actions"><button type="button" class="btn btn-sm" data-retry>${escapeHtml(t("try_again", "Try again"))}</button></div>` : "");
  if (onRetry) el.querySelector("[data-retry]").addEventListener("click", onRetry);
}

function clearState(el) {
  if (el) el.removeAttribute("aria-busy");
}

// Disable a button for the length of an async action so it can't be double-
// submitted, show that it is working, and always restore it afterwards.
async function withBusy(button, fn, busyLabel) {
  if (!button) return fn();
  if (button.getAttribute("aria-busy") === "true") return;
  const original = button.innerHTML;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  button.innerHTML = `<span class="spinner spinner-sm" aria-hidden="true"></span>${escapeHtml(busyLabel || button.textContent.trim())}`;
  try {
    return await fn();
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
    button.innerHTML = original;
  }
}

/* ---------------------------------------------------------------------------
   Forms: inline field errors and password visibility.
   ------------------------------------------------------------------------- */
function setFieldError(input, message) {
  if (!input) return;
  const id = input.id + "-error";
  let el = document.getElementById(id);
  if (!message) {
    input.removeAttribute("aria-invalid");
    if (el) el.remove();
    return;
  }
  if (!el) {
    el = document.createElement("p");
    el.id = id;
    el.className = "field-error";
    // A password input shares a wrapper with its show/hide button; put the
    // message after the wrapper, not wedged between the field and its button.
    (input.closest(".password-field") || input).insertAdjacentElement("afterend", el);
  }
  el.textContent = message;
  input.setAttribute("aria-invalid", "true");
  const described = (input.getAttribute("aria-describedby") || "").split(" ").filter(Boolean);
  if (!described.includes(id)) input.setAttribute("aria-describedby", [...described, id].join(" "));
}

function initPasswordToggles() {
  document.querySelectorAll("[data-password-toggle]").forEach((btn) => {
    const input = document.getElementById(btn.getAttribute("aria-controls"));
    if (!input) return;
    btn.addEventListener("click", () => {
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.setAttribute("aria-pressed", String(show));
      btn.setAttribute("aria-label", show ? t("hide_password", "Hide password") : t("show_password", "Show password"));
      btn.innerHTML = icon(show ? "eye-off" : "eye", 18);
      input.focus();
    });
  });
}

// Messages for the ?error= codes the Google sign-in flow redirects back with.
const AUTH_ERRORS = {
  google_unavailable: t("google_unavailable", "Google sign-in isn't set up on this site yet. Use your email and password instead."),
  google_cancelled: t("google_cancelled", "Google sign-in was cancelled."),
  google_state: t("google_state", "That sign-in link had expired. Please try again."),
  google_failed: t("google_failed", "We couldn't finish signing you in with Google. Please try again."),
};

function showAuthErrorFromUrl(el) {
  const code = new URLSearchParams(location.search).get("error");
  if (el && code && AUTH_ERRORS[code]) {
    el.textContent = AUTH_ERRORS[code];
    el.hidden = false;
  }
}

let _toastContainer = null;
function getToastContainer() {
  if (!_toastContainer || !document.body.contains(_toastContainer)) {
    _toastContainer = document.getElementById("toast-container");
    if (!_toastContainer) {
      _toastContainer = document.createElement("div");
      _toastContainer.id = "toast-container";
      _toastContainer.className = "toast-container";
      _toastContainer.setAttribute("aria-live", "polite");
      document.body.appendChild(_toastContainer);
    }
  }
  return _toastContainer;
}

function toast(message, type = "success") {
  const container = getToastContainer();
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  const iconName = type === "error" ? "alert-triangle" : type === "info" ? "compass" : "check-circle";
  el.innerHTML = `${icon(iconName, 18)}<span style="flex:1">${escapeHtml(message)}</span><button type="button" class="modal-close" style="padding:2px" aria-label="${escapeHtml(t("close", "Close"))}">×</button>`;
  
  const dismiss = () => {
    if (el.classList.contains("leaving")) return;
    el.classList.add("leaving");
    setTimeout(() => el.remove(), 260);
  };

  el.querySelector("button").addEventListener("click", dismiss);
  container.appendChild(el);
  setTimeout(dismiss, 3500);
}

async function copyToClipboard(text, successMsg) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    toast(successMsg || t("copied", "Copied to clipboard!"), "success");
    return true;
  } catch (err) {
    toast(t("copy_failed", "Failed to copy text"), "error");
    return false;
  }
}

let _activeModal = null;
function openModal({ title, bodyHtml, footerHtml = "" }) {
  closeModal();
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.setAttribute("role", "dialog");
  backdrop.setAttribute("aria-modal", "true");
  backdrop.setAttribute("aria-labelledby", "modal-title");

  backdrop.innerHTML = `
    <div class="modal-dialog">
      <div class="modal-header">
        <h3 id="modal-title">${escapeHtml(title)}</h3>
        <button type="button" class="modal-close" id="modal-close-btn" aria-label="${escapeHtml(t("close", "Close"))}">×</button>
      </div>
      <div class="modal-body">${bodyHtml}</div>
      ${footerHtml ? `<div class="modal-footer">${footerHtml}</div>` : ""}
    </div>
  `;

  const close = () => {
    backdrop.classList.remove("is-open");
    setTimeout(() => backdrop.remove(), 200);
    document.removeEventListener("keydown", onKey);
    _activeModal = null;
  };

  const onKey = (e) => {
    if (e.key === "Escape") close();
  };

  backdrop.querySelector("#modal-close-btn").addEventListener("click", close);
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) close();
  });
  document.addEventListener("keydown", onKey);

  document.body.appendChild(backdrop);
  requestAnimationFrame(() => backdrop.classList.add("is-open"));
  _activeModal = { close, element: backdrop };
  return { close, element: backdrop };
}

function closeModal() {
  if (_activeModal) _activeModal.close();
}

// Mirrors the Jinja `icon()` macro so markup built in JS pulls from the same
// sprite as markup built server-side, instead of drifting back to emoji.
function icon(name, size = 16) {
  return `<svg class="icon" width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><use href="#i-${name}"></use></svg>`;
}

// The button holds both a sun and a moon icon; CSS shows whichever one offers
// the theme you'd switch *to*. Setting textContent here would delete them both.
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  // Charts paint with colours read at draw time, so they must redraw when the
  // theme changes or they keep the old theme's (possibly unreadable) colours.
  document.dispatchEvent(new CustomEvent("sb:themechange", { detail: { theme } }));
  const toggle = document.getElementById("theme-toggle");
  if (!toggle) return;
  const label = theme === "dark"
    ? t("theme_to_light", "Switch to light theme")
    : t("theme_to_dark", "Switch to dark theme");
  toggle.setAttribute("aria-label", label);
  toggle.setAttribute("title", label);
}

// Chart colours taken from the active theme's CSS variables. They used to be
// hard-coded for the dark theme, which put axis labels at 2.1:1 on the light
// background. The *-text variants clear WCAG AA as text (4.5:1) and as chart
// marks (3:1) in both themes.
function chartTheme() {
  const css = getComputedStyle(document.documentElement);
  const v = (name) => css.getPropertyValue(name).trim();
  const light = document.documentElement.getAttribute("data-theme") === "light";
  return {
    text: v("--text-muted"),
    grid: light ? "rgba(22, 26, 46, 0.10)" : "rgba(238, 240, 251, 0.08)",
    track: light ? "rgba(22, 26, 46, 0.18)" : "rgba(238, 240, 251, 0.16)",
    accent: v("--accent-text"),
    accent2: v("--accent-2-text"),
    success: v("--success-text"),
    danger: v("--danger-text"),
  };
}

function initTheme() {
  applyTheme(localStorage.getItem("sb-theme") || "dark");
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  localStorage.setItem("sb-theme", next);
  applyTheme(next);
}

function initNav() {
  const burger = document.getElementById("hamburger");
  const links = document.getElementById("nav-links");
  if (burger && links) burger.addEventListener("click", () => links.classList.toggle("open"));

  const path = window.location.pathname;
  document.querySelectorAll(".nav-links a").forEach((a) => {
    if (a.getAttribute("href") === path) a.classList.add("active");
  });

  const toggle = document.getElementById("theme-toggle");
  if (toggle) toggle.addEventListener("click", toggleTheme);
}

async function logout() {
  try { await api("/api/auth/logout", { method: "POST" }); } catch (e) {}
  try { sessionStorage.removeItem("sb-tab-account"); } catch (e) {}
  window.location.href = "/";
}

// Call right after this tab causes an account change (login, register, or
// picking an account from the switcher) so this tab's claim is never left to
// a stale value that a focus-triggered reclaim could fight against.
function claimAccountInThisTab(userId) {
  try { sessionStorage.setItem("sb-tab-account", String(userId)); } catch (e) {}
}

function switchAccount(userId) {
  claimAccountInThisTab(userId);
  window.location.href = "/api/auth/switch-account/" + encodeURIComponent(userId);
}

function initAccountSwitcher() {
  const btn = document.getElementById("account-switcher-btn");
  const menu = document.getElementById("account-switcher-menu");
  if (!btn || !menu) return;
  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    menu.hidden = !menu.hidden;
  });
  menu.addEventListener("click", (e) => e.stopPropagation());
  document.addEventListener("click", () => { menu.hidden = true; });
}

// Each browser tab "claims" whichever account was active when it first loaded.
// If another tab switches the shared active-account cookie, this tab notices
// on its next load/focus and switches it back before rendering stays wrong.
function initAccountReclaim() {
  const current = window.__SB_ACTIVE_UID__;
  if (current === undefined) return;
  const key = "sb-tab-account";
  const claimed = sessionStorage.getItem(key);
  if (claimed === null) {
    if (current !== null) sessionStorage.setItem(key, String(current));
    return;
  }
  if (current !== null && claimed !== String(current)) {
    fetch("/api/auth/switch-account/" + encodeURIComponent(claimed), { credentials: "include" })
      .then(() => window.location.reload())
      .catch(() => {});
  }
}

async function loadUserBadge() {
  const badge = document.getElementById("user-badge");
  if (!badge) return;
  try {
    const me = await api("/api/profile/me");
    badge.textContent = me.name.split(" ")[0];
  } catch (e) {
    badge.textContent = "";
  }
}

// A redirect-based sign-in (Google) lands with ?signed_in=<id>. Claim that
// account for this tab *before* the reclaim check runs, or the tab would switch
// straight back to whichever account it held before and undo the sign-in.
function claimFromUrl() {
  const params = new URLSearchParams(location.search);
  const uid = params.get("signed_in");
  if (!uid) return;
  if (String(window.__SB_ACTIVE_UID__) === uid) claimAccountInThisTab(uid);
  params.delete("signed_in");
  const query = params.toString();
  history.replaceState(null, "", location.pathname + (query ? "?" + query : "") + location.hash);
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initNav();
  initAccountSwitcher();
  claimFromUrl();
  initAccountReclaim();
  initPasswordToggles();
  loadUserBadge();
});

window.addEventListener("focus", initAccountReclaim);
