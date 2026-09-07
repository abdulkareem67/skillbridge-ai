let pendingManualSkills = [];

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => { if (fileInput.files.length) handleFile(fileInput.files[0]); });

async function handleFile(file) {
  const status = document.getElementById("upload-status");
  status.innerHTML = `<div style="display:flex;align-items:center;gap:8px"><div class="spinner"></div> Extracting skills from ${file.name}...</div>`;
  const fd = new FormData();
  fd.append("file", file);
  try {
    const result = await api("/api/profile/cv-upload", { method: "POST", body: fd });
    status.innerHTML = `<span style="color:var(--success)">✔ Extracted ${result.extracted_count} skill(s) from your CV (replaced any skills from a previous CV upload).</span>`;
    toast(`${result.extracted_count} skills extracted from CV`);
    loadSkillProfile();
  } catch (err) {
    status.innerHTML = `<span style="color:var(--danger)">${err.message}</span>`;
  }
}

const manualInput = document.getElementById("manual-skill-input");
manualInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && manualInput.value.trim()) {
    e.preventDefault();
    pendingManualSkills.push(manualInput.value.trim());
    manualInput.value = "";
    renderPendingChips();
  }
});

function renderPendingChips() {
  const el = document.getElementById("manual-chip-preview");
  el.innerHTML = pendingManualSkills.map((s, i) =>
    `<span class="chip">${escapeHtml(s)} <span class="chip-remove" onclick="removePending(${i})">×</span></span>`
  ).join("");
}

function removePending(i) {
  pendingManualSkills.splice(i, 1);
  renderPendingChips();
}

async function submitManualSkills() {
  if (manualInput.value.trim()) { pendingManualSkills.push(manualInput.value.trim()); manualInput.value = ""; }
  if (!pendingManualSkills.length) { toast("Enter at least one skill", "error"); return; }
  try {
    await api("/api/profile/skills/manual", { method: "POST", body: JSON.stringify({ skills: pendingManualSkills }) });
    toast(`${pendingManualSkills.length} skill(s) added`);
    pendingManualSkills = [];
    renderPendingChips();
    loadSkillProfile();
  } catch (err) {
    toast(err.message, "error");
  }
}

async function removeSkill(name) {
  await api(`/api/profile/skills/${encodeURIComponent(name)}`, { method: "DELETE" });
  loadSkillProfile();
}

async function clearAllSkills() {
  if (!confirm("Remove all skills from your profile? This can't be undone.")) return;
  await api("/api/profile/skills", { method: "DELETE" });
  toast("All skills cleared");
  loadSkillProfile();
}

async function loadSkillProfile() {
  const categorized = await api("/api/skills/categorized");
  const container = document.getElementById("category-lists");
  const empty = document.getElementById("empty-skills");
  const labels = { technical: "Technical Skills", soft: "Soft Skills", tool: "Tools & Technologies", certification: "Certifications" };
  const total = Object.values(categorized).reduce((a, b) => a + b.length, 0);
  empty.style.display = total === 0 ? "block" : "none";

  container.innerHTML = Object.keys(labels).map((cat) => `
    <div>
      <h4 style="margin:0 0 8px">${labels[cat]}</h4>
      <div>${(categorized[cat] || []).map((s) => `<span class="chip">${escapeHtml(s)} <span class="chip-remove" data-skill="${escapeHtml(s)}">×</span></span>`).join("") || '<span style="color:var(--text-muted); font-size:0.85rem">None yet</span>'}</div>
    </div>
  `).join("");
  container.querySelectorAll(".chip-remove[data-skill]").forEach((el) => {
    el.addEventListener("click", () => removeSkill(el.dataset.skill));
  });

  loadResumeTips();
}

async function loadResumeTips() {
  const { tips } = await api("/api/skills/resume-tips");
  document.getElementById("resume-tips-list").innerHTML = tips.map((t) => `<li>${escapeHtml(t)}</li>`).join("");
  loadImprovedCV();
}

function skillRow(label, items) {
  if (!items || !items.length) return "";
  return `<div style="margin-bottom:10px"><strong>${label}:</strong> ${items.map(escapeHtml).join(", ")}</div>`;
}

async function loadImprovedCV() {
  document.getElementById("download-cv-pdf").href = "/api/reports/improved-cv-pdf";
  const { cv } = await api("/api/reports/improved-cv");
  const el = document.getElementById("cv-preview");
  el.innerHTML = `
    <div class="topic-item">
      <div style="margin-bottom:10px"><strong>Professional Summary:</strong><br/>${escapeHtml(cv.summary)}</div>
      ${skillRow("Technical Skills", cv.technical_skills)}
      ${skillRow("Tools & Technologies", cv.tools)}
      ${skillRow("Soft Skills", cv.soft_skills)}
      ${skillRow("Certifications", cv.certifications)}
      ${cv.project_suggestions.length ? `<div><strong>Suggested Projects to Add:</strong><ul style="margin:6px 0 0; padding-left:20px">${cv.project_suggestions.map((p) => `<li>${escapeHtml(p)}</li>`).join("")}</ul></div>` : ""}
    </div>
  `;
}

loadSkillProfile();
