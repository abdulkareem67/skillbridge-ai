let roadmapData = null;
let progressMap = {};
let currentPhase = "beginner";
const phaseTitles = () => ({
  beginner: t("rm_phase_beginner", "Beginner Phase"),
  intermediate: t("rm_phase_intermediate", "Intermediate Phase — Practical Projects"),
  advanced: t("rm_phase_advanced", "Advanced Phase — Industry Projects & Interview Prep")
});

function updateRoadmapProgress() {
  if (!roadmapData) return;
  const allTopics = [
    ...(roadmapData.beginner ? roadmapData.beginner.topics : []),
    ...(roadmapData.intermediate ? roadmapData.intermediate.topics : []),
    ...(roadmapData.advanced ? roadmapData.advanced.topics : [])
  ];
  const total = allTopics.length;
  const completed = allTopics.filter((t) => (progressMap[t.skill] || (t.already_have ? "completed" : "not_started")) === "completed").length;
  const pct = total ? Math.round((completed * 100) / total) : 0;

  const bar = document.getElementById("roadmap-progress-fill");
  const pctText = document.getElementById("roadmap-progress-pct");
  const summaryText = document.getElementById("roadmap-progress-summary");

  if (bar) bar.style.width = pct + "%";
  if (pctText) pctText.textContent = pct + "% Completed";
  if (summaryText) summaryText.textContent = `${completed} of ${total} roadmap skills mastered`;
}

async function loadRoadmap() {
  const roleText = document.getElementById("roadmap-role-text");
  const list = document.getElementById("topics-list");
  const pdf = document.getElementById("download-pdf");
  const progressCard = document.getElementById("roadmap-progress-card");
  showLoading(list, t("rm_building", "Building your roadmap…"));
  try {
    const me = await api("/api/profile/me");
    if (!me.target_role) {
      if (progressCard) progressCard.style.display = "none";
      roleText.textContent = t("rm_pick_role", "Pick a target role to get a roadmap.");
      showEmpty(list, t("rm_empty", "Your roadmap is built from the gap between your skills and a target role — choose a role first."),
        `<a class="btn btn-sm" href="/skill-analysis">${escapeHtml(t("rm_choose_role", "Choose a role"))}</a>`);
      return;
    }
    if (progressCard) progressCard.style.display = "block";
    roleText.textContent = t("rm_for", "Roadmap for: {role}").replace("{role}", me.target_role);

    const [res, progress] = await Promise.all([
      api(`/api/skills/roadmap?role=${encodeURIComponent(me.target_role)}`),
      api("/api/skills/progress"),
    ]);
    roadmapData = res.roadmap;
    progressMap = progress;

    // The PDF link only makes sense once we know the role it is for.
    if (pdf) {
      pdf.href = `/api/reports/roadmap-pdf?role=${encodeURIComponent(me.target_role)}`;
      pdf.removeAttribute("aria-disabled");
      pdf.classList.remove("is-disabled");
    }

    clearState(list);
    renderPhase();
    updateRoadmapProgress();
  } catch (err) {
    roleText.textContent = t("rm_failed", "Your roadmap couldn't be loaded.");
    showError(list, err.message, loadRoadmap);
  }
}

function switchPhase(phase) {
  currentPhase = phase;
  document.querySelectorAll(".phase-tab").forEach((t) => {
    const on = t.dataset.phase === phase;
    t.classList.toggle("active", on);
    t.setAttribute("aria-selected", String(on));
  });
  renderPhase();
}

function renderPhase() {
  if (!roadmapData) return;
  const phase = roadmapData[currentPhase];
  const list = document.getElementById("topics-list");
  document.getElementById("phase-title").textContent = phaseTitles()[currentPhase];
  document.getElementById("phase-duration").textContent = phase.duration;

  if (!phase.topics.length) {
    showEmpty(list, t("rm_nothing", "Nothing to learn in this phase for your role."));
    return;
  }

  list.innerHTML = phase.topics.map((topic) => {
    const status = progressMap[topic.skill] || (topic.already_have ? "completed" : "not_started");
    const done = status === "completed";
    return `
    <div class="topic-item ${done ? "done" : ""}">
      <div class="topic-title">
        <label style="display:flex; align-items:center; gap:10px; margin:0; cursor:pointer; color:var(--text)">
          <input type="checkbox" class="topic-check" style="width:auto;margin:0" data-skill="${escapeHtml(topic.skill)}" ${done ? "checked" : ""} />
          <strong>${escapeHtml(topic.skill)}</strong> ${topic.already_have ? `<span class="chip chip-matched" style="margin:0">${escapeHtml(t("rm_have_it", "Have it"))}</span>` : ""}
        </label>
      </div>
      <div style="color:var(--text-muted); font-size:0.88rem">${escapeHtml(topic.resource.course)}</div>
      <div class="resource-links">
        <a href="${escapeHtml(topic.resource.youtube)}" target="_blank" rel="noopener">▶ ${escapeHtml(t("rm_youtube", "YouTube Tutorials"))}</a>
        <a href="${escapeHtml(topic.resource.practice)}" target="_blank" rel="noopener">${icon("laptop")} ${escapeHtml(t("rm_practice", "Practice Platform"))}</a>
      </div>
    </div>`;
  }).join("");
}

document.getElementById("topics-list").addEventListener("change", (e) => {
  if (e.target.classList.contains("topic-check")) toggleDone(e.target);
});

async function toggleDone(box) {
  const skill = box.dataset.skill;
  const previous = progressMap[skill];
  const status = box.checked ? "completed" : "not_started";
  progressMap[skill] = status;
  box.disabled = true;
  try {
    await api("/api/skills/progress", { method: "POST", body: JSON.stringify({ skill_name: skill, status }) });
    renderPhase();
    updateRoadmapProgress();
    toast(box.checked ? `Marked "${skill}" as completed!` : `Marked "${skill}" as in-progress`, "success");
  } catch (err) {
    if (previous === undefined) delete progressMap[skill]; else progressMap[skill] = previous;
    box.checked = !box.checked;
    box.disabled = false;
    toast(t("rm_save_failed", "Couldn't save that. {msg}").replace("{msg}", err.message), "error");
  }
}

loadRoadmap();
