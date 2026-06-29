const STEPS = [
  { id: "region", stage: 1, title: "Target region", subtitle: "Stage 1 — Academic", type: "choice", options: [
    { value: "Europe", label: "Europe", hint: "Germany, Netherlands, UK…" },
    { value: "North America", label: "North America", hint: "USA, Canada" },
    { value: "Asia Pacific", label: "Asia Pacific", hint: "Singapore, Australia" },
    { value: "USA", label: "USA", hint: "United States" },
    { value: "Canada", label: "Canada", hint: "" },
    { value: "UK", label: "UK", hint: "" },
    { value: "Germany", label: "Germany", hint: "" },
    { value: "Other", label: "Other", hint: "" },
  ]},
  { id: "target_degree", stage: 1, title: "Target degree", subtitle: "Stage 1 — Academic", type: "choice", options: [
    { value: "MS", label: "MS", hint: "Master of Science" },
    { value: "MBA", label: "MBA", hint: "" },
    { value: "PhD", label: "PhD", hint: "" },
    { value: "MEng", label: "MEng", hint: "" },
    { value: "Master's", label: "Master's (general)", hint: "" },
    { value: "Bachelor's", label: "Bachelor's", hint: "" },
  ]},
  { id: "major", stage: 1, title: "Current / target field", subtitle: "Stage 1 — Academic", type: "text", placeholder: "e.g. Computer Science", chips: ["Computer Science", "AI / ML", "Finance", "Engineering"] },
  { id: "cgpa", stage: 1, title: "CGPA or GPA", subtitle: "Stage 1 — Academic", type: "number", placeholder: "8.2 or 3.7", hint: "Out of 10 or 4.0 scale" },
  { id: "university_name", stage: 1, title: "Your university name", subtitle: "Stage 1 — Academic", type: "text", placeholder: "e.g. IIT Delhi, State University" },
  { id: "institution_tier", stage: 1, title: "Institution ranking tier", subtitle: "Stage 1 — Academic", type: "choice", options: [
    { value: "top_50", label: "Top 50 globally/nationally", hint: "" },
    { value: "51_200", label: "Rank 51–200", hint: "" },
    { value: "201_500", label: "Rank 201–500", hint: "" },
    { value: "500_plus", label: "500+", hint: "" },
    { value: "not_ranked", label: "Not ranked", hint: "" },
  ]},
  { id: "ielts_expected", stage: 2, title: "IELTS score (actual or expected)", subtitle: "Stage 2 — Tests", type: "number", placeholder: "7.0", hint: "Overall band; use expected if not taken yet" },
  { id: "gre_taken", stage: 2, title: "Have you taken the GRE?", subtitle: "Stage 2 — Tests", type: "choice", options: [
    { value: "yes", label: "Yes", hint: "" },
    { value: "no", label: "No / planning to", hint: "" },
    { value: "waived", label: "Waived for my programs", hint: "" },
  ]},
  { id: "has_papers", stage: 3, title: "Published research papers?", subtitle: "Stage 3 — Research", type: "choice", options: [
    { value: "yes", label: "Yes", hint: "Journal or conference" },
    { value: "no", label: "No", hint: "Thesis or projects only" },
  ]},
  { id: "full_time_months", stage: 4, title: "Full-time work experience (months)", subtitle: "Stage 4 — Work", type: "number", placeholder: "0", hint: "0 if none" },
  { id: "leadership_roles", stage: 5, title: "Leadership roles?", subtitle: "Stage 5 — Extracurriculars", type: "choice", options: [
    { value: "yes", label: "Yes", hint: "Club president, team lead…" },
    { value: "no", label: "No", hint: "" },
  ]},
  { id: "budget_usd", stage: 6, title: "Annual tuition budget (USD)", subtitle: "Stage 6 — Finance", type: "number", placeholder: "30000", hint: "Tuition only per year" },
  { id: "budget_range", stage: 6, title: "Total budget band (optional)", subtitle: "Stage 6 — Finance", type: "choice", options: [
    { value: "Under ₹10L", label: "Under ₹10L", hint: "" },
    { value: "₹10L – ₹20L", label: "₹10L – ₹20L", hint: "" },
    { value: "₹20L – ₹40L", label: "₹20L – ₹40L", hint: "" },
    { value: "₹40L+", label: "₹40L+", hint: "" },
  ]},
  { id: "target_intake", stage: 7, title: "Target intake", subtitle: "Stage 7 — Preferences", type: "choice", options: [
    { value: "Fall 2026", label: "Fall 2026", hint: "" },
    { value: "Fall 2027", label: "Fall 2027", hint: "" },
    { value: "Spring 2027", label: "Spring 2027", hint: "" },
    { value: "2028", label: "2028+", hint: "" },
  ]},
  { id: "campus_type", stage: 7, title: "Campus environment", subtitle: "Stage 7 — Preferences", type: "choice", options: [
    { value: "urban", label: "Urban", hint: "" },
    { value: "suburban", label: "Suburban", hint: "" },
    { value: "rural", label: "Rural", hint: "" },
    { value: "no_preference", label: "No preference", hint: "" },
  ]},
  { id: "priority", stage: 7, title: "Top priority", subtitle: "Stage 7 — Preferences", type: "choice", options: [
    { value: "cheapest", label: "Cheapest", hint: "" },
    { value: "best_universities", label: "Best universities", hint: "" },
    { value: "salary", label: "Job outcomes", hint: "" },
    { value: "immigration", label: "Immigration / PR", hint: "" },
  ]},
  { id: "post_study_goal", stage: 7, title: "Post-study goal", subtitle: "Stage 7 — Preferences", type: "text", placeholder: "Job abroad, research career, return home…" },
  { id: "review", stage: 7, title: "Review & submit", subtitle: "Confirm your profile", type: "review" },
];

const bridge = window.openai ?? {};
const savedState = bridge.widgetState ?? {};

function readToolPayload() {
  const output = bridge.toolOutput;
  if (!output) return {};
  if (output.structuredContent && typeof output.structuredContent === "object") return output.structuredContent;
  if (typeof output === "object" && !Array.isArray(output)) return output;
  return {};
}

function resolvePlanId() {
  const payload = readToolPayload();
  const input = bridge.toolInput ?? {};
  return savedState.plan_id ?? payload.plan_id ?? input.plan_id ?? payload.profile?.plan_id ?? null;
}

let planId = resolvePlanId();
let currentStep = savedState.step ?? 0;
let form = { region: "Europe", ...(readToolPayload().profile ?? {}), ...(savedState.form ?? {}) };
let submitting = false;
let initialized = false;

const stepTitle = document.getElementById("step-title");
const stepIndicator = document.getElementById("step-indicator");
const stepContent = document.getElementById("step-content");
const progressBar = document.getElementById("progress-bar");
const backBtn = document.getElementById("back-btn");
const nextBtn = document.getElementById("next-btn");
const statusEl = document.getElementById("status");

function persistState() {
  bridge.setWidgetState?.({ step: currentStep, form, plan_id: planId });
}

function showStatus(message, isError = false) {
  statusEl.hidden = false;
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function buildPayload(complete = false) {
  const countries = form.region ? [form.region] : null;
  return {
    plan_id: planId,
    complete,
    region: form.region ?? null,
    degree: form.target_degree === "Bachelor's" ? "Bachelor's" : form.degree ?? "Master's",
    target_degree: form.target_degree ?? null,
    target_field: form.major ?? null,
    major: form.major ?? null,
    cgpa: form.cgpa ? Number(form.cgpa) : null,
    university_name: form.university_name ?? null,
    institution_tier: form.institution_tier ?? null,
    budget_range: form.budget_range ?? null,
    budget_usd: form.budget_usd ? Number(form.budget_usd) : null,
    target_intake: form.target_intake ?? null,
    priority: form.priority ?? null,
    preferred_countries: countries,
    ielts_expected: form.ielts_expected ? Number(form.ielts_expected) : null,
    gre_taken: form.gre_taken === "yes",
    has_papers: form.has_papers === "yes",
    full_time_months: form.full_time_months ? Number(form.full_time_months) : 0,
    scholarship_seeking: false,
    campus_type: form.campus_type ?? null,
    post_study_goal: form.post_study_goal ?? null,
  };
}

async function callBackendTool(toolName, payload) {
  if (!bridge.callTool) return null;
  try {
    const result = await bridge.callTool(toolName, payload);
    const data = result?.structuredContent ?? result;
    if (!data || typeof data !== "object" || data.error) return null;
    if (data.plan_id) return data;
    return null;
  } catch {
    return null;
  }
}

async function callBackendHttp(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Save failed (${response.status})`);
  return response.json();
}

async function ensurePlanId() {
  if (planId) { persistState(); return planId; }
  showStatus("Creating your plan…", false);
  let data = (await callBackendTool("start_planning_widget", { region: form.region || "Europe" }))
    ?? (await callBackendHttp("/api/onboarding/start", { region: form.region || "Europe" }));
  planId = data?.plan_id ?? null;
  if (!planId) { showStatus("Could not create a plan.", true); return null; }
  if (data.profile) form = { ...form, ...data.profile };
  persistState();
  statusEl.hidden = true;
  return planId;
}

async function saveProgress(complete = false) {
  if (!(await ensurePlanId())) return null;
  const payload = buildPayload(complete);
  try {
    let data = (await callBackendTool(complete ? "submit_onboarding" : "save_onboarding_step", payload))
      ?? (await callBackendHttp(complete ? "/api/onboarding/submit" : "/api/onboarding/save", payload));
    if (data?.error) { showStatus(data.error, true); return null; }
    return data;
  } catch (err) {
    showStatus(err?.message ?? "Save failed.", true);
    return null;
  }
}

function getStepValue(step) {
  if (step.type === "review") return true;
  const value = form[step.id];
  if (value === undefined || value === null || String(value).trim() === "") {
    if (step.id === "budget_range" || step.id === "full_time_months") return true;
    return null;
  }
  return value;
}

function renderChoiceStep(step) {
  const grid = document.createElement("div");
  grid.className = "option-grid";
  for (const option of step.options) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "option-card" + (form[step.id] === option.value ? " selected" : "");
    card.innerHTML = `<strong>${option.label}</strong>${option.hint ? `<span>${option.hint}</span>` : ""}`;
    card.onclick = () => { form[step.id] = option.value; persistState(); render(); };
    grid.appendChild(card);
  }
  stepContent.appendChild(grid);
}

function renderTextStep(step) {
  const label = document.createElement("label");
  label.className = "field-label";
  const input = document.createElement("input");
  input.className = "text-input";
  input.type = "text";
  input.placeholder = step.placeholder ?? "";
  input.value = form[step.id] ?? "";
  input.oninput = (e) => { form[step.id] = e.target.value; persistState(); };
  label.appendChild(input);
  stepContent.appendChild(label);
  if (step.chips) {
    const chips = document.createElement("div");
    chips.className = "chip-row";
    for (const chip of step.chips) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip" + (form[step.id] === chip ? " selected" : "");
      btn.textContent = chip;
      btn.onclick = () => { form[step.id] = chip; persistState(); render(); };
      chips.appendChild(btn);
    }
    stepContent.appendChild(chips);
  }
}

function renderNumberStep(step) {
  const input = document.createElement("input");
  input.className = "text-input";
  input.type = "number";
  input.step = "0.01";
  input.placeholder = step.placeholder ?? "";
  input.value = form[step.id] ?? "";
  input.oninput = (e) => { form[step.id] = e.target.value; persistState(); };
  stepContent.appendChild(input);
  if (step.hint) {
    const hint = document.createElement("p");
    hint.className = "hint";
    hint.textContent = step.hint;
    stepContent.appendChild(hint);
  }
}

function renderReviewStep() {
  const list = document.createElement("ul");
  list.className = "summary-list";
  for (const step of STEPS) {
    if (step.type === "review" || !form[step.id]) continue;
    const li = document.createElement("li");
    li.innerHTML = `<span>${step.title}</span><strong>${form[step.id]}</strong>`;
    list.appendChild(li);
  }
  stepContent.appendChild(list);
}

function renderSuccess(data) {
  stepTitle.textContent = "Profile saved";
  stepIndicator.textContent = "Next: profile scoring & university research";
  progressBar.style.width = "100%";
  stepContent.innerHTML = `<div class="success-box"><pre>${data.summary ?? ""}</pre></div>`;
  backBtn.hidden = true;
  nextBtn.hidden = true;
  showStatus(data.message ?? "Submitted.", false);
}

function render() {
  const step = STEPS[currentStep];
  stepTitle.textContent = step.title;
  stepIndicator.textContent = `Step ${currentStep + 1}/${STEPS.length} · ${step.subtitle}`;
  progressBar.style.width = `${((currentStep + 1) / STEPS.length) * 100}%`;
  backBtn.hidden = currentStep === 0;
  nextBtn.textContent = currentStep === STEPS.length - 1 ? "Submit profile" : "Continue";
  nextBtn.disabled = submitting;
  stepContent.innerHTML = "";
  if (step.type === "choice") renderChoiceStep(step);
  else if (step.type === "text") renderTextStep(step);
  else if (step.type === "number") renderNumberStep(step);
  else if (step.type === "review") renderReviewStep(step);
}

async function triggerRoadmapGeneration(data) {
  const prompt = data.next_prompt ?? `Profile saved (plan #${data.plan_id}). Run check_profile_ready and search workflow.`;
  if (bridge.sendFollowUpMessage) await bridge.sendFollowUpMessage({ prompt });
}

backBtn.onclick = () => { if (currentStep > 0) { currentStep--; persistState(); render(); } };

nextBtn.onclick = async () => {
  const step = STEPS[currentStep];
  if (!getStepValue(step)) { showStatus("Please complete this step.", true); return; }
  statusEl.hidden = true;
  submitting = true;
  render();
  let finished = false;
  try {
    if (currentStep < STEPS.length - 1) {
      await saveProgress(false);
      currentStep++;
      persistState();
    } else {
      const data = await saveProgress(true);
      if (!data) return;
      finished = true;
      renderSuccess(data);
      await triggerRoadmapGeneration(data);
    }
  } finally {
    submitting = false;
    if (!finished) render();
  }
};

(async function boot() {
  if (initialized) return;
  initialized = true;
  await ensurePlanId();
  render();
})();
