let allOpportunities = [];
let currentFilter = "All";
let searchQuery = "";
let includeOtherFields = false;

const SAVED_KEY = "sb_saved_opportunities";

function getSavedIds() {
  try {
    return JSON.parse(localStorage.getItem(SAVED_KEY) || "[]");
  } catch (e) {
    return [];
  }
}

function saveSavedIds(ids) {
  try {
    localStorage.setItem(SAVED_KEY, JSON.stringify(ids));
  } catch (e) {}
}

function updateSavedCount() {
  const badge = document.getElementById("saved-count");
  if (badge) badge.textContent = getSavedIds().length;
}

function toggleBookmark(id, e) {
  if (e) e.stopPropagation();
  let ids = getSavedIds();
  const index = ids.indexOf(id);
  const isSaving = index === -1;
  if (isSaving) {
    ids.push(id);
    toast(t("opp_saved", "Opportunity saved to your bookmarks"), "success");
  } else {
    ids.splice(index, 1);
    toast(t("opp_unsaved", "Removed from bookmarks"), "info");
  }
  saveSavedIds(ids);
  updateSavedCount();
  render();
}

const FILTER_LABELS = () => ({
  Job: t("opp_word_jobs", "jobs"),
  Internship: t("opp_word_internships", "internships"),
  Freelance: t("opp_word_freelance", "freelance roles"),
  Remote: t("opp_word_remote", "remote roles"),
  Saved: t("opp_word_saved", "saved opportunities"),
});

function badgeColor(pct) {
  if (pct >= 70) return "var(--success-text)";
  if (pct >= 40) return "var(--warning-text)";
  return "var(--danger-text)";
}

function getInitials(str) {
  if (!str) return "SB";
  const parts = str.trim().split(/\s+/);
  return (parts[0][0] + (parts.length > 1 ? parts[1][0] : "")).toUpperCase();
}

function render() {
  const container = document.getElementById("opp-list");
  clearState(container);

  const savedIds = getSavedIds();
  updateSavedCount();

  let list = allOpportunities;

  // Filter by Type / Saved
  if (currentFilter === "Saved") {
    list = list.filter((o) => savedIds.includes(o.title + "::" + o.company));
  } else if (currentFilter !== "All") {
    list = list.filter((o) => o.type === currentFilter);
  }

  // Filter by Search Query
  if (searchQuery.trim()) {
    const q = searchQuery.toLowerCase().trim();
    list = list.filter((o) =>
      o.title.toLowerCase().includes(q) ||
      o.company.toLowerCase().includes(q) ||
      (o.location && o.location.toLowerCase().includes(q)) ||
      (o.field && o.field.toLowerCase().includes(q)) ||
      (o.skills && o.skills.some((s) => s.toLowerCase().includes(q)))
    );
  }

  if (!list.length) {
    container.classList.remove("grid", "grid-3");
    const what = FILTER_LABELS()[currentFilter] || t("opp_word_roles", "roles");
    showEmpty(
      container,
      searchQuery.trim()
        ? `No ${what} matched "${searchQuery}". Try a different keyword or clear your search.`
        : allOpportunities.length
        ? t("opp_none_filter", "No {what} match your skills yet. Try another filter, or add more skills to widen your matches.").replace("{what}", what)
        : t("opp_none", "No roles match your skills yet. Add more skills to unlock matches."),
      searchQuery.trim()
        ? `<button type="button" class="btn btn-sm" onclick="clearSearch()">Clear search</button>`
        : `<a class="btn btn-sm" href="/cv-upload">${escapeHtml(t("opp_add_skills", "Add skills"))}</a>`
    );
    return;
  }

  container.classList.add("grid", "grid-3");
  container.innerHTML = list.map((o, idx) => {
    const oppId = o.title + "::" + o.company;
    const isSaved = savedIds.includes(oppId);
    const pct = Number(o.match_percent);
    const color = badgeColor(pct);

    return `
    <div class="glass opp-card">
      <div class="opp-card-top">
        <div style="display:flex; align-items:center; gap:12px; flex:1; min-width:0">
          <div class="opp-avatar">${escapeHtml(getInitials(o.company))}</div>
          <div style="min-width:0">
            <h3 style="margin:0 0 2px; font-size:1.05rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis" title="${escapeHtml(o.title)}">${escapeHtml(o.title)}</h3>
            <p style="margin:0; font-size:0.85rem; color:var(--text-muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis">${escapeHtml(o.company)}</p>
          </div>
        </div>
        <button type="button" class="opp-bookmark-btn ${isSaved ? "is-saved" : ""}" 
                onclick="toggleBookmark('${escapeHtml(oppId)}', event)"
                title="${isSaved ? "Remove from bookmarks" : "Save opportunity"}"
                aria-label="${isSaved ? "Remove bookmark" : "Save bookmark"}">
          ${icon(isSaved ? "bookmark-fill" : "bookmark", 16)}
        </button>
      </div>

      <div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:12px">
        <span class="opp-type">${escapeHtml(o.type)}</span>
        ${o.field ? `<span class="opp-type opp-field">${escapeHtml(o.field)}</span>` : ""}
        <span class="opp-type" style="background:rgba(255,255,255,0.06); color:var(--text-muted)">
          ${icon("map-pin", 12)} ${escapeHtml(o.location || "Pakistan")}
        </span>
      </div>

      <div style="margin-bottom:14px">
        <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.85rem; margin-bottom:6px">
          <span style="color:var(--text-muted)">Skill Match</span>
          <strong style="color:${color}">${pct}%</strong>
        </div>
        <div class="progress-track" role="img" aria-label="${escapeHtml(t("opp_match_aria", "{pct}% skill match").replace("{pct}", pct))}">
          <div class="progress-fill" style="width:${pct}%; background:${color}"></div>
        </div>
      </div>

      <div style="margin-bottom:16px; flex:1">
        <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:6px; font-weight:600">REQUIRED SKILLS</div>
        <div>
          ${o.skills.map((s) => {
            const matched = o.matched_skills && o.matched_skills.includes(s);
            return `<span class="chip ${matched ? "chip-matched" : ""}" style="font-size:0.75rem; margin:2px 4px 2px 0">${matched ? icon("check", 12) + " " : ""}${escapeHtml(s)}</span>`;
          }).join("")}
        </div>
      </div>

      <div class="opp-card-footer">
        <button type="button" class="btn btn-sm btn-ghost" onclick="showOppBreakdown(${allOpportunities.indexOf(o)})" style="padding:6px 10px">
          ${icon("target", 14)} Breakdown
        </button>
        ${renderApplyAction(o, idx)}
      </div>
    </div>
  `;
  }).join("");
}

function renderApplyAction(o, idx) {
  if (!o.apply_links || !o.apply_links.length) {
    return "";
  }
  if (o.apply_links.length === 1) {
    const l = o.apply_links[0];
    return `
      <a href="${escapeHtml(l.url)}" class="btn btn-sm btn-primary" target="_blank" rel="noopener" style="padding:6px 12px">
        ${icon("link", 14)} ${escapeHtml(l.label)}
      </a>
    `;
  }
  return `
    <div class="opp-dropdown">
      <button type="button" class="btn btn-sm btn-primary" onclick="toggleOppDropdown(${idx}, event)" aria-expanded="false" aria-haspopup="true" id="opp-btn-${idx}" style="padding:6px 12px">
        ${icon("link", 14)} ${escapeHtml(t("opp_find_jobs", "Find Jobs"))} (${o.apply_links.length}) ▾
      </button>
      <div class="opp-dropdown-menu" id="opp-menu-${idx}" hidden>
        <div class="opp-dropdown-header">${escapeHtml(t("opp_search_on", "Search live roles on:"))}</div>
        ${o.apply_links.map((l) => `
          <a href="${escapeHtml(l.url)}" class="opp-dropdown-item" target="_blank" rel="noopener" onclick="closeAllOppDropdowns()">
            <span>${escapeHtml(l.label.replace(/^Search on /i, ""))}</span>
            ${icon("arrow-right", 12)}
          </a>
        `).join("")}
      </div>
    </div>
  `;
}

function toggleOppDropdown(idx, e) {
  if (e) {
    e.stopPropagation();
    e.preventDefault();
  }
  const menu = document.getElementById(`opp-menu-${idx}`);
  const btn = document.getElementById(`opp-btn-${idx}`);
  if (!menu) return;
  const isHidden = menu.hidden;
  closeAllOppDropdowns();
  if (isHidden) {
    menu.hidden = false;
    if (btn) btn.setAttribute("aria-expanded", "true");
    const card = menu.closest(".opp-card");
    if (card) card.style.zIndex = "25";
  }
}

function closeAllOppDropdowns() {
  document.querySelectorAll(".opp-dropdown-menu").forEach((m) => {
    m.hidden = true;
    const card = m.closest(".opp-card");
    if (card) card.style.zIndex = "";
  });
  document.querySelectorAll(".opp-dropdown button[aria-expanded='true']").forEach((b) => {
    b.setAttribute("aria-expanded", "false");
  });
}

document.addEventListener("click", (e) => {
  if (!e.target.closest(".opp-dropdown")) {
    closeAllOppDropdowns();
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeAllOppDropdowns();
  }
});

function showOppBreakdown(idx) {
  const o = allOpportunities[idx];
  if (!o) return;

  const pct = Number(o.match_percent);
  const color = badgeColor(pct);
  const matched = o.matched_skills || [];
  const missing = o.skills.filter((s) => !matched.includes(s));
  const applyLinks = o.apply_links || [];

  const bodyHtml = `
    <div style="margin-bottom:18px">
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px">
        <div>
          <h4 style="margin:0 0 4px; font-size:1.15rem">${escapeHtml(o.title)}</h4>
          <p style="margin:0; color:var(--text-muted)">${escapeHtml(o.company)} • ${escapeHtml(o.location || "Remote")}</p>
        </div>
        <div style="text-align:right">
          <div style="font-size:1.5rem; font-weight:800; color:${color}">${pct}%</div>
          <div style="font-size:0.75rem; color:var(--text-muted)">Skill Match</div>
        </div>
      </div>
      <div class="progress-track" style="margin-bottom:16px">
        <div class="progress-fill" style="width:${pct}%; background:${color}"></div>
      </div>
    </div>

    <div style="margin-bottom:16px">
      <h5 style="margin:0 0 8px; color:var(--success-text); display:flex; align-items:center; gap:6px">
        ${icon("check-circle", 16)} Skills You Have (${matched.length})
      </h5>
      <div>
        ${matched.length
          ? matched.map((s) => `<span class="chip chip-matched">${escapeHtml(s)}</span>`).join("")
          : `<p style="color:var(--text-muted); margin:0">No overlapping skills yet.</p>`}
      </div>
    </div>

    <div style="margin-bottom:20px">
      <h5 style="margin:0 0 8px; color:var(--warning-text); display:flex; align-items:center; gap:6px">
        ${icon("alert-triangle", 16)} Skills to Highlight or Learn (${missing.length})
      </h5>
      <div>
        ${missing.length
          ? missing.map((s) => `<span class="chip chip-missing">${escapeHtml(s)}</span>`).join("")
          : `<p style="color:var(--success-text); margin:0">You have all required skills for this position!</p>`}
      </div>
    </div>

    ${applyLinks.length ? `
    <div style="margin-bottom:20px">
      <h5 style="margin:0 0 8px; color:var(--text); display:flex; align-items:center; gap:6px">
        ${icon("briefcase", 16)} Search Live Openings (${applyLinks.length} job boards)
      </h5>
      <div style="display:flex; flex-wrap:wrap; gap:8px">
        ${applyLinks.map((l) => `
          <a href="${escapeHtml(l.url)}" class="btn btn-sm btn-ghost" style="border:1px solid var(--card-border); background:var(--card-bg-raised); padding:6px 12px" target="_blank" rel="noopener">
            ${icon("link", 14)} ${escapeHtml(l.label)}
          </a>
        `).join("")}
      </div>
    </div>
    ` : ""}

    <div style="padding:14px; background:var(--card-bg); border-radius:var(--radius-md); border:1px solid var(--card-border)">
      <strong style="display:block; margin-bottom:4px; font-size:0.88rem">${icon("sparkles", 14)} Application Tip</strong>
      <p style="margin:0; font-size:0.82rem; color:var(--text-muted); line-height:1.5">
        Tailor your CV to emphasize <strong>${matched.slice(0, 3).join(", ") || "relevant projects"}</strong> in your experience bullet points before submitting.
      </p>
    </div>
  `;

  const footerHtml = `
    <a href="/roadmap" class="btn btn-ghost btn-sm">${icon("map", 14)} View Learning Roadmap</a>
    ${applyLinks.length ? `<a href="${escapeHtml(applyLinks[0].url)}" class="btn btn-primary btn-sm" target="_blank" rel="noopener">${icon("link", 14)} Search on ${escapeHtml(applyLinks[0].label.replace(/^Search on /i, ""))}</a>` : ""}
  `;

  openModal({
    title: "Opportunity Skill Match Breakdown",
    bodyHtml,
    footerHtml,
  });
}

function filterType(type) {
  currentFilter = type;
  document.querySelectorAll("[data-type]").forEach((b) => {
    const on = b.dataset.type === type;
    b.classList.toggle("btn-primary", on);
    b.setAttribute("aria-pressed", String(on));
  });
  render();
}

function clearSearch() {
  const input = document.getElementById("opp-search");
  if (input) {
    input.value = "";
    searchQuery = "";
    const wrap = input.closest(".search-bar-wrap");
    if (wrap) wrap.classList.remove("has-value");
    render();
  }
}

function initSearch() {
  const input = document.getElementById("opp-search");
  const clearBtn = document.getElementById("opp-search-clear");
  if (!input) return;

  const wrap = input.closest(".search-bar-wrap");

  input.addEventListener("input", () => {
    searchQuery = input.value;
    if (wrap) wrap.classList.toggle("has-value", Boolean(input.value));
    render();
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", clearSearch);
  }
}

async function loadApplyGuide() {
  const list = document.getElementById("apply-guide-list");
  showLoading(list, t("opp_plan_loading", "Building your application plan…"));
  try {
    const guide = await api("/api/opportunities/application-guide");
    clearState(list);
    list.innerHTML = guide.steps.map((s) => `<li>${escapeHtml(s)}</li>`).join("");
  } catch (err) {
    showError(list, t("opp_plan_failed", "Couldn't load your application plan. {msg}").replace("{msg}", err.message), loadApplyGuide);
  }
}

async function loadOpportunities() {
  const container = document.getElementById("opp-list");
  container.classList.remove("grid", "grid-3");
  showLoading(container, t("opp_matching", "Matching roles to your skills…"));
  try {
    const res = await api(`/api/opportunities?include_other_fields=${includeOtherFields}`);
    allOpportunities = res.opportunities;
    render();
  } catch (err) {
    showError(container, t("opp_load_failed", "Couldn't load matching roles. {msg}").replace("{msg}", err.message), loadOpportunities);
  }
  loadApplyGuide();
}

function onIncludeOtherFieldsChange() {
  includeOtherFields = document.getElementById("include-other-fields").checked;
  loadOpportunities();
}

async function init() {
  initSearch();
  updateSavedCount();

  document.querySelectorAll("[data-type]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.type === "All")));
  const allBtn = document.querySelector('[data-type="All"]');
  if (allBtn) allBtn.classList.add("btn-primary");

  try {
    const me = await api("/api/profile/me");
    if (me.target_role) {
      document.getElementById("other-fields-toggle").style.display = "flex";
      const note = document.getElementById("field-note");
      note.textContent = t("opp_showing", "Showing roles matched to your target role ({role}) first — tick the box above to also see roles outside that field.").replace("{role}", me.target_role);
      note.style.display = "block";
    }
  } catch (e) { /* non-essential */ }

  await loadOpportunities();
}

init();
