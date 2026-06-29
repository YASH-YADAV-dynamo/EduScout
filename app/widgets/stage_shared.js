const bridge = window.openai ?? {};

function readPayload() {
  const output = bridge.toolOutput;
  if (!output) return {};
  if (output.structuredContent && typeof output.structuredContent === "object") return output.structuredContent;
  if (typeof output === "object" && !Array.isArray(output)) return output;
  return {};
}

function resolvePlanId() {
  const payload = readPayload();
  const state = bridge.widgetState ?? {};
  return state.plan_id ?? payload.plan_id ?? payload.profile?.plan_id ?? null;
}

function persistState(extra = {}) {
  bridge.setWidgetState?.({ ...(bridge.widgetState ?? {}), ...extra });
}

async function ensurePlan(region = "Europe") {
  let planId = resolvePlanId();
  if (planId) {
    persistState({ plan_id: planId });
    return planId;
  }
  let data = null;
  if (bridge.callTool) {
    data = await bridge.callTool("start_planning_widget", { region });
    data = data?.structuredContent ?? data;
  }
  if (!data?.plan_id) {
    const res = await fetch("/api/onboarding/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ region }),
    });
    if (!res.ok) throw new Error("Could not create plan");
    data = await res.json();
  }
  planId = data.plan_id;
  persistState({ plan_id: planId });
  return planId;
}

async function loadSavedProfile(planId) {
  const payload = readPayload();
  if (payload.profile && Object.keys(payload.profile).length) return payload.profile;
  try {
    const res = await fetch(`/api/onboarding/profile/${planId}`);
    if (res.ok) {
      const data = await res.json();
      return data.profile ?? {};
    }
  } catch {
    /* offline / same-origin blocked */
  }
  return {};
}

function setStatus(message, isError = false) {
  const el = document.getElementById("status");
  if (!el) return;
  el.hidden = !message;
  el.textContent = message || "";
  el.classList.toggle("error", isError);
}

function setField(form, name, value) {
  if (value === undefined || value === null || value === "") return;
  const field = form.elements.namedItem(name);
  if (!field) return;
  if (field.type === "checkbox") field.checked = !!value;
  else if (Array.isArray(value)) field.value = value.join(", ");
  else field.value = String(value);
}

async function postJson(path, payload) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.detail || data.message || data.error || `Request failed (${res.status})`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data;
}

async function submitStage({ stage, payload, nextTool, nextMessage, buttonLabel = "Submit" }) {
  const btn = document.getElementById("submit-btn");
  if (!btn) throw new Error("Missing submit button");
  const defaultLabel = btn.dataset.defaultLabel || btn.textContent;
  btn.dataset.defaultLabel = defaultLabel;
  btn.disabled = true;
  btn.textContent = "Saving…";
  setStatus("Saving…", false);

  try {
    const planId = await ensurePlan();
    payload.plan_id = planId;
    const result = await postJson(`/api/onboarding/stage${stage}`, payload);
    persistState({ plan_id: planId, stage_complete: stage });

    if (bridge.callTool) {
      await bridge.callTool("save_onboarding_stage", { plan_id: planId, stage, data: payload }).catch(() => {});
    }

    setStatus(`Stage ${stage} saved.`, false);
    btn.textContent = "Saved ✓";

    if (nextTool && bridge.callTool) {
      await bridge.callTool(nextTool, { plan_id: planId });
    }
    if (nextMessage) {
      bridge.sendFollowUpMessage?.({ prompt: nextMessage });
    }
    return result;
  } catch (err) {
    setStatus(err.message || "Save failed", true);
    btn.disabled = false;
    btn.textContent = defaultLabel;
    throw err;
  }
}
