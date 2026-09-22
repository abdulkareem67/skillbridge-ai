let allOpportunities = [];
let currentFilter = "All";
let includeOtherFields = false;

const FILTER_LABELS = { Job: "jobs", Internship: "internships", Freelance: "freelance roles", Remote: "remote roles" };

function badgeColor(pct) {
  if (pct >= 70) return "var(--success-text)";
  if (pct >= 40) return "var(--warning-text)";
  return "var(--danger-text)";
}

// Everything interpolated below is escaped. It is all our own example data
// today, but this list is meant to be replaced by a real jobs feed, and the
// day it is, unescaped titles would be a script-injection hole.
function render() {
  const list = currentFilter === "All" ? allOpportunities : allOpportunities.filter((o) => o.type === currentFilter);
  const container = document.getElementById("opp-list");
  clearState(container);

  if (!list.length) {
    container.classList.remove("grid", "grid-3");
    const what = currentFilter === "All" ? "roles" : FILTER_LABELS[currentFilter] || "roles";
    showEmpty(
      container,
      allOpportunities.length
        ? `No ${what} match your skills yet. Try another filter, or add more skills to widen your matches.`
        : "No roles match your skills yet. Add more skills to unlock matches.",
      '<a class="btn btn-sm" href="/cv-upload">Add skills</a>'
    );
    return;
  }

  container.classList.add("grid", "grid-3");
  container.innerHTML = list.map((o) => `
    <div class="glass opp-card">
      <span class="opp-type">${escapeHtml(o.type)}</span>
      ${o.field ? `<span class="opp-type opp-field">${escapeHtml(o.field)}</span>` : ""}
      <h3 style="margin:8px 0 4px">${escapeHtml(o.title)}</h3>
      <p style="margin:0 0 4px; color:var(--text-muted)">${escapeHtml(o.company)} • ${escapeHtml(o.location)}</p>
      <div style="display:flex; align-items:center; gap:10px; margin:12px 0">
        <div class="progress-track" style="flex:1" role="img" aria-label="${o.match_percent}% skill match">
          <div class="progress-fill" style="width:${Number(o.match_percent)}%; background:${badgeColor(o.match_percent)}"></div>
        </div>
        <strong style="color:${badgeColor(o.match_percent)}">${Number(o.match_percent)}%</strong>
      </div>
      <div>${o.skills.map((s) => `<span class="chip ${o.matched_skills.includes(s) ? "chip-matched" : ""}" style="font-size:0.75rem">${escapeHtml(s)}</span>`).join("")}</div>
      <div class="resource-links">${o.apply_links.map((l) => `<a href="${escapeHtml(l.url)}" target="_blank" rel="noopener">${icon("link")} ${escapeHtml(l.label)}</a>`).join("")}</div>
    </div>
  `).join("");
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

async function loadApplyGuide() {
  const list = document.getElementById("apply-guide-list");
  showLoading(list, "Building your application plan…");
  try {
    const guide = await api("/api/opportunities/application-guide");
    clearState(list);
    list.innerHTML = guide.steps.map((s) => `<li>${escapeHtml(s)}</li>`).join("");
  } catch (err) {
    showError(list, `Couldn't load your application plan. ${err.message}`, loadApplyGuide);
  }
}

async function loadOpportunities() {
  const container = document.getElementById("opp-list");
  container.classList.remove("grid", "grid-3");
  showLoading(container, "Matching roles to your skills…");
  try {
    const res = await api(`/api/opportunities?include_other_fields=${includeOtherFields}`);
    allOpportunities = res.opportunities;
    render();
  } catch (err) {
    showError(container, `Couldn't load matching roles. ${err.message}`, loadOpportunities);
  }
  loadApplyGuide();
}

function onIncludeOtherFieldsChange() {
  includeOtherFields = document.getElementById("include-other-fields").checked;
  loadOpportunities();
}

async function init() {
  document.querySelectorAll("[data-type]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.type === "All")));
  document.querySelector('[data-type="All"]').classList.add("btn-primary");

  // The profile only adds a note and a toggle. If it fails, still show roles.
  try {
    const me = await api("/api/profile/me");
    if (me.target_role) {
      document.getElementById("other-fields-toggle").style.display = "flex";
      const note = document.getElementById("field-note");
      note.textContent = `Showing roles matched to your target role (${me.target_role}) first — tick the box above to also see roles outside that field.`;
      note.style.display = "block";
    }
  } catch (e) { /* non-essential */ }

  await loadOpportunities();
}

init();
