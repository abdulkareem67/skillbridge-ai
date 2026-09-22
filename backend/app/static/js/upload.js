let pendingManualSkills = [];

const MAX_CV_BYTES = 5 * 1024 * 1024;
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");

dropzone.addEventListener("click", () => fileInput.click());
// The dropzone is a role="button" div, so it must answer the keys a button does.
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); }
});
dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => { if (fileInput.files.length) handleFile(fileInput.files[0]); fileInput.value = ""; });

async function handleFile(file) {
  const status = document.getElementById("upload-status");
  if (!/\.(pdf|docx)$/i.test(file.name)) {
    showError(status, t("cv_type_bad", "That file type isn't supported. Upload a PDF or a DOCX."));
    return;
  }
  // Checked here too so a 40 MB scan fails in a second, not after the upload.
  if (file.size > MAX_CV_BYTES) {
    showError(status, t("cv_too_big", "That file is over 5 MB. Try exporting a smaller PDF, or upload a DOCX."));
    return;
  }
  // The file name is user-controlled; showLoading escapes it. Interpolating it
  // straight into innerHTML, as this used to, ran any markup in the name.
  showLoading(status, t("cv_extracting", "Extracting skills from {name}…").replace("{name}", file.name));
  dropzone.setAttribute("aria-disabled", "true");
  const fd = new FormData();
  fd.append("file", file);
  try {
    const result = await api("/api/profile/cv-upload", { method: "POST", body: fd, timeout: 45000 });
    if (!result.extracted_count) {
      // Most often a scanned PDF: an image of text, with no text layer to read.
      showEmpty(status,
        t("cv_no_skills", "We couldn't find any skills we recognise in that file. If it's a scanned PDF, try a DOCX or a PDF exported from Word or Google Docs — or add your skills manually."));
    } else {
      status.innerHTML = `<div class="state-box state-success" role="status">${icon("check-circle", 20)}<div class="state-text"><p>${(result.extracted_count === 1 ? t("cv_extracted_one", "Extracted {n} skill from your CV. Skills from any earlier upload were replaced.") : t("cv_extracted", "Extracted {n} skills from your CV. Skills from any earlier upload were replaced.")).replace("{n}", result.extracted_count)}</p></div></div>`;
    }
    loadSkillProfile();
  } catch (err) {
    showError(status, err.message);
  } finally {
    dropzone.removeAttribute("aria-disabled");
  }
}

const manualInput = document.getElementById("manual-skill-input");
manualInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && manualInput.value.trim()) {
    e.preventDefault();
    addPending(manualInput.value);
    manualInput.value = "";
  }
});

function addPending(raw) {
  raw.split(",").map((s) => s.trim()).filter(Boolean).forEach((s) => {
    if (!pendingManualSkills.some((p) => p.toLowerCase() === s.toLowerCase())) pendingManualSkills.push(s);
  });
  renderPendingChips();
}

// Remove controls are real buttons with a name, so they can be reached and
// understood without a mouse; a bare "×" span was neither.
function removeButton(label, attrs) {
  return `<button type="button" class="chip-remove" aria-label="${escapeHtml(t("sk_remove", "Remove {name}").replace("{name}", label))}" ${attrs}>×</button>`;
}

function renderPendingChips() {
  const el = document.getElementById("manual-chip-preview");
  el.innerHTML = pendingManualSkills.map((s, i) =>
    `<span class="chip">${escapeHtml(s)} ${removeButton(s, `data-pending="${i}"`)}</span>`
  ).join("");
}

document.getElementById("manual-chip-preview").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-pending]");
  if (!btn) return;
  pendingManualSkills.splice(Number(btn.dataset.pending), 1);
  renderPendingChips();
  manualInput.focus();
});

async function submitManualSkills(button) {
  if (manualInput.value.trim()) { addPending(manualInput.value); manualInput.value = ""; }
  if (!pendingManualSkills.length) {
    setFieldError(manualInput, t("sk_type_first", "Type a skill first, then press Enter or Add Skills."));
    manualInput.focus();
    return;
  }
  setFieldError(manualInput, "");
  await withBusy(button, async () => {
    try {
      const { added } = await api("/api/profile/skills/manual", { method: "POST", body: JSON.stringify({ skills: pendingManualSkills }) });
      toast((added.length === 1 ? t("sk_added_one", "{n} skill added") : t("sk_added", "{n} skills added")).replace("{n}", added.length));
      pendingManualSkills = [];
      renderPendingChips();
      loadSkillProfile();
    } catch (err) {
      setFieldError(manualInput, err.message);
    }
  }, t("sk_adding", "Adding…"));
}

async function removeSkill(button, name) {
  await withBusy(button, async () => {
    try {
      await api(`/api/profile/skills/${encodeURIComponent(name)}`, { method: "DELETE" });
      loadSkillProfile();
    } catch (err) {
      toast(t("sk_remove_failed", "Couldn't remove {name}. {msg}").replace("{name}", name).replace("{msg}", err.message), "error");
    }
  }, "");
}

async function clearAllSkills(button) {
  if (!confirm(t("sk_clear_confirm", "Remove all skills from your profile? This can't be undone."))) return;
  await withBusy(button, async () => {
    try {
      await api("/api/profile/skills", { method: "DELETE" });
      toast(t("sk_cleared", "All skills cleared"));
      loadSkillProfile();
    } catch (err) {
      toast(t("sk_clear_failed", "Couldn't clear your skills. {msg}").replace("{msg}", err.message), "error");
    }
  }, t("sk_clearing", "Clearing…"));
}

async function loadSkillProfile() {
  const container = document.getElementById("category-lists");
  const labels = { technical: t("cat_technical", "Technical Skills"), soft: t("cat_soft", "Soft Skills"), tool: t("cat_tool", "Tools & Technologies"), certification: t("cat_certification", "Certifications") };
  container.classList.remove("grid", "grid-4");
  showLoading(container, t("sk_loading", "Loading your skills…"));

  let categorized;
  try {
    categorized = await api("/api/skills/categorized");
  } catch (err) {
    showError(container, t("sk_load_failed", "Couldn't load your skills. {msg}").replace("{msg}", err.message), loadSkillProfile);
    return;
  }

  clearState(container);
  const total = Object.values(categorized).reduce((a, b) => a + b.length, 0);
  if (!total) {
    showEmpty(container, t("sk_none", "No skills yet — upload a CV or add skills manually above."));
  } else {
    container.classList.add("grid", "grid-4");
    container.innerHTML = Object.keys(labels).map((cat) => `
      <div>
        <h3 style="margin:0 0 8px; font-size:1rem">${labels[cat]}</h3>
        <div>${(categorized[cat] || []).map((s) => `<span class="chip">${escapeHtml(s)} ${removeButton(s, `data-skill="${escapeHtml(s)}"`)}</span>`).join("") || `<span style="color:var(--text-muted); font-size:0.85rem">${escapeHtml(t("sk_none_yet", "None yet"))}</span>`}</div>
      </div>
    `).join("");
  }

  // Tips and the rewritten CV each load on their own, so one failing doesn't
  // blank the other.
  loadResumeTips();
  loadImprovedCV(total);
}

document.getElementById("category-lists").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-skill]");
  if (btn) removeSkill(btn, btn.dataset.skill);
});

async function loadResumeTips() {
  const list = document.getElementById("resume-tips-list");
  showLoading(list, t("tips_loading", "Reviewing your CV…"));
  try {
    const { tips } = await api("/api/skills/resume-tips");
    clearState(list);
    list.innerHTML = tips.map((tip) => `<li>${escapeHtml(tip)}</li>`).join("");
  } catch (err) {
    showError(list, t("tips_failed", "Couldn't load suggestions. {msg}").replace("{msg}", err.message), loadResumeTips);
  }
}

function skillRow(label, items) {
  if (!items || !items.length) return "";
  return `<div style="margin-bottom:10px"><strong>${label}:</strong> ${items.map(escapeHtml).join(", ")}</div>`;
}

async function loadImprovedCV(skillCount) {
  const el = document.getElementById("cv-preview");
  const pdf = document.getElementById("download-cv-pdf");
  const setPdf = (on) => {
    if (on) { pdf.href = "/api/reports/improved-cv-pdf"; pdf.removeAttribute("aria-disabled"); }
    else { pdf.removeAttribute("href"); pdf.setAttribute("aria-disabled", "true"); }
    pdf.classList.toggle("is-disabled", !on);
  };

  if (!skillCount) {
    setPdf(false);
    showEmpty(el, t("cv_draft_empty", "Add some skills and we'll draft an improved CV from them."));
    return;
  }
  showLoading(el, t("cv_drafting", "Drafting your improved CV…"));
  try {
    const { cv } = await api("/api/reports/improved-cv");
    clearState(el);
    el.innerHTML = `
      <div class="topic-item">
        <div style="margin-bottom:10px"><strong>${escapeHtml(t("cv_summary", "Professional Summary"))}:</strong><br/>${escapeHtml(cv.summary)}</div>
        ${skillRow(t("cat_technical", "Technical Skills"), cv.technical_skills)}
        ${skillRow(t("cat_tool", "Tools & Technologies"), cv.tools)}
        ${skillRow(t("cat_soft", "Soft Skills"), cv.soft_skills)}
        ${skillRow(t("cat_certification", "Certifications"), cv.certifications)}
        ${cv.project_suggestions.length ? `<div><strong>${escapeHtml(t("cv_suggested_projects", "Suggested Projects to Add"))}:</strong><ul style="margin:6px 0 0; padding-left:20px">${cv.project_suggestions.map((p) => `<li>${escapeHtml(p)}</li>`).join("")}</ul></div>` : ""}
      </div>
    `;
    setPdf(true);
  } catch (err) {
    setPdf(false);
    showError(el, t("cv_draft_failed", "Couldn't draft your CV. {msg}").replace("{msg}", err.message), () => loadImprovedCV(skillCount));
  }
}

loadSkillProfile();
