const API = "";

const _escapeEl = document.createElement("div");
function escapeHtml(str) {
  _escapeEl.textContent = str == null ? "" : String(str);
  return _escapeEl.innerHTML;
}

async function api(path, options = {}) {
  const res = await fetch(API + path, {
    credentials: "include",
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = "Something went wrong";
    try { detail = (await res.json()).detail || detail; } catch (e) {}
    if (res.status === 401) { window.location.href = "/login"; }
    throw new Error(detail);
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res;
}

function toast(message, type = "success") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

function initTheme() {
  const saved = localStorage.getItem("sb-theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  const toggle = document.getElementById("theme-toggle");
  if (toggle) toggle.textContent = saved === "dark" ? "☀" : "☽";
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("sb-theme", next);
  const toggle = document.getElementById("theme-toggle");
  if (toggle) toggle.textContent = next === "dark" ? "☀" : "☽";
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

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initNav();
  initAccountSwitcher();
  initAccountReclaim();
  loadUserBadge();
});

window.addEventListener("focus", initAccountReclaim);
