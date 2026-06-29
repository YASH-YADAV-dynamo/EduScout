function collectStage3(form) {
  const fd = new FormData(form);
  return {
    work: {
      jobs: [{ months: Number(fd.get("full_time_months")) || 0 }],
      internships: [{ months: Number(fd.get("internship_months")) || 0 }],
    },
    research: {
      has_papers: fd.get("has_papers") === "true",
      conference_tier: fd.get("conference_tier"),
    },
    extracurriculars: { leadership_roles: fd.get("leadership_roles") === "true" },
    campus_type: fd.get("campus_type"),
    post_study_goal: fd.get("post_study_goal"),
    visa_constraints: fd.get("visa_constraints"),
    funding_open: !!fd.get("funding_open"),
  };
}

function prefillStage3(form, profile) {
  const work = profile.work || {};
  const jobs = work.jobs || [];
  const internships = work.internships || [];
  setField(form, "full_time_months", jobs[0]?.months ?? 0);
  setField(form, "internship_months", internships[0]?.months ?? 0);
  const research = profile.research || {};
  setField(form, "has_papers", research.has_papers ? "true" : "false");
  setField(form, "conference_tier", research.conference_tier);
  const extra = profile.extracurriculars || {};
  setField(form, "leadership_roles", extra.leadership_roles ? "true" : "false");
  setField(form, "campus_type", profile.campus_type);
  setField(form, "post_study_goal", profile.post_study_goal);
  setField(form, "visa_constraints", profile.visa_constraints);
  if (profile.funding_open) setField(form, "funding_open", true);
}

async function initStage3() {
  const form = document.getElementById("form");
  const payload = readPayload();
  const planId = await ensurePlan();
  const profile = await loadSavedProfile(planId);
  prefillStage3(form, profile);
  const esid = payload.esid ?? "";

  document.getElementById("submit-btn").onclick = async () => {
    const btn = document.getElementById("submit-btn");
    const stage3 = collectStage3(form);
    btn.disabled = true;
    btn.textContent = "Saving…";
    setStatus("Saving profile…", false);

    try {
      await postJson(`/api/onboarding/stage3`, { plan_id: planId, ...stage3 });
      if (bridge.callTool) {
        await bridge.callTool("save_onboarding_stage", { plan_id: planId, stage: 3, data: stage3 }).catch(() => {});
      }
      const result = await postJson("/api/onboarding/submit_all", {
        plan_id: planId,
        esid,
        stage3,
        email: payload.email,
      });

      setStatus(`Profile complete (${result.profile_completeness}%).`, false);
      btn.textContent = "Saved ✓";
      bridge.sendFollowUpMessage?.({
        prompt: `Profile complete! (${result.profile_completeness}% complete). Your ESID is ${result.esid}. Now find my best college matches.`,
      });
      if (bridge.callTool) {
        await bridge.callTool("search_universities", { plan_id: planId });
      }
    } catch (err) {
      setStatus(err.message || "Submit failed", true);
      btn.disabled = false;
      btn.textContent = "Submit profile";
    }
  };
}

initStage3().catch((err) => setStatus(err.message, true));
