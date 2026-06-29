const bridge = window.openai ?? {};

function readPayload() {
  const output = bridge.toolOutput;
  if (!output) return {};
  if (output.structuredContent && typeof output.structuredContent === "object") {
    return output.structuredContent;
  }
  if (typeof output === "object" && !Array.isArray(output)) return output;
  return {};
}

const data = { ...readPayload(), ...(bridge.toolInput ?? {}) };

document.getElementById("user-name").textContent = data.name ?? "Student";
document.getElementById("user-email").textContent = data.email ?? "";

const publicId = data.public_id ?? "SAA-------";
document.getElementById("public-id").textContent = publicId;

const esid = data.esid ?? "AB----";
document.getElementById("esid").textContent = esid;

document.getElementById("copy-esid-btn").onclick = async () => {
  try {
    await navigator.clipboard.writeText(esid);
    document.getElementById("copy-esid-btn").textContent = "Copied";
    setTimeout(() => {
      document.getElementById("copy-esid-btn").textContent = "Copy";
    }, 1500);
  } catch {
    document.getElementById("copy-esid-btn").textContent = "Failed";
  }
};

document.getElementById("copy-id-btn").onclick = async () => {
  try {
    await navigator.clipboard.writeText(publicId);
    document.getElementById("copy-id-btn").textContent = "Copied";
    setTimeout(() => {
      document.getElementById("copy-id-btn").textContent = "Copy";
    }, 1500);
  } catch {
    document.getElementById("copy-id-btn").textContent = "Failed";
  }
};

const authEl = document.getElementById("auth-status");
if (data.mcp_oauth_at_connect || data.signed_in_with_google) {
  authEl.textContent = "Signed in via Google (MCP connect)";
  authEl.classList.add("connected");
} else {
  authEl.textContent = "Guest — reconnect MCP with OAuth: Yes to sign in with Google";
}

const channelsEl = document.getElementById("channels");
const channelsEmpty = document.getElementById("channels-empty");
const channels = data.linked_channels ?? [];

if (channels.length) {
  channelsEmpty.hidden = true;
  for (const ch of channels) {
    const li = document.createElement("li");
    const label = ch.channel_type === "whatsapp" ? "WhatsApp" : "Telegram";
    li.textContent = `${label}: ${ch.external_id}`;
    channelsEl.appendChild(li);
  }
} else {
  channelsEmpty.hidden = false;
}

const profile = data.profile ?? {};
const profileEl = document.getElementById("profile-summary");
const profileEmpty = document.getElementById("profile-empty");
const fields = [
  ["Region", profile.region],
  ["Degree", profile.degree],
  ["Field", profile.major],
  ["CGPA", profile.cgpa],
  ["Budget", profile.budget_range],
  ["Intake", profile.target_intake],
  ["Priority", profile.priority],
];

let hasProfile = false;
for (const [label, value] of fields) {
  if (!value) continue;
  hasProfile = true;
  const li = document.createElement("li");
  li.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
  profileEl.appendChild(li);
}
profileEmpty.hidden = hasProfile;
