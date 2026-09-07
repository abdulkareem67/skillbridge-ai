let gapChart;
let disciplines = {};

function fillRoles(discipline, selectedRole) {
  const roles = disciplines[discipline] || [];
  const sel = document.getElementById("role-select");
  sel.innerHTML = roles.map((r) => `<option value="${r}" ${r === selectedRole ? "selected" : ""}>${r}</option>`).join("");
}

function onDisciplineChange() {
  const discipline = document.getElementById("discipline-select").value;
  fillRoles(discipline);
}

async function init() {
  const res = await api("/api/skills/disciplines");
  disciplines = res.disciplines;
  const me = await api("/api/profile/me");

  const currentDiscipline =
    Object.keys(disciplines).find((d) => disciplines[d].includes(me.target_role)) || Object.keys(disciplines)[0];

  const dsel = document.getElementById("discipline-select");
  dsel.innerHTML = Object.keys(disciplines)
    .map((d) => `<option value="${d}" ${d === currentDiscipline ? "selected" : ""}>${d}</option>`)
    .join("");
  dsel.addEventListener("change", onDisciplineChange);

  fillRoles(currentDiscipline, me.target_role);
  if (me.target_role) runAnalysis();
}

async function runAnalysis() {
  const role = document.getElementById("role-select").value;
  try {
    await api("/api/profile/target-role", { method: "POST", body: JSON.stringify({ role }) });
    const gap = await api(`/api/skills/gap-analysis?role=${encodeURIComponent(role)}`);
    renderResults(gap);
    const { certifications } = await api(`/api/skills/certifications?role=${encodeURIComponent(role)}`);
    document.getElementById("cert-list").innerHTML = certifications.map((c) => `<span class="chip">🎓 ${c}</span>`).join("");
  } catch (err) {
    toast(err.message, "error");
  }
}

function renderResults(gap) {
  document.getElementById("results").style.display = "block";
  document.getElementById("no-results").style.display = "none";
  document.getElementById("match-percent").textContent = gap.match_percent + "%";
  document.getElementById("progress-fill").style.width = gap.match_percent + "%";
  document.getElementById("progress-summary").textContent =
    `You match ${gap.matched_skills.length} of ${gap.required_skills.length} required skills for ${gap.role}.`;

  document.getElementById("matched-list").innerHTML = gap.matched_skills.length
    ? gap.matched_skills.map((s) => `<span class="chip chip-matched">✓ ${s}</span>`).join("")
    : '<p style="color:var(--text-muted)">No matched skills yet.</p>';

  document.getElementById("missing-list").innerHTML = gap.missing_skills.length
    ? gap.missing_skills.map((s) => `<span class="chip chip-missing">${s}</span>`).join("")
    : '<p style="color:var(--success)">You have all required skills!</p>';

  const ctx = document.getElementById("chart-gap");
  if (gapChart) gapChart.destroy();
  gapChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Matched", "Missing"],
      datasets: [{ data: [gap.match_percent, 100 - gap.match_percent], backgroundColor: ["#34d399", "#fb7185"], borderWidth: 0 }],
    },
    options: { cutout: "70%", plugins: { legend: { position: "bottom", labels: { color: "#a5abc9" } } } },
  });
}

init();
