function collectStage1(form) {
  const fd = new FormData(form);
  return {
    name: fd.get("name"),
    degree: fd.get("degree"),
    major: fd.get("major"),
    cgpa: Number(fd.get("cgpa")),
    gpa_scale: fd.get("gpa_scale"),
    university_name: fd.get("university_name"),
    institution_tier: fd.get("institution_tier"),
    target_degree: fd.get("target_degree"),
    target_field: fd.get("target_field"),
    preferred_countries: String(fd.get("preferred_countries")).split(",").map((s) => s.trim()).filter(Boolean),
    target_intake: fd.get("target_intake"),
    budget_usd: Number(fd.get("budget_usd")),
    living_budget_usd: fd.get("living_budget_usd") ? Number(fd.get("living_budget_usd")) : null,
    scholarship_seeking: !!fd.get("scholarship_seeking"),
  };
}

function prefillStage1(form, profile) {
  setField(form, "degree", profile.degree);
  setField(form, "major", profile.major || profile.target_field);
  setField(form, "cgpa", profile.cgpa);
  setField(form, "gpa_scale", profile.gpa_scale);
  setField(form, "university_name", profile.university_name);
  setField(form, "institution_tier", profile.institution_tier);
  setField(form, "target_degree", profile.target_degree);
  setField(form, "target_field", profile.target_field);
  setField(form, "preferred_countries", profile.preferred_countries);
  setField(form, "target_intake", profile.target_intake);
  setField(form, "budget_usd", profile.budget_usd);
  setField(form, "living_budget_usd", profile.living_budget_usd);
  if (profile.scholarship_seeking) setField(form, "scholarship_seeking", true);
}

async function initStage1() {
  const form = document.getElementById("form");
  const planId = await ensurePlan();
  const profile = await loadSavedProfile(planId);
  prefillStage1(form, profile);

  document.getElementById("submit-btn").onclick = async () => {
    if (!form.reportValidity()) return;
    await submitStage({
      stage: 1,
      payload: collectStage1(form),
      nextTool: "show_stage2_widget",
      nextMessage: "Stage 1 saved. Continuing with Stage 2 — exam scores and documents.",
    });
  };
}

initStage1().catch((err) => setStatus(err.message, true));
