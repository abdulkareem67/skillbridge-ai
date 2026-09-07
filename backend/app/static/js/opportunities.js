let allOpportunities = [];
let currentFilter = "All";
let includeOtherFields = false;

function badgeColor(pct) {
  if (pct >= 70) return "var(--success)";
  if (pct >= 40) return "var(--warning)";
  return "var(--danger)";
}

function render() {
  const list = currentFilter === "All" ? allOpportunities : allOpportunities.filter((o) => o.type === currentFilter);
  const container = document.getElementById("opp-list");
  document.getElementById("empty-opps").style.display = list.length ? "none" : "block";
  container.innerHTML = list.map((o) => `
    <div class="glass opp-card">
      <span class="opp-type">${o.type}</span>
      ${o.field ? `<span class="opp-type" style="background:rgba(34,211,238,0.15); color:var(--accent-2, #22d3ee)">${o.field}</span>` : ""}
      <h3 style="margin:8px 0 4px">${o.title}</h3>
      <p style="margin:0 0 4px; color:var(--text-muted)">${o.company} • ${o.location}</p>
      <div style="display:flex; align-items:center; gap:10px; margin:12px 0">
        <div class="progress-track" style="flex:1">
          <div class="progress-fill" style="width:${o.match_percent}%; background:${badgeColor(o.match_percent)}"></div>
        </div>
        <strong style="color:${badgeColor(o.match_percent)}">${o.match_percent}%</strong>
      </div>
      <div>${o.skills.map((s) => `<span class="chip ${o.matched_skills.includes(s) ? "chip-matched" : ""}" style="font-size:0.75rem">${s}</span>`).join("")}</div>
      <div class="resource-links">${o.apply_links.map((l) => `<a href="${l.url}" target="_blank" rel="noopener">🔗 ${l.label}</a>`).join("")}</div>
    </div>
  `).join("");
}

function filterType(type) {
  currentFilter = type;
  document.querySelectorAll("[data-type]").forEach((b) => b.classList.toggle("btn-primary", b.dataset.type === type));
  render();
}

async function loadApplyGuide() {
  const guide = await api("/api/opportunities/application-guide");
  document.getElementById("apply-guide-list").innerHTML = guide.steps.map((s) => `<li>${escapeHtml(s)}</li>`).join("");
}

async function loadOpportunities() {
  const res = await api(`/api/opportunities?include_other_fields=${includeOtherFields}`);
  allOpportunities = res.opportunities;
  render();
  loadApplyGuide();
}

function onIncludeOtherFieldsChange() {
  includeOtherFields = document.getElementById("include-other-fields").checked;
  loadOpportunities();
}

async function init() {
  document.querySelector('[data-type="All"]').classList.add("btn-primary");

  const me = await api("/api/profile/me");
  if (me.target_role) {
    document.getElementById("other-fields-toggle").style.display = "flex";
    const note = document.getElementById("field-note");
    note.textContent = `Showing opportunities matched to your target role (${me.target_role}) first — tick the box above to also see roles outside that field.`;
    note.style.display = "block";
  }

  await loadOpportunities();
}

init();
