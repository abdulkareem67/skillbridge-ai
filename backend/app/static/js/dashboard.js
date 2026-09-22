let matchChart, categoryChart;
let disciplines = {};

function fillRoles(discipline, selectedRole) {
  const roles = disciplines[discipline] || [];
  const sel = document.getElementById("role-select");
  sel.innerHTML = roles.map((r) => `<option value="${r}" ${r === selectedRole ? "selected" : ""}>${r}</option>`).join("");
}

async function loadRoles(selectedRole) {
  const res = await api("/api/skills/disciplines");
  disciplines = res.disciplines;

  const currentDiscipline =
    Object.keys(disciplines).find((d) => disciplines[d].includes(selectedRole)) || Object.keys(disciplines)[0];

  const dsel = document.getElementById("discipline-select");
  dsel.innerHTML = Object.keys(disciplines)
    .map((d) => `<option value="${d}" ${d === currentDiscipline ? "selected" : ""}>${d}</option>`)
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

function renderMatchChart(pct) {
  const ctx = document.getElementById("chart-match");
  if (matchChart) matchChart.destroy();
  matchChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: [t("matched", "Matched"), t("missing", "Missing")],
      datasets: [{ data: [pct, 100 - pct], backgroundColor: ["#6d5bf8", "rgba(255,255,255,0.1)"], borderWidth: 0 }],
    },
    options: { cutout: "72%", plugins: { legend: { labels: { color: "#a5abc9" } } } },
  });
}

function renderCategoryChart(categorized) {
  const ctx = document.getElementById("chart-category");
  const labels = Object.keys(categorized);
  const data = labels.map((l) => categorized[l].length);
  if (categoryChart) categoryChart.destroy();
  categoryChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels.map((l) => l[0].toUpperCase() + l.slice(1)),
      datasets: [{ label: "Skills", data, backgroundColor: "#22d3ee" }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#a5abc9" }, grid: { display: false } },
        y: { ticks: { color: "#a5abc9", stepSize: 1 }, grid: { color: "rgba(255,255,255,0.06)" } },
      },
    },
  });
}

const STAT_IDS = ["stat-match", "stat-total-skills", "stat-missing", "stat-opportunities"];

function setStat(id, value) {
  const el = document.getElementById(id);
  el.textContent = value;
  el.parentElement.removeAttribute("aria-busy");
}

// Each section loads on its own. Previously a failure was swallowed with an
// empty catch, so the page just showed a zero - indistinguishable from a real
// zero. Now a failed section shows a dash and is named in one notice with a
// retry, and the rest of the dashboard still loads.
async function loadDashboard() {
  const status = document.getElementById("dash-status");
  status.innerHTML = "";
  STAT_IDS.forEach((id) => {
    const el = document.getElementById(id);
    el.textContent = "…";
    el.parentElement.setAttribute("aria-busy", "true");
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

  const failed = [];
  const section = (label, fn) => fn().catch(() => failed.push(label));

  await Promise.all([
    section("career tracks", () => loadRoles(me.target_role)),
    section("skill categories", async () => renderCategoryChart(await api("/api/skills/categorized"))),
    section("match score", async () => {
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
    }),
    section("learning progress", async () => {
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
    section("opportunities", async () => {
      const opps = await api("/api/opportunities");
      setStat("stat-opportunities", opps.opportunities.filter((o) => o.match_percent >= 50).length);
    }),
  ]);

  // Anything still showing the loading ellipsis belongs to a section that failed.
  STAT_IDS.forEach((id) => { if (document.getElementById(id).textContent === "…") setStat(id, "—"); });
  if (document.getElementById("learning-progress-text").textContent === "Loading…") {
    document.getElementById("learning-progress-text").textContent = t("progress_load_failed", "Couldn't load your progress.");
  }
  if (failed.length) {
    showError(status, t("dash_partial", "Some parts of your dashboard didn't load: {parts}.").replace("{parts}", failed.join(", ")), loadDashboard);
  }
}

loadDashboard();
