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

async function saveRole() {
  const role = document.getElementById("role-select").value;
  try {
    await api("/api/profile/target-role", { method: "POST", body: JSON.stringify({ role }) });
    toast("Target role updated");
    loadDashboard();
  } catch (err) {
    toast(err.message, "error");
  }
}

function renderMatchChart(pct) {
  const ctx = document.getElementById("chart-match");
  if (matchChart) matchChart.destroy();
  matchChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Matched", "Missing"],
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

async function loadDashboard() {
  const me = await api("/api/profile/me");
  document.getElementById("stat-total-skills").textContent = me.skills.length;
  await loadRoles(me.target_role);

  const categorized = await api("/api/skills/categorized");
  renderCategoryChart(categorized);

  if (me.target_role) {
    document.getElementById("current-role-text").textContent = `Currently targeting: ${me.target_role}`;
    try {
      const gap = await api(`/api/skills/gap-analysis`);
      document.getElementById("stat-match").textContent = gap.match_percent + "%";
      document.getElementById("stat-missing").textContent = gap.missing_skills.length;
      renderMatchChart(gap.match_percent);
    } catch (e) {}

    try {
      const { roadmap } = await api(`/api/skills/roadmap`);
      const progress = await api("/api/skills/progress");
      const allTopics = [...roadmap.beginner.topics, ...roadmap.intermediate.topics, ...roadmap.advanced.topics];
      const total = allTopics.length;
      const done = allTopics.filter((t) => (progress[t.skill] || (t.already_have ? "completed" : "not_started")) === "completed").length;
      const pct = total ? Math.round((100 * done) / total) : 0;
      document.getElementById("learning-progress-text").textContent = `${done} of ${total} roadmap skills completed for ${me.target_role}.`;
      document.getElementById("learning-progress-fill").style.width = pct + "%";
    } catch (e) {}
  } else {
    renderMatchChart(0);
  }

  try {
    const opps = await api("/api/opportunities");
    document.getElementById("stat-opportunities").textContent = opps.opportunities.filter((o) => o.match_percent >= 50).length;
  } catch (e) {}
}

loadDashboard();
