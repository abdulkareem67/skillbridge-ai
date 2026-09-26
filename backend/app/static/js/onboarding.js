// Three-step setup: location -> target role -> skills.
//
// Resumes wherever the person left off, so closing the tab halfway through and
// coming back never makes them redo a step. The dashboard sends people here
// until they have a role and at least one skill (see onboarding.py), so step 3
// can't be finished without actually adding a skill.
(function () {
  const markets = window.__SB_MARKETS__ || [];
  const steps = [...document.querySelectorAll(".ob-step")];
  const markers = [...document.querySelectorAll("[data-step-marker]")];
  const loading = document.getElementById("ob-loading");
  const finish = document.getElementById("ob-finish");
  let disciplines = {};
  let rolesLoaded = false;
  let hasSkills = false;

  function go(n, { focus = true } = {}) {
    steps.forEach((s) => { s.hidden = s.dataset.step !== String(n); });
    markers.forEach((m) => {
      const k = Number(m.dataset.stepMarker);
      m.classList.toggle("is-done", k < n);
      m.classList.toggle("is-current", k === n);
      if (k === n) m.setAttribute("aria-current", "step"); else m.removeAttribute("aria-current");
    });
    if (n === 2) loadRoles();
    // Move focus to the new heading so keyboard and screen-reader users land on
    // the step they just opened rather than on a button that no longer exists.
    if (focus) document.getElementById(`ob-h${n}`).focus();
  }

  document.querySelectorAll("[data-back]").forEach((b) => b.addEventListener("click", () => go(Number(b.dataset.back))));

  /* ---- Step 1: location ------------------------------------------------ */
  const country = document.getElementById("ob-country");
  const city = document.getElementById("ob-city");
  const cityList = document.getElementById("ob-cities");
  const countryList = document.getElementById("ob-countries");

  // Every country name the browser knows, in the reader's own language. The
  // markets we have dedicated job boards for are already listed first.
  (function addAllCountries() {
    if (!("DisplayNames" in Intl)) return;
    let names;
    try { names = new Intl.DisplayNames([navigator.language || "en"], { type: "region" }); } catch (e) { return; }
    // Codes that are real in the registry but are not countries you'd live in.
    const notCountries = new Set(["EU", "EZ", "UN", "ZZ", "QO", "AC", "CP", "DG", "EA", "IC", "TA", "CQ"]);
    const known = new Set(markets.map((m) => m.name.toLowerCase()));
    const found = [];
    for (let a = 65; a <= 90; a++) {
      for (let b = 65; b <= 90; b++) {
        const code = String.fromCharCode(a, b);
        if (notCountries.has(code) || code[0] === "X") continue;
        const name = names.of(code);
        // An unknown code comes back unchanged, which is how we tell real ones apart.
        if (name && name !== code && !known.has(name.toLowerCase())) found.push(name);
      }
    }
    found.sort((x, y) => x.localeCompare(y));
    countryList.insertAdjacentHTML("beforeend", found.map((n) => `<option value="${escapeHtml(n)}"></option>`).join(""));
  })();

  function refreshCities() {
    const m = markets.find((mk) => mk.name.toLowerCase() === country.value.trim().toLowerCase());
    cityList.innerHTML = m ? m.cities.map((c) => `<option value="${escapeHtml(c)}"></option>`).join("") : "";
  }
  country.addEventListener("input", refreshCities);

  document.getElementById("ob-save-location").addEventListener("click", (e) => {
    // Not `t`: that name is the translation helper, and shadowing it here made
    // every t(...) call below throw, so this button silently did nothing.
    const c = country.value.trim();
    const town = city.value.trim();
    if (!c && !town) {
      setFieldError(country, t("ob_need_country", "Enter a country, or choose “Skip” below."));
      country.focus();
      return;
    }
    setFieldError(country, "");
    const location = c && town ? `${town}, ${c}` : c || town;
    withBusy(e.currentTarget, async () => {
      try {
        await api("/api/profile/location", { method: "POST", body: JSON.stringify({ location }) });
        go(2);
      } catch (err) {
        setFieldError(country, err.message);
      }
    }, t("ob_saving", "Saving…"));
  });

  document.getElementById("ob-skip-location").addEventListener("click", () => go(2));

  /* ---- Step 2: target role --------------------------------------------- */
  const rolesState = document.getElementById("ob-roles-state");
  const rolesForm = document.getElementById("ob-roles-form");
  const dSel = document.getElementById("ob-discipline");
  const rSel = document.getElementById("ob-role");
  let pendingRole = null;

  function fillRoles(discipline, selected) {
    rSel.innerHTML = (disciplines[discipline] || [])
      .map((r) => `<option value="${escapeHtml(r)}" ${r === selected ? "selected" : ""}>${escapeHtml(r)}</option>`)
      .join("");
  }

  async function loadRoles() {
    if (rolesLoaded) return;
    showLoading(rolesState, t("ob_loading_tracks", "Loading career tracks…"));
    rolesForm.hidden = true;
    try {
      disciplines = (await api("/api/skills/disciplines")).disciplines;
      const names = Object.keys(disciplines);
      if (!names.length) { showEmpty(rolesState, t("ob_no_tracks", "No career tracks are configured yet.")); return; }
      const current = names.find((d) => disciplines[d].includes(pendingRole)) || names[0];
      dSel.innerHTML = names.map((d) => `<option value="${escapeHtml(d)}" ${d === current ? "selected" : ""}>${escapeHtml(d)}</option>`).join("");
      dSel.onchange = () => fillRoles(dSel.value);
      fillRoles(current, pendingRole);
      rolesState.innerHTML = "";
      clearState(rolesState);
      rolesForm.hidden = false;
      rolesLoaded = true;
    } catch (err) {
      showError(rolesState, err.message, loadRoles);
    }
  }

  document.getElementById("ob-save-role").addEventListener("click", (e) => {
    if (!rolesLoaded || !rSel.value) return;
    withBusy(e.currentTarget, async () => {
      try {
        await api("/api/profile/target-role", { method: "POST", body: JSON.stringify({ role: rSel.value }) });
        go(3);
      } catch (err) {
        toast(err.message, "error");
      }
    }, t("ob_saving", "Saving…"));
  });

  /* ---- Step 3: skills --------------------------------------------------- */
  const result = document.getElementById("ob-skills-result");
  const cvInput = document.getElementById("ob-cv");
  const manual = document.getElementById("ob-manual");

  function setFinishEnabled(on) {
    hasSkills = on;
    finish.setAttribute("aria-disabled", String(!on));
    finish.classList.toggle("is-disabled", !on);
  }
  // A link can't be `disabled`, so block it by hand until there is a skill.
  finish.addEventListener("click", (e) => {
    if (!hasSkills) { e.preventDefault(); toast(t("ob_need_skill", "Add at least one skill first."), "error"); }
  });

  function showSkills(names, lead) {
    result.innerHTML = `<div class="state-box state-success" role="status">${icon("check-circle", 20)}<div class="state-text"><p>${escapeHtml(lead)}</p><div>${
      names.slice(0, 24).map((n) => `<span class="chip chip-matched">${escapeHtml(n)}</span>`).join("")
    }</div></div></div>`;
    setFinishEnabled(true);
  }

  cvInput.addEventListener("change", async () => {
    const file = cvInput.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { showError(result, t("ob_too_big", "That file is over 5 MB. Try a smaller PDF or a DOCX.")); return; }
    showLoading(result, t("ob_reading", "Reading {name}…").replace("{name}", file.name));
    const fd = new FormData();
    fd.append("file", file);
    try {
      const r = await api("/api/profile/cv-upload", { method: "POST", body: fd, timeout: 45000 });
      if (!r.extracted_count) {
        showEmpty(result, t("ob_no_skills_found", "We couldn't find any skills we recognise in that file. If it's a scanned PDF, try a DOCX — or type a few skills above."));
      } else {
        showSkills(r.skills.map((s) => s.skill_name), (r.extracted_count === 1 ? t("ob_found_skill", "Found {n} skill in your CV.") : t("ob_found_skills", "Found {n} skills in your CV.")).replace("{n}", r.extracted_count));
      }
    } catch (err) {
      showError(result, err.message);
    } finally {
      cvInput.value = "";
    }
  });

  document.getElementById("ob-add-manual").addEventListener("click", (e) => {
    const skills = manual.value.split(",").map((s) => s.trim()).filter(Boolean);
    if (!skills.length) { setFieldError(manual, t("ob_type_a_skill", "Type at least one skill.")); manual.focus(); return; }
    if (skills.length > 50) { setFieldError(manual, t("ob_too_many", "That's more than 50 — add the most important ones first.")); return; }
    setFieldError(manual, "");
    withBusy(e.currentTarget, async () => {
      try {
        const r = await api("/api/profile/skills/manual", { method: "POST", body: JSON.stringify({ skills }) });
        manual.value = "";
        showSkills(r.added, (r.added.length === 1 ? t("ob_added_skill", "Added {n} skill.") : t("ob_added_skills", "Added {n} skills.")).replace("{n}", r.added.length));
      } catch (err) {
        setFieldError(manual, err.message);
      }
    }, t("ob_adding", "Adding…"));
  });

  /* ---- Resume where they left off --------------------------------------- */
  async function start() {
    showLoading(loading, t("ob_loading_profile", "Loading your profile…"));
    try {
      const me = await api("/api/profile/me");
      loading.innerHTML = "";
      clearState(loading);
      if (me.location) {
        const parts = me.location.split(",").map((p) => p.trim());
        if (parts.length > 1) { city.value = parts[0]; country.value = parts.slice(1).join(", "); }
        else country.value = parts[0];
        refreshCities();
      }
      pendingRole = me.target_role;
      if (me.skills.length) setFinishEnabled(true);
      const step = !me.target_role ? (me.location ? 2 : 1) : 3;
      go(step, { focus: false });
    } catch (err) {
      showError(loading, err.message, start);
    }
  }
  setFinishEnabled(false);
  start();
})();
