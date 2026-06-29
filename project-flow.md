# Study Abroad Agent — Project Flow

A plain-language guide to how this project works: what it does, how data moves, and how to run or extend it.

---

## What is this?

**Study Abroad Agent** is a backend server that connects to **ChatGPT** (via MCP) and **Claude**. It helps students build a study-abroad profile, get college matches, manage documents, and receive deadline alerts on WhatsApp or Telegram.

**Important split of responsibilities:**

| Who | Does what |
|-----|-----------|
| **This backend** | Saves profile data, scores candidates, stores shortlists, serves form widgets, sends notifications |
| **ChatGPT / Claude** | Talks to the user, researches universities, writes resume/SOP text |

The backend **never** calls OpenAI or Anthropic directly. MCP tools return structured data and briefs; the host AI does the reasoning and writing.

**Stack:** Python 3.12+, FastAPI, FastMCP, SQLite, APScheduler.

---

## How to run it (development)

You need **two terminals** when testing with ChatGPT:

```powershell
# Terminal 1 — backend
cd D:\studyabroad
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — public HTTPS tunnel
ngrok http 8000
```

Then:

1. Copy the ngrok HTTPS URL (e.g. `https://abc123.ngrok-free.app`)
2. Put it in `.env` as `PUBLIC_BASE_URL=https://abc123.ngrok-free.app`
3. **Restart uvicorn** — reload does **not** pick up `.env` changes
4. In ChatGPT: add connector URL `{PUBLIC_BASE_URL}/sse`

**Check it works:**

```powershell
curl http://127.0.0.1:8000/health
```

Open `https://YOUR-NGROK-URL/auth/setup` for an OAuth checklist.

**Use `scripts/dev.ps1`** if your shell sets `BASE_URL=localhost` and overrides `.env`.

---

## ChatGPT connector: OAuth vs No Auth

| Mode | `.env` | ChatGPT setting |
|------|--------|-----------------|
| **Guest / No Auth** | `MCP_OAUTH_ENABLED=false` | Authentication → **No Auth** |
| **Google sign-in** | `MCP_OAUTH_ENABLED=true` + Google creds | Authentication → **OAuth** |

**OAuth requirements:**

- `PUBLIC_BASE_URL` must be **HTTPS** (ngrok)
- Google Cloud Console → **Web application** client
- **Authorized redirect URI:** `{PUBLIC_BASE_URL}/auth/callback`
- **Authorized JavaScript origin:** `{PUBLIC_BASE_URL}` (no trailing path)
- Restart uvicorn after every ngrok URL change

**Common failures:**

- *“MCP server does not implement OAuth”* — server started before `.env` was updated; restart uvicorn
- *“Doesn't support CIMD or DCR”* — ngrok URL in ChatGPT ≠ `PUBLIC_BASE_URL` in running server
- *Infinite loading on OAuth* — wrong Google redirect URI, or ngrok “Visit Site” warning blocking the popup

---

## User journey (happy path)

```
Connect MCP (OAuth or guest)
        ↓
User says “hi” → AI calls check_form_progress
        ↓
Stage 1 widget — personal & academic info
        ↓ POST /api/onboarding/stage1 → auto-opens Stage 2
Stage 2 widget — exam scores (+ upload docs in chat)
        ↓ POST /api/onboarding/stage2 → auto-opens Stage 3
Stage 3 widget — experience & preferences
        ↓ POST /api/onboarding/submit_all
Profile scored → search_universities → college basket
        ↓
User clicks 🔔 Notify on colleges → Telegram deep link (?start=ESID)
        ↓
Bot confirms subscriptions; hourly deadline alerts
```

The host AI is instructed (**system prompt**) not to search colleges until all 3 form stages are complete.

---

## Identity: ESID and SAA ID

Each user gets two IDs:

| ID | Format | Used for |
|----|--------|----------|
| **ESID** | `AB1234` (2 letters + 4+ digits) | Telegram notify flow, account display |
| **SAA ID** | `SAA-XXXXXX` | Legacy WhatsApp/Telegram link codes |

ESID is created at signup (or first OAuth connect). Telegram uses a deep link:

`https://t.me/YourBot?start=AB1234`

No typing required — the bot reads ESID from `/start AB1234`.

---

## Three-stage onboarding form

The profile is collected in **three widgets**, not one long form. This reduces drop-off and keeps document upload isolated in Stage 2.

### Stage 1 — Personal & Academic
- Name, degree, major, CGPA, home university, target degree/field, countries, intake, budget
- Widget: `profile_form_stage1`
- Save: `POST /api/onboarding/stage1`
- On submit → opens Stage 2 automatically

### Stage 2 — Exams & Documents
- IELTS, TOEFL, GRE scores
- User uploads resume/transcript **in ChatGPT chat** → AI calls `analyze_document` (base64 → backend extracts outline)
- Widget: `profile_form_stage2`
- Save: `POST /api/onboarding/stage2`
- On submit → opens Stage 3 automatically

### Stage 3 — Experience & Preferences
- Work, internships, research, extracurriculars, campus/visa preferences
- Widget: `profile_form_stage3`
- Save: `POST /api/onboarding/stage3` then `POST /api/onboarding/submit_all`
- On success → triggers college search

### Widget behavior (ChatGPT)

- **Scroll:** Form fields scroll inside the widget (`overscroll-behavior: contain`) so ChatGPT chat scroll is not hijacked
- **Submit:** Always **POSTs** to the backend API first, then syncs via MCP `save_onboarding_stage`
- **Prefill:** Loads saved data from `GET /api/onboarding/profile/{plan_id}`
- **Auto-advance:** After save, calls `show_stage2_widget` / `show_stage3_widget` via MCP

Shared widget code lives in `app/widgets/stage_shared.js` and `stage_layout.css`, injected when bundles are built.

---

## College matches & notifications

After profile submit:

1. `generate_candidate_score` — dimension scores (academic, language, research, etc.)
2. `search_universities` — returns a **research brief**; ChatGPT researches programs
3. `add_university_to_plan` — saves REACH / TARGET / SAFETY rows
4. `show_university_basket` — scrollable top matches with **🔔 Notify** buttons

**Subscriptions:**

- Max **10 colleges** per user (`college_subscriptions` table)
- Notify click → `subscribe_college_notification` → Telegram link with ESID
- Hourly scheduler sends deadline reminders to linked Telegram/WhatsApp channels

---

## HTTP routes (FastAPI)

| Path | Purpose |
|------|---------|
| `GET /health` | Status, OAuth mode, connector URL, setup checklist |
| `GET /auth/setup` | Step-by-step OAuth + Google Console instructions |
| `GET /auth/success` | Post-login “Connected” page (closes tab) |
| `GET /auth/error` | Friendly OAuth failure page |
| `GET /api/onboarding/profile/{plan_id}` | Load saved profile for widget prefill |
| `POST /api/onboarding/stage1\|2\|3` | Save each form stage |
| `POST /api/onboarding/submit_all` | Final validation + scoring + `research_ready` |
| `POST /whatsapp/webhook` | WhatsApp link + verify |
| `POST /telegram/webhook` | ESID deep link + subscription confirm |

**MCP routes** (via middleware → FastMCP):

| Path | Purpose |
|------|---------|
| `GET /sse`, `POST /messages` | ChatGPT connector |
| `GET /mcp` | Claude streamable HTTP |
| `/authorize`, `/token`, `/register`, `/auth/callback` | OAuth (when enabled) |
| `/.well-known/*` | OAuth discovery (RFC 7591 DCR, CIMD) |

Only `/auth/callback` goes to FastMCP OAuth. Other `/auth/*` paths (success, error, setup) are handled by FastAPI.

---

## Database (SQLite)

**File:** `app/database/study_abroad.db`

### Core tables

- **users** — email, name, `public_id` (SAA-), **`esid`**, `google_sub`, `overall_score`
- **study_plans** — one roadmap per user; status: `active` → `profile_complete` → `research_ready`
- **profiles** — one row per plan; scalar fields + JSON blobs for exams, work, research, etc.
- **onboarding_stages** — which of stages 1–3 are done (`plan_id`, `stage`, `completed_at`, snapshot)
- **universities** — shortlist with category, rankings, tuition, deadline, match_score
- **college_subscriptions** — user ↔ university notify links (max 10)
- **documents** — resume, SOP, LOR drafts (versioned)
- **tasks**, **calendar_events** — planning + scheduler alerts
- **link_codes**, **linked_channels** — WhatsApp/Telegram linking

### Profile JSON columns

Stored as TEXT, parsed on read:

- `exams_json` → IELTS, TOEFL, GRE, GMAT
- `work_json` → jobs, internships
- `research_json` → papers, conference tier
- `extracurriculars_json` → leadership, awards
- `resume_outline_json`, `transcript_outline_json` — from `analyze_document`
- `candidate_score_json` — scoring engine output

Migrations run automatically on startup (`init_db()`).

---

## MCP tools (~52)

Tools live in `app/tools/*/actions.py` and register via `register_all_tools(mcp)`.

### Account
`ensure_user`, `show_account`, `get_my_profile`, `update_profile`, **`get_esid`**

### User input (onboarding)
`start_planning_widget` (Stage 1), **`check_form_progress`**, **`handle_greeting`**, **`show_stage2_widget`**, **`show_stage3_widget`**, **`save_onboarding_stage`**, `save_onboarding_step`, `submit_onboarding`, `collect_*` helpers, `generate_candidate_score`, `check_profile_ready`

### University research
`search_universities`, `match_universities`, `add_university_to_plan`, `show_university_basket`, `compare_universities`, etc.

### Documents
`generate_resume_draft`, `generate_sop_outline`, `generate_lor_guide`, `save_document`, **`analyze_document`**

### Planning
`create_study_plan`, `add_task`, `get_tasks`, `add_calendar_event`, etc.

### Linking
`create_link_code`, `show_dashboard`, **`subscribe_college_notification`**, **`get_college_subscriptions`**, **`unsubscribe_college`**

Aliases (e.g. `onboard` → `start_planning_widget`, `notify` → `subscribe_college_notification`) are in `app/tools/registry.py`.

---

## Widgets

| Widget | Opens when | Notes |
|--------|------------|-------|
| `profile_form_stage1` | `start_planning_widget` | Stage 1 form, scroll + POST submit |
| `profile_form_stage2` | `show_stage2_widget` | Exam scores |
| `profile_form_stage3` | `show_stage3_widget` | Final submit → `submit_all` |
| `profile_form` | Legacy 18-step wizard | Still registered |
| `university_basket` | `show_university_basket` | Notify buttons, scroll list |
| `account` | `show_account` | ESID + SAA ID |
| `dashboard` | `show_dashboard` | Plan overview |

Widgets use the ChatGPT bridge: `window.openai.callTool`, `setWidgetState`, `sendFollowUpMessage`.

Bundles are rebuilt on server start (`app/mcp_server.py` → `_register_widgets()`).

---

## System prompt rules (for the host AI)

Defined in `app/prompts/system_prompt.py`:

1. **First action after connect:** `check_form_progress`
2. **Never search colleges** until stage 3 is complete
3. **Never skip the form** — re-show current stage widget if user asks
4. **Document uploads in chat** → call `analyze_document`
5. After submit → score, search, basket, offer resume/SOP tools
6. Notify click → share Telegram `?start=ESID` link

---

## Scoring (no LLM)

**Candidate score** (`app/services/scoring.py`): weighted blend of academic (30%), language (15%), research (25%), professional (20%), extracurricular (10%).

**Match score** per program: GPA fit, language, research, budget, preferences → label as reach / target / safety.

**Profile gates** before search (`check_profile_ready`): target degree/field, CGPA, language test, budget, countries, intake must be filled.

---

## Notifications

**Scheduler:** runs every hour.

Sends to linked WhatsApp/Telegram channels:

- Tasks due within 3 days
- Overdue tasks
- College subscription deadline alerts (when configured)

---

## Project layout (key folders)

```
studyabroad/
├── app/
│   ├── main.py              # FastAPI + MCP routing middleware
│   ├── mcp_server.py        # FastMCP, widgets, tools
│   ├── config.py            # Settings from .env
│   ├── routes/              # auth, onboarding, whatsapp, telegram
│   ├── services/            # Business logic
│   ├── tools/               # MCP tool definitions
│   ├── widgets/             # HTML/CSS/JS UI for ChatGPT
│   └── database/db.py       # Schema + migrations
├── scripts/dev.ps1          # Start server (avoids BASE_URL override)
├── .env                     # Secrets + PUBLIC_BASE_URL
└── project-flow.md          # This file
```

---

## Environment variables

| Variable | What it does |
|----------|--------------|
| `PUBLIC_BASE_URL` | Your ngrok HTTPS URL — **must match** ChatGPT connector URL |
| `PORT` | Server port (default 8000; must match ngrok) |
| `MCP_OAUTH_ENABLED` | `true` = OAuth at connect; `false` = guest mode |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth web client |
| `TELEGRAM_BOT_TOKEN` | Telegram bot for alerts |
| `TELEGRAM_BOT_USERNAME` | Bot username for deep links (e.g. `StudyAbroadAgentBot`) |
| `WHATSAPP_*` | WhatsApp Cloud API (optional) |

---

## Where to change things

| You want to… | Edit… |
|--------------|-------|
| Add an MCP tool | `app/tools/{domain}/actions.py` + `registry.py` |
| Change AI workflow rules | `app/prompts/system_prompt.py` |
| Fix form UI / scroll / submit | `app/widgets/profile_form_stage*/` + `stage_shared.js` |
| Add a profile field | `app/database/db.py`, `profile_extended.py`, stage widgets |
| Change validation before search | `app/services/profile_validation.py` |
| Change scoring | `app/services/scoring.py` |
| Debug ChatGPT connect | `.env`, restart uvicorn, `/health`, `/auth/setup` |
| Telegram ESID linking | `app/routes/telegram.py`, `college_subscriptions.py` |

---

## Quick verification

```powershell
# Health (check chatgpt_auth_mode and base_url)
Invoke-RestMethod http://127.0.0.1:8000/health

# Tool count
python -c "import asyncio; from app.mcp_server import mcp; print(len(asyncio.run(mcp.list_tools())))"
```

Expected: ~52 tools, `/health` shows correct `base_url` and auth mode for your `.env`.

---

## Not built yet

- Full conversational agent on WhatsApp/Telegram (link + push only today)
- PostgreSQL / Redis
- Live university ranking APIs
- Standalone web app
- Stored chat history

---

*Last updated to reflect: 3-stage onboarding widgets, ESID, OAuth/DCR setup, college subscriptions, analyze_document, and widget POST submit + auto-advance flow.*
