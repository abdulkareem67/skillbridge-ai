let matchChart, categoryChart;
let disciplines = {};

function fillRoles(discipline, selectedRole) {
  const roles = disciplines[discipline] || [];
  const sel = document.getElementById("role-select");
  sel.innerHTML = roles.map((r) => `<option value="${escapeHtml(r)}" ${r === selectedRole ? "selected" : ""}>${escapeHtml(r)}</option>`).join("");
}

async function loadRoles(selectedRole) {
  const res = await api("/api/skills/disciplines");
  disciplines = res.disciplines;

  const currentDiscipline =
    Object.keys(disciplines).find((d) => disciplines[d].includes(selectedRole)) || Object.keys(disciplines)[0];

  const dsel = document.getElementById("discipline-select");
  dsel.innerHTML = Object.keys(disciplines)
    .map((d) => `<option value="${escapeHtml(d)}" ${d === currentDiscipline ? "selected" : ""}>${escapeHtml(d)}</option>`)
    .join("");
  dsel.onchange = () => fillRoles(dsel.value);

  fillRoles(currentDiscipline, selectedRole);
}

async function saveRole(button) {
  const role = document.getElementById("role-select").value;
  if (!role) return;
  await withBusy(button, async () => {
    try {
      await api("/api/profile/target-role", { method: "POST", body: JSON.stringify({ role }) });
      toast(t("role_updated", "Target role updated"));
      await loadDashboard();
    } catch (err) {
      toast(err.message, "error");
    }
  }, t("saving", "Saving…"));
}

let lastMatchPct = null;
let lastCategorized = null;

const CATEGORY_LABELS = {
  technical: ["cat_technical", "Technical Skills"],
  soft: ["cat_soft", "Soft Skills"],
  tool: ["cat_tool", "Tools & Technologies"],
  certification: ["cat_certification", "Certifications"],
};
function categoryLabel(key) {
  const entry = CATEGORY_LABELS[key];
  return entry ? t(entry[0], entry[1]) : key[0].toUpperCase() + key.slice(1);
}

function renderMatchChart(pct) {
  lastMatchPct = pct;
  const c = chartTheme();
  const ctx = document.getElementById("chart-match");
  if (matchChart) matchChart.destroy();
  matchChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: [t("matched", "Matched"), t("missing", "Missing")],
      datasets: [{ data: [pct, 100 - pct], backgroundColor: [c.accent, c.track], borderWidth: 0 }],
    },
    options: {
      // The .chart-box sets the height; without this Chart.js keeps its own
      // aspect ratio and a doughnut fills the whole height of a phone screen.
      maintainAspectRatio: false,
      cutout: "72%",
      plugins: {
        legend: { labels: { color: c.text } },
        tooltip: {
          callbacks: {
            label: (item) => ` ${item.label}: ${item.raw}%`
          }
        }
      }
    },
  });
}

function renderCategoryChart(categorized) {
  lastCategorized = categorized;
  const c = chartTheme();
  const ctx = document.getElementById("chart-category");
  const keys = Object.keys(categorized);
  const data = keys.map((k) => categorized[k].length);
  if (categoryChart) categoryChart.destroy();
  categoryChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: keys.map(categoryLabel),
      datasets: [{ label: t("skills_label", "Skills"), data, backgroundColor: c.accent2 }],
    },
    options: {
      // The .chart-box sets the height; without this Chart.js keeps its own
      // aspect ratio and a doughnut fills the whole height of a phone screen.
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: c.text }, grid: { display: false } },
        y: { ticks: { color: c.text, stepSize: 1 }, grid: { color: c.grid } },
      },
    },
  });
}

document.addEventListener("sb:themechange", () => {
  if (lastMatchPct !== null) renderMatchChart(lastMatchPct);
  if (lastCategorized !== null) renderCategoryChart(lastCategorized);
});

const STAT_IDS = ["stat-match", "stat-total-skills", "stat-missing", "stat-opportunities"];

function setStat(id, value) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = value;
    el.parentElement.removeAttribute("aria-busy");
  }
}

function setNextAction(title, desc, btnText, btnHref) {
  const banner = document.getElementById("dash-next-action");
  if (!banner) return;
  document.getElementById("next-action-title").textContent = title;
  document.getElementById("next-action-desc").textContent = desc;
  const btn = document.getElementById("next-action-btn");
  btn.textContent = btnText;
  btn.href = btnHref;
  banner.style.display = "flex";
}

async function loadDashboard() {
  const status = document.getElementById("dash-status");
  if (status) status.innerHTML = "";

  STAT_IDS.forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.innerHTML = '<span class="skeleton skeleton-stat"></span>';
      el.parentElement.setAttribute("aria-busy", "true");
    }
  });

  let me;
  try {
    me = await api("/api/profile/me");
  } catch (err) {
    STAT_IDS.forEach((id) => setStat(id, "—"));
    showError(status, t("dash_load_failed", "Couldn't load your dashboard. {msg}").replace("{msg}", err.message), loadDashboard);
    return;
  }

  setStat("stat-total-skills", me.skills.length);
  document.getElementById("current-role-text").textContent = me.target_role
    ? t("targeting", "Currently targeting: {role}").replace("{role}", me.target_role)
    : t("no_role", "No target role selected yet.");

  if (!me.skills.length) {
    setNextAction(
      t("na_upload_title", "Upload your CV or add skills"),
      t("na_upload_desc", "Start by uploading your CV or adding skills to unlock your gap analysis and role matches."),
      t("na_upload_btn", "Upload CV"),
      "/cv-upload"
    );
  } else if (!me.target_role) {
    setNextAction(
      t("na_role_title", "Choose a target role"),
      t("na_role_desc", "Pick the career you're aiming for below to see how ready you are and get a tailored roadmap."),
      t("na_role_btn", "Choose a role"),
      "#role-select"
    );
  }

  const failed = [];
  const section = (label, fn) => fn().catch(() => failed.push(label));

  await Promise.all([
    section(t("dash_part_tracks", "career tracks"), () => loadRoles(me.target_role)),
    section(t("dash_part_categories", "skill categories"), async () => renderCategoryChart(await api("/api/skills/categorized"))),
    section(t("dash_part_match", "match score"), async () => {
      if (!me.target_role) {
        setStat("stat-match", "—");
        setStat("stat-missing", "—");
        renderMatchChart(0);
        return;
      }
      const gap = await api("/api/skills/gap-analysis");
      setStat("stat-match", gap.match_percent + "%");
      setStat("stat-missing", gap.missing_skills.length);
      renderMatchChart(gap.match_percent);

      // No country here: the user may be job-hunting anywhere, and this used
      // to name one country's job market to everybody.
      if (gap.missing_skills.length > 0) {
        const skill = gap.missing_skills[0];
        setNextAction(
          t("na_priority_title", "Priority skill: {skill}").replace("{skill}", skill),
          t("na_priority_desc", "Learning {skill} is the biggest single step towards {role} right now.").replace("{skill}", skill).replace("{role}", me.target_role),
          t("na_priority_btn", "Start learning"),
          "/roadmap"
        );
      } else {
        setNextAction(
          t("na_ready_title", "Ready for {role}!").replace("{role}", me.target_role),
          t("na_ready_desc", "You have every skill we track for this role. Start applying — the Opportunities page links to live job boards in your country."),
          t("na_ready_btn", "Explore openings"),
          "/opportunities"
        );
      }
    }),
    section(t("dash_part_progress", "learning progress"), async () => {
      const text = document.getElementById("learning-progress-text");
      if (!me.target_role) {
        text.textContent = t("set_role_hint", "Set a target role to start tracking roadmap progress.");
        return;
      }
      const [{ roadmap }, progress] = await Promise.all([api("/api/skills/roadmap"), api("/api/skills/progress")]);
      const allTopics = [...roadmap.beginner.topics, ...roadmap.intermediate.topics, ...roadmap.advanced.topics];
      const total = allTopics.length;
      const done = allTopics.filter((t) => (progress[t.skill] || (t.already_have ? "completed" : "not_started")) === "completed").length;
      const pct = total ? Math.round((100 * done) / total) : 0;
      text.textContent = t("progress_done", "{done} of {total} roadmap skills completed for {role}.").replace("{done}", done).replace("{total}", total).replace("{role}", me.target_role);
      document.getElementById("learning-progress-fill").style.width = pct + "%";
    }),
    section(t("dash_part_opps", "opportunities"), async () => {
      const opps = await api("/api/opportunities");
      setStat("stat-opportunities", opps.opportunities.filter((o) => o.match_percent >= 50).length);
    }),
  ]);

  STAT_IDS.forEach((id) => {
    const el = document.getElementById(id);
    if (el && el.innerHTML.includes("skeleton")) setStat(id, "—");
  });

  if (failed.includes(t("dash_part_progress", "learning progress"))) {
    document.getElementById("learning-progress-text").textContent = t("progress_load_failed", "Couldn't load your progress.");
  }
  if (failed.length && status) {
    showError(status, t("dash_partial", "Some parts of your dashboard didn't load: {parts}.").replace("{parts}", failed.join(", ")), loadDashboard);
  }
}

loadDashboard();
