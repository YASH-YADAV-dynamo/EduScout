function collectStage2(form) {
  const fd = new FormData(form);
  return {
    exams: {
      ielts_overall: Number(fd.get("ielts_overall")) || 0,
      ielts_expected: Number(fd.get("ielts_expected")) || 0,
      toefl_total: Number(fd.get("toefl_total")) || 0,
      gre_taken: fd.get("gre_taken") === "true",
      gre_verbal: Number(fd.get("gre_verbal")) || 0,
      gre_quant: Number(fd.get("gre_quant")) || 0,
    },
  };
}

function prefillStage2(form, profile) {
  const exams = profile.exams || {};
  setField(form, "ielts_overall", exams.ielts_overall);
  setField(form, "ielts_expected", exams.ielts_expected);
  setField(form, "toefl_total", exams.toefl_total);
  setField(form, "gre_taken", exams.gre_taken ? "true" : "false");
  setField(form, "gre_verbal", exams.gre_verbal);
  setField(form, "gre_quant", exams.gre_quant);
}

async function initStage2() {
  const form = document.getElementById("form");
  const planId = await ensurePlan();
  const profile = await loadSavedProfile(planId);
  prefillStage2(form, profile);

  document.getElementById("submit-btn").onclick = async () => {
    await submitStage({
      stage: 2,
      payload: collectStage2(form),
      nextTool: "show_stage3_widget",
      nextMessage: "Stage 2 saved. Continuing with Stage 3 — experience and preferences.",
    });
  };
}

initStage2().catch((err) => setStatus(err.message, true));
