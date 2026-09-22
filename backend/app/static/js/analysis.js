let gapChart;
let disciplines = {};

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
      renderResults(await api(`/api/skills/gap-analysis?role=${encodeURIComponent(role)}`));
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
  document.getElementById("results").style.display = "block";
  document.getElementById("no-results").style.display = "none";
  document.getElementById("match-percent").textContent = gap.match_percent + "%";
  document.getElementById("progress-fill").style.width = gap.match_percent + "%";
  document.getElementById("progress-summary").textContent =
    t("an_progress", "You match {matched} of {required} required skills for {role}.").replace("{matched}", gap.matched_skills.length).replace("{required}", gap.required_skills.length).replace("{role}", gap.role);

  document.getElementById("matched-list").innerHTML = gap.matched_skills.length
    ? gap.matched_skills.map((s) => `<span class="chip chip-matched">${icon("check")} ${escapeHtml(s)}</span>`).join("")
    : `<p style="color:var(--text-muted)">${escapeHtml(t("an_no_matched", "No matched skills yet."))}</p>`;

  document.getElementById("missing-list").innerHTML = gap.missing_skills.length
    ? gap.missing_skills.map((s) => `<span class="chip chip-missing">${escapeHtml(s)}</span>`).join("")
    : `<p style="color:var(--success-text)">${escapeHtml(t("an_all_skills", "You have all required skills!"))}</p>`;

  const ctx = document.getElementById("chart-gap");
  if (gapChart) gapChart.destroy();
  gapChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: [t("matched", "Matched"), t("missing", "Missing")],
      datasets: [{ data: [gap.match_percent, 100 - gap.match_percent], backgroundColor: ["#34d399", "#fb7185"], borderWidth: 0 }],
    },
    options: { cutout: "70%", plugins: { legend: { position: "bottom", labels: { color: "#a5abc9" } } } },
  });
}

init();
