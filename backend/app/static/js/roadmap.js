let roadmapData = null;
let progressMap = {};
let currentPhase = "beginner";
const phaseTitles = { beginner: "Beginner Phase", intermediate: "Intermediate Phase — Practical Projects", advanced: "Advanced Phase — Industry Projects & Interview Prep" };

async function loadRoadmap() {
  const roleText = document.getElementById("roadmap-role-text");
  const list = document.getElementById("topics-list");
  const pdf = document.getElementById("download-pdf");
  showLoading(list, "Building your roadmap…");
  try {
    const me = await api("/api/profile/me");
    if (!me.target_role) {
      roleText.textContent = "Pick a target role to get a roadmap.";
      showEmpty(list, "Your roadmap is built from the gap between your skills and a target role — choose a role first.",
        '<a class="btn btn-sm" href="/skill-analysis">Choose a role</a>');
      return;
    }
    roleText.textContent = `Roadmap for: ${me.target_role}`;

    const [res, progress] = await Promise.all([
      api(`/api/skills/roadmap?role=${encodeURIComponent(me.target_role)}`),
      api("/api/skills/progress"),
    ]);
    roadmapData = res.roadmap;
    progressMap = progress;

    // The PDF link only makes sense once we know the role it is for.
    pdf.href = `/api/reports/roadmap-pdf?role=${encodeURIComponent(me.target_role)}`;
    pdf.removeAttribute("aria-disabled");
    pdf.classList.remove("is-disabled");

    clearState(list);
    renderPhase();
  } catch (err) {
    roleText.textContent = "Your roadmap couldn't be loaded.";
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
  document.getElementById("phase-title").textContent = phaseTitles[currentPhase];
  document.getElementById("phase-duration").textContent = phase.duration;

  if (!phase.topics.length) {
    showEmpty(list, "Nothing to learn in this phase for your role.");
    return;
  }

  // Skills travel in data attributes, not inside an inline onchange string, so a
  // name containing a quote can't break out of the handler.
  list.innerHTML = phase.topics.map((t) => {
    const status = progressMap[t.skill] || (t.already_have ? "completed" : "not_started");
    const done = status === "completed";
    return `
    <div class="topic-item ${done ? "done" : ""}">
      <div class="topic-title">
        <label style="display:flex; align-items:center; gap:10px; margin:0; cursor:pointer; color:var(--text)">
          <input type="checkbox" class="topic-check" style="width:auto;margin:0" data-skill="${escapeHtml(t.skill)}" ${done ? "checked" : ""} />
          <strong>${escapeHtml(t.skill)}</strong> ${t.already_have ? '<span class="chip chip-matched" style="margin:0">Have it</span>' : ""}
        </label>
      </div>
      <div style="color:var(--text-muted); font-size:0.88rem">${escapeHtml(t.resource.course)}</div>
      <div class="resource-links">
        <a href="${escapeHtml(t.resource.youtube)}" target="_blank" rel="noopener">▶ YouTube Tutorials</a>
        <a href="${escapeHtml(t.resource.practice)}" target="_blank" rel="noopener">${icon("laptop")} Practice Platform</a>
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
  } catch (err) {
    // Put it back. Leaving the box ticked after a failed save told people their
    // progress was recorded when it wasn't.
    if (previous === undefined) delete progressMap[skill]; else progressMap[skill] = previous;
    box.checked = !box.checked;
    box.disabled = false;
    toast(`Couldn't save that. ${err.message}`, "error");
  }
}

loadRoadmap();
