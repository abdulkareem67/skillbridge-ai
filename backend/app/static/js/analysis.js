let gapChart;
let disciplines = {};
let currentGapData = null;
let currentSkillFilter = "all";
let skillSearchQuery = "";

function fillRoles(discipline, selectedRole) {
  const roles = disciplines[discipline] || [];
  const sel = document.getElementById("role-select");
  sel.innerHTML = roles.map((r) => `<option value="${escapeHtml(r)}" ${r === selectedRole ? "selected" : ""}>${escapeHtml(r)}</option>`).join("");
}

function onDisciplineChange() {
  const discipline = document.getElementById("discipline-select").value;
  fillRoles(discipline);
}

async function init() {
  const status = document.getElementById("analysis-status");
  const button = document.getElementById("analyze-btn");
  button.disabled = true;
  showLoading(status, t("an_load_tracks", "Loading career tracks…"));

  initSkillSearch();

  let me;
  try {
    const [res, profile] = await Promise.all([api("/api/skills/disciplines"), api("/api/profile/me")]);
    disciplines = res.disciplines;
    me = profile;
  } catch (err) {
    showError(status, t("an_tracks_failed", "Couldn't load career tracks. {msg}").replace("{msg}", err.message), init);
    return;
  }
  status.innerHTML = "";
  clearState(status);
  button.disabled = false;

  const currentDiscipline =
    Object.keys(disciplines).find((d) => disciplines[d].includes(me.target_role)) || Object.keys(disciplines)[0];

  const dsel = document.getElementById("discipline-select");
  dsel.innerHTML = Object.keys(disciplines)
    .map((d) => `<option value="${escapeHtml(d)}" ${d === currentDiscipline ? "selected" : ""}>${escapeHtml(d)}</option>`)
    .join("");
  dsel.onchange = onDisciplineChange;

  fillRoles(currentDiscipline, me.target_role);
  if (!me.skills.length) {
    showEmpty(status, t("an_no_skills", "You haven't added any skills yet, so every requirement will show as missing."),
      '<a class="btn btn-sm" href="/cv-upload">Add skills</a>');
  }
  if (me.target_role) runAnalysis(button);
}

async function runAnalysis(button) {
  const role = document.getElementById("role-select").value;
  if (!role) return;
  const certs = document.getElementById("cert-list");
  await withBusy(button, async () => {
    try {
      await api("/api/profile/target-role", { method: "POST", body: JSON.stringify({ role }) });
      const gap = await api(`/api/skills/gap-analysis?role=${encodeURIComponent(role)}`);
      currentGapData = gap;
      renderResults(gap);
    } catch (err) {
      toast(err.message, "error");
      return;
    }
    // Certifications are extra; if they fail, the analysis above still stands.
    showLoading(certs, t("an_finding_certs", "Finding certifications…"));
    try {
      const { certifications } = await api(`/api/skills/certifications?role=${encodeURIComponent(role)}`);
      clearState(certs);
      certs.innerHTML = certifications.length
        ? certifications.map((c) => `<span class="chip">${icon("graduation-cap")} ${escapeHtml(c)}</span>`).join("")
        : `<p style="color:var(--text-muted)">${escapeHtml(t("an_no_certs", "No specific certifications recommended for this role."))}</p>`;
    } catch (err) {
      showError(certs, t("an_certs_failed", "Couldn't load certifications. {msg}").replace("{msg}", err.message));
    }
  }, t("an_analysing", "Analysing…"));
}

function renderResults(gap) {
  currentGapData = gap;
  document.getElementById("results").style.display = "block";
  document.getElementById("no-results").style.display = "none";
  document.getElementById("match-percent").textContent = gap.match_percent + "%";
  document.getElementById("progress-fill").style.width = gap.match_percent + "%";
  document.getElementById("progress-summary").textContent =
    t("an_progress", "You match {matched} of {required} required skills for {role}.").replace("{matched}", gap.matched_skills.length).replace("{required}", gap.required_skills.length).replace("{role}", gap.role);

  const roleBadge = document.getElementById("target-role-badge");
  if (roleBadge) roleBadge.textContent = "Target: " + gap.role;

  const badge = document.getElementById("readiness-badge");
  const advice = document.getElementById("analysis-advice");
  if (badge) {
    if (gap.match_percent >= 80) {
      badge.className = "readiness-status readiness-high";
      badge.innerHTML = `${icon("check-circle", 14)} High Readiness · Ready to Apply`;
      if (advice) advice.textContent = "You have the majority of core requirements for this role. Focus on polishing your portfolio, practicing interview questions, and actively applying to open opportunities.";
    } else if (gap.match_percent >= 50) {
      badge.className = "readiness-status readiness-mid";
      badge.innerHTML = `${icon("sparkles", 14)} Intermediate · Strong Foundation`;
      if (advice) advice.textContent = "You match the core foundational skills. Bridging 2 or 3 of your top missing skills will significantly elevate your chances in job screenings.";
    } else {
      badge.className = "readiness-status readiness-low";
      badge.innerHTML = `${icon("compass", 14)} Skill Building Phase`;
      if (advice) advice.textContent = "You are in the learning phase for this career track. Follow the personalized roadmap to methodically acquire the beginner and intermediate skills.";
    }
  }

  const matchedCountEl = document.getElementById("matched-count");
  if (matchedCountEl) matchedCountEl.textContent = gap.matched_skills.length;
  const missingCountEl = document.getElementById("missing-count");
  if (missingCountEl) missingCountEl.textContent = gap.missing_skills.length;

  renderSkillLists();
  renderGapChart(gap.match_percent);
}

function renderSkillLists() {
  if (!currentGapData) return;

  const q = skillSearchQuery.toLowerCase().trim();
  const matched = currentGapData.matched_skills.filter((s) => !q || s.toLowerCase().includes(q));
  const missing = currentGapData.missing_skills.filter((s) => !q || s.toLowerCase().includes(q));

  const cardMatched = document.getElementById("card-matched");
  const cardMissing = document.getElementById("card-missing");

  if (currentSkillFilter === "missing") {
    if (cardMatched) cardMatched.style.display = "none";
    if (cardMissing) cardMissing.style.display = "block";
  } else if (currentSkillFilter === "matched") {
    if (cardMatched) cardMatched.style.display = "block";
    if (cardMissing) cardMissing.style.display = "none";
  } else {
    if (cardMatched) cardMatched.style.display = "block";
    if (cardMissing) cardMissing.style.display = "block";
  }

  document.getElementById("matched-list").innerHTML = matched.length
    ? matched.map((s) => `<span class="chip chip-matched">${icon("check", 14)} ${escapeHtml(s)}</span>`).join("")
    : `<p style="color:var(--text-muted)">${q ? "No matched skills matching search." : escapeHtml(t("an_no_matched", "No matched skills yet."))}</p>`;

  document.getElementById("missing-list").innerHTML = missing.length
    ? missing.map((s) => `<span class="chip chip-missing">${escapeHtml(s)}</span>`).join("")
    : `<p style="color:var(--success-text)">${q ? "No missing skills matching search." : escapeHtml(t("an_all_skills", "You have all required skills!"))}</p>`;
}

function filterSkills(type) {
  currentSkillFilter = type;
  document.querySelectorAll("[data-skill-filter]").forEach((btn) => {
    const on = btn.dataset.skillFilter === type;
    btn.classList.toggle("btn-primary", on);
    btn.classList.toggle("btn-ghost", !on);
  });
  renderSkillLists();
}

function initSkillSearch() {
  const input = document.getElementById("skill-search");
  const clearBtn = document.getElementById("skill-search-clear");
  if (!input) return;

  const wrap = input.closest(".search-bar-wrap");
  input.addEventListener("input", () => {
    skillSearchQuery = input.value;
    if (wrap) wrap.classList.toggle("has-value", Boolean(input.value));
    renderSkillLists();
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      input.value = "";
      skillSearchQuery = "";
      if (wrap) wrap.classList.remove("has-value");
      renderSkillLists();
    });
  }
}

function copyGapSummary() {
  if (!currentGapData) return;
  const { role, match_percent, matched_skills, missing_skills } = currentGapData;
  const text = [
    `SkillBridge AI Career Analysis for ${role}`,
    `Match Score: ${match_percent}%`,
    `Skills Matched (${matched_skills.length}): ${matched_skills.join(", ") || "None"}`,
    `Skills to Learn (${missing_skills.length}): ${missing_skills.join(", ") || "None"}`,
    `Analysis generated via SkillBridge AI`
  ].join("\n");

  copyToClipboard(text, "Career analysis copied to clipboard!");
}

let lastGapPct = null;

function renderGapChart(pct) {
  lastGapPct = pct;
  const c = chartTheme();
  const ctx = document.getElementById("chart-gap");
  if (gapChart) gapChart.destroy();
  gapChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: [t("matched", "Matched"), t("missing", "Missing")],
      datasets: [{ data: [pct, 100 - pct], backgroundColor: [c.success, c.danger], borderWidth: 0 }],
    },
    options: {
      cutout: "70%",
      plugins: {
        legend: { position: "bottom", labels: { color: c.text } },
        tooltip: {
          callbacks: {
            label: (item) => ` ${item.label}: ${item.raw}%`
          }
        }
      }
    },
  });
}

document.addEventListener("sb:themechange", () => {
  if (lastGapPct !== null) renderGapChart(lastGapPct);
});

init();
