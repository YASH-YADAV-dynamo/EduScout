const bridge = window.openai ?? {};

function readPayload() {
  const output = bridge.toolOutput;
  if (!output) return {};
  if (output.structuredContent && typeof output.structuredContent === "object") {
    return output.structuredContent;
  }
  if (typeof output === "object" && !Array.isArray(output)) {
    return output;
  }
  return {};
}

const data = { ...readPayload(), ...(bridge.toolInput ?? {}) };

const profile = data.profile ?? {};
const tasks = data.tasks ?? [];
const universities = data.universities ?? [];
const stats = data.stats ?? {};
const today = new Date().toISOString().slice(0, 10);

document.getElementById("plan-title").textContent = data.plan_title ?? "Study Plan";

const metaParts = [];
if (profile.region) metaParts.push(profile.region);
if (profile.target_intake) metaParts.push(`Intake ${profile.target_intake}`);
if (data.plan_status) metaParts.push(data.plan_status.replace("_", " "));
document.getElementById("plan-meta").textContent =
  metaParts.join(" · ") || "Complete your profile to personalize this plan";

const chipsEl = document.getElementById("profile-chips");
const chipFields = [
  ["degree", profile.degree],
  ["major", profile.major],
  ["CGPA", profile.cgpa],
  ["budget", profile.budget_range],
  ["priority", profile.priority],
];
for (const [, value] of chipFields) {
  if (!value) continue;
  const chip = document.createElement("span");
  chip.className = "profile-chip";
  chip.textContent = value;
  chipsEl.appendChild(chip);
}
if (!chipsEl.children.length) {
  chipsEl.innerHTML = '<span class="profile-chip">Profile not filled — open the planning widget</span>';
}

document.getElementById("stat-tasks").textContent = stats.tasks_total ?? tasks.length;
document.getElementById("stat-pending").textContent =
  stats.tasks_pending ?? tasks.filter((t) => t.status === "pending").length;
document.getElementById("stat-unis").textContent = stats.universities_total ?? universities.length;

const tasksEl = document.getElementById("tasks");
const tasksEmpty = document.getElementById("tasks-empty");
document.getElementById("tasks-count").textContent = tasks.length ? `${tasks.length} total` : "";

if (!tasks.length) {
  tasksEmpty.hidden = false;
} else {
  tasksEmpty.hidden = true;
  const sorted = [...tasks].sort((a, b) => {
    if (!a.due_date) return 1;
    if (!b.due_date) return -1;
    return a.due_date.localeCompare(b.due_date);
  });
  for (const task of sorted.slice(0, 6)) {
    const li = document.createElement("li");
    const overdue = task.status === "pending" && task.due_date && task.due_date < today;
    if (overdue) li.className = "overdue";

    const title = document.createElement("span");
    title.textContent = task.title;
    li.appendChild(title);

    const right = document.createElement("span");
    if (task.due_date) {
      const date = document.createElement("span");
      date.className = "task-date";
      date.textContent = task.due_date;
      right.appendChild(date);
    }
    if (task.status !== "pending") {
      const badge = document.createElement("span");
      badge.className = "badge";
      badge.textContent = task.status;
      right.appendChild(badge);
    }
    li.appendChild(right);
    tasksEl.appendChild(li);
  }
}

const uniEl = document.getElementById("universities");
const unisEmpty = document.getElementById("unis-empty");
document.getElementById("unis-count").textContent = universities.length ? `${universities.length} total` : "";

if (!universities.length) {
  unisEmpty.hidden = false;
} else {
  unisEmpty.hidden = true;
  const groups = { reach: [], target: [], safety: [] };
  for (const uni of universities) {
    const cat = (uni.category || "target").toLowerCase();
    if (groups[cat]) groups[cat].push(uni.university_name);
    else groups.target.push(uni.university_name);
  }
  for (const [cat, names] of Object.entries(groups)) {
    if (!names.length) continue;
    const group = document.createElement("div");
    group.className = "uni-group";
    group.innerHTML = `<div class="uni-group-title">${cat}</div>`;
    const ul = document.createElement("ul");
    for (const name of names) {
      const li = document.createElement("li");
      li.textContent = name;
      ul.appendChild(li);
    }
    group.appendChild(ul);
    uniEl.appendChild(group);
  }
}

const linkCode = data.link_code ?? "------";
document.getElementById("link-code").textContent = linkCode;

document.getElementById("copy-btn").onclick = async () => {
  try {
    await navigator.clipboard.writeText(linkCode);
    document.getElementById("copy-btn").textContent = "Copied";
    setTimeout(() => {
      document.getElementById("copy-btn").textContent = "Copy";
    }, 1500);
  } catch {
    document.getElementById("copy-btn").textContent = "Copy failed";
  }
};
