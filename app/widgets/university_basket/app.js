const bridge = window.openai ?? {};
const data = bridge.toolOutput?.structuredContent ?? bridge.toolOutput ?? {};
const universities = data.universities ?? [];
const planId = data.plan_id ?? bridge.widgetState?.plan_id;
const subscribedIds = new Set(data.subscribed_university_ids ?? []);
const maxSubs = data.max_subscriptions ?? 10;
let subCount = data.subscription_count ?? subscribedIds.size;

const basket = document.getElementById("basket");
const headerScore = document.getElementById("header-score");
const subHint = document.getElementById("sub-hint");

const overall = data.candidate_score?.overall ?? data.profile?.candidate_score_json?.overall;
if (overall != null) {
  headerScore.textContent = `Based on your profile · Score: ${Math.round(overall)}/100`;
  headerScore.hidden = false;
}
subHint.textContent = `You can subscribe to up to ${maxSubs} colleges (${subCount}/${maxSubs} used)`;

basket.innerHTML = "";

const groups = { reach: [], target: [], safety: [] };
for (const uni of universities.slice(0, 10)) {
  const cat = (uni.category || "target").toLowerCase();
  (groups[cat] || groups.target).push(uni);
}

function budgetLight(tuition, profileBudget) {
  if (!tuition) return "";
  const budget = profileBudget || 50000;
  if (tuition <= budget * 0.8) return "under";
  if (tuition <= budget) return "ok";
  return "over";
}

async function onNotify(btn, uni) {
  if (!planId) {
    alert("Missing plan_id");
    return;
  }
  if (btn.disabled) return;

  const result = bridge.callTool
    ? await bridge.callTool("subscribe_college_notification", {
        plan_id: planId,
        university_id: uni.id,
      })
    : await fetch("/api/subscriptions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_id: planId, university_id: uni.id }),
      }).then((r) => r.json());

  if (result?.status === "subscribed") {
    btn.textContent = "✅ Notified";
    btn.disabled = true;
    btn.classList.add("notified");
    subCount = result.subscribed_count ?? subCount + 1;
    subHint.textContent = `You can subscribe to up to ${maxSubs} colleges (${subCount}/${maxSubs} used)`;
    bridge.sendFollowUpMessage?.({
      prompt:
        `You've subscribed to ${uni.university_name} notifications! ` +
        `To receive updates on Telegram, click this link: ${result.telegram_invite_link} ` +
        `Then send your ESID (${result.esid}) to the bot.`,
    });
  } else if (result?.status === "limit_reached") {
    alert("You have reached the maximum of 10 college subscriptions.");
  } else if (result?.status === "already_subscribed") {
    btn.textContent = "✅ Notified";
    btn.disabled = true;
    btn.classList.add("notified");
  }
}

function renderCard(uni) {
  const card = document.createElement("div");
  card.className = "uni-card";
  const name = uni.university_name || "Unknown";
  const program = uni.program_name ? ` — ${uni.program_name}` : "";
  const rank = uni.qs_rank ? `QS #${uni.qs_rank}` : "";
  const tuition = uni.tuition_usd ? `$${Number(uni.tuition_usd).toLocaleString()}/yr` : "";
  const deadline = uni.deadline ? uni.deadline : "";
  const match = uni.match_score != null ? `Match: ${Math.round(uni.match_score)}%` : "";
  const accept = uni.acceptance_rate ? `Acceptance: ${uni.acceptance_rate}%` : "";
  const light = budgetLight(uni.tuition_usd, data.profile?.budget_usd);
  const isSubscribed = subscribedIds.has(uni.id);

  const row = document.createElement("div");
  row.className = "uni-row";

  const info = document.createElement("div");
  info.className = "uni-info";
  info.innerHTML = `
    <div class="uni-header">
      <strong>${name}${program}</strong>
    </div>
    <div class="uni-meta">
      ${rank ? `<span class="badge">${rank}</span>` : ""}
      ${tuition ? `<span class="tuition ${light}">${tuition}</span>` : ""}
      ${deadline ? `<span class="deadline">${deadline}</span>` : ""}
    </div>
    <div class="uni-meta secondary">
      ${match ? `<span class="match-bar">${match}</span>` : ""}
      ${accept ? `<span class="accept">${accept}</span>` : ""}
    </div>
  `;

  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "notify-btn";
  btn.dataset.uniId = uni.id;
  btn.dataset.uniName = name;
  if (isSubscribed) {
    btn.textContent = "✅ Notified";
    btn.disabled = true;
    btn.classList.add("notified");
  } else {
    btn.textContent = "🔔 Notify";
    btn.onclick = () => onNotify(btn, uni);
  }

  row.appendChild(info);
  row.appendChild(btn);
  card.appendChild(row);
  return card;
}

for (const [category, items] of Object.entries(groups)) {
  if (!items.length) continue;
  const section = document.createElement("div");
  section.className = `category ${category}`;
  section.innerHTML = `<h2>${category.toUpperCase()} <span class="count">(${items.length})</span></h2>`;
  const grid = document.createElement("div");
  grid.className = "card-grid";
  for (const uni of items) grid.appendChild(renderCard(uni));
  section.appendChild(grid);
  basket.appendChild(section);
}

if (!universities.length) {
  basket.innerHTML =
    '<p class="empty">No universities in your shortlist yet. Ask the agent to run search_universities.</p>';
}
