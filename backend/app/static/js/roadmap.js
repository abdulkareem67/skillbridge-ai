let roadmapData = null;
let progressMap = {};
let currentPhase = "beginner";
const phaseTitles = { beginner: "Beginner Phase", intermediate: "Intermediate Phase — Practical Projects", advanced: "Advanced Phase — Industry Projects & Interview Prep" };

async function loadRoadmap() {
  try {
    const me = await api("/api/profile/me");
    if (!me.target_role) {
      document.getElementById("roadmap-role-text").textContent = "No target role selected. Go to Skill Analysis to pick one.";
      return;
    }
    document.getElementById("roadmap-role-text").textContent = `Roadmap for: ${me.target_role}`;
    document.getElementById("download-pdf").href = `/api/reports/roadmap-pdf?role=${encodeURIComponent(me.target_role)}`;

    const res = await api(`/api/skills/roadmap?role=${encodeURIComponent(me.target_role)}`);
    roadmapData = res.roadmap;
    progressMap = await api("/api/skills/progress");
    renderPhase();
  } catch (err) {
    toast(err.message, "error");
  }
}

function switchPhase(phase) {
  currentPhase = phase;
  document.querySelectorAll(".phase-tab").forEach((t) => t.classList.toggle("active", t.dataset.phase === phase));
  renderPhase();
}

function renderPhase() {
  if (!roadmapData) return;
  const phase = roadmapData[currentPhase];
  document.getElementById("phase-title").textContent = phaseTitles[currentPhase];
  document.getElementById("phase-duration").textContent = phase.duration;

  document.getElementById("topics-list").innerHTML = phase.topics.map((t) => {
    const status = progressMap[t.skill] || (t.already_have ? "completed" : "not_started");
    const done = status === "completed";
    return `
    <div class="topic-item ${done ? "done" : ""}">
      <div class="topic-title">
        <label style="display:flex; align-items:center; gap:10px; margin:0; cursor:pointer; color:var(--text)">
          <input type="checkbox" style="width:auto;margin:0" ${done ? "checked" : ""} onchange="toggleDone('${t.skill.replace(/'/g, "\\'")}', this.checked)" />
          <strong>${t.skill}</strong> ${t.already_have ? '<span class="chip chip-matched" style="margin:0">Have it</span>' : ""}
        </label>
      </div>
      <div style="color:var(--text-muted); font-size:0.88rem">${t.resource.course}</div>
      <div class="resource-links">
        <a href="${t.resource.youtube}" target="_blank">▶ YouTube Tutorials</a>
        <a href="${t.resource.practice}" target="_blank">💻 Practice Platform</a>
      </div>
    </div>`;
  }).join("");
}

async function toggleDone(skill, checked) {
  const status = checked ? "completed" : "not_started";
  progressMap[skill] = status;
  try {
    await api("/api/skills/progress", { method: "POST", body: JSON.stringify({ skill_name: skill, status }) });
    renderPhase();
  } catch (err) {
    toast(err.message, "error");
  }
}

loadRoadmap();
