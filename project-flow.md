# EduScout — End-to-End System Flow

> Everything that happens from a user opening ChatGPT/Claude to receiving a
> Telegram deadline ping three weeks later.  
> Read this before touching any service, route, or schema change.

---

## 1. System Map

```
┌─────────────────────────────────────────────────────────────────────┐
│  CLIENT LAYER                                                        │
│  ChatGPT (MCP/SSE)  ·  Claude (MCP/HTTP)  ·  Telegram Bot          │
└────────────────┬───────────────────────────────┬────────────────────┘
                 │ MCP tool calls                 │ Telegram Webhook
                 ▼                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FASTAPI BACKEND  (uvicorn / Docker)                                │
│                                                                      │
│  /sse  /mcp          ← MCP endpoints (FastMCP)                      │
│  /api/onboarding/*   ← widget form submissions                      │
│  /telegram/webhook   ← Telegram bot messages                        │
│  /webhooks/supabase  ← Supabase DB event push                       │
│  /auth/*             ← Google OAuth (FastMCP-managed)               │
│  /health             ← status + config dump                         │
│                                                                      │
│  app/query/      ← one file per table, direct Supabase client       │
│  app/services/   ← business logic                                   │
│  app/tools/      ← MCP tool definitions                             │
│  app/routes/     ← HTTP route handlers                              │
└──────────────────────────┬──────────────────────────────────────────┘
                            │ REST / PostgREST
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  SUPABASE                                                            │
│  PostgreSQL DB  ·  Database Webhooks  ·  Edge Functions (scheduler) │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. User Identity & Authentication

### 2a. MCP / ChatGPT path (Google OAuth)

```
User adds MCP connector in ChatGPT/Claude
          │
          ▼
FastMCP GoogleProvider → Google OAuth consent screen
          │
          ▼ id_token (sub, email, name)
          │
services/session.py → resolve_current_user()
          │
          ▼
services/user.py → get_or_create_by_google(sub, email, name)
          │
          ▼
DB: users table
  • email, name, google_sub (unique)
  • public_id = ESC-XXXXXX  (generated on first insert)
  • esid     = AB0042        (letter-prefix + sequence, for Telegram linking)
  • overall_score (updated when candidate score is generated)
```

**Every MCP tool call** that needs a user calls `resolve_current_user()`.  
If OAuth is off (guest mode), a throw-away `guest-<hex>@studyabroad.local` row
is created so the rest of the code never needs to special-case anonymous users.

### 2b. Telegram path (ESID linking)

```
User sends ESID (e.g. "AB0042") to Telegram bot
          │
          ▼
routes/telegram.py → handle_esid_link(chat_id, esid)
          │
          ▼
query/links.py → upsert_linked_channel(user_id, "telegram", chat_id)
          │
          ▼
DB: linked_channels (user_id, channel_type="telegram", external_id=chat_id)
```

After linking, every outbound notification to that user hits their Telegram chat.

---

## 3. Onboarding & Profile Collection

The profile is collected in three stages, each mapped to a widget form and an
API endpoint.  The MCP tools in `app/tools/user_input/` drive the same flow
when the user is talking to ChatGPT/Claude directly.

```
┌──────────────┐   POST /api/onboarding/start
│  /start      │ ─────────────────────────────► create study_plan row
│              │                                 create profiles row (empty)
└──────────────┘                                 return { plan_id, user_id }

┌──────────────┐   POST /api/onboarding/stage1
│  Stage 1     │ ─────────────────────────────► profiles: degree, major, cgpa,
│  Academic    │                                 university_name, target_degree,
│  + Budget    │                                 target_field, budget_usd,
│  + Countries │                                 preferred_countries, region,
└──────────────┘                                 target_intake, priority
                                                 onboarding_stages: stage=1 ✓

┌──────────────┐   POST /api/onboarding/stage2
│  Stage 2     │ ─────────────────────────────► profiles: exams_json
│  Exams       │                                 onboarding_stages: stage=2 ✓
└──────────────┘

┌──────────────┐   POST /api/onboarding/stage3
│  Stage 3     │ ─────────────────────────────► profiles: work_json,
│  Experience  │                                 research_json,
│  + Prefs     │                                 extracurriculars_json,
└──────────────┘                                 campus_type, post_study_goal,
                                                 visa_constraints, funding_open
                                                 onboarding_stages: stage=3 ✓
                                                 → triggers candidate score gen
```

**DB tables written during onboarding:**
- `study_plans` — one row per plan (user can have multiple)
- `profiles` — one row per plan (plan_id is PK)
- `onboarding_stages` — one row per (plan_id, stage), stores snapshot JSON

**Key validation gate:**  
`services/profile_validation.py → check_profile_ready()` must return
`{ ready: true }` before `search_universities` is allowed to run.  
Required fields: `target_degree`, `target_field`, `cgpa`, `language_test`,
`budget_usd`, `preferred_countries`, `target_intake`.

---

## 4. University Research & Subscription

```
MCP tool: search_universities(plan_id, target_degree, ...)
          │
          ▼
Returns a research brief prompt → host AI (ChatGPT/Claude) does the web
research and calls add_university_to_plan for each result
          │
          ▼
MCP tool: add_university_to_plan(plan_id, university_name, category, ...)
          │
          ▼
DB: universities row created (plan_id FK, category=reach/target/safety,
    deadline, match_score, program_name, tuition_usd, etc.)
          │
          ▼  Supabase DB Webhook fires (universities INSERT)
          │
routes/webhooks.py → _handle_university_event()
          │
          ▼
notify_user() → Telegram: "🏫 MIT — deadline set: 2025-12-15"
```

**Subscription** (user decides to track a specific university):
```
MCP tool: subscribe_to_college(user_id, university_id)
          │
          ▼
DB: college_subscriptions (user_id, university_id, subscribed_at)
          │
          ▼  Supabase DB Webhook fires (college_subscriptions INSERT)
          │
routes/webhooks.py → _handle_subscription_event()
          │
          ▼
Telegram: "✅ Subscribed to MIT — deadline: 2025-12-15"
```

---

## 5. Task Management

Tasks are created by the MCP agent when it builds a study plan roadmap.

```
MCP tool: create_task(plan_id, title, due_date)
          │
          ▼
DB: tasks row (plan_id FK, title, due_date, status="pending")
          │
          ▼  Supabase DB Webhook fires (tasks INSERT)
          │
routes/webhooks.py → _handle_task_event()
          │
          ▼
Telegram: "📋 New task added: Request LOR from Prof X — due 2025-11-01"
```

---

## 6. Notification Delivery

Two complementary mechanisms — webhook (instant) and scheduler (sweep).

### 6a. Supabase Database Webhooks → instant push

| Trigger table | Events | Handler | Message sent |
|---|---|---|---|
| `tasks` | INSERT | new task notification | "📋 New task: {title}" |
| `tasks` | UPDATE status→overdue | overdue alert | "⚠️ Overdue: {title}" |
| `universities` | INSERT / UPDATE deadline | deadline set | "🏫 {uni} deadline: {date}" |
| `college_subscriptions` | INSERT | subscription confirm | "✅ Subscribed to {uni}" |

Configure in: **Supabase Dashboard → Database → Webhooks**  
URL: `{PUBLIC_BASE_URL}/webhooks/supabase`  
Secret: set `SUPABASE_WEBHOOK_SECRET` in both Supabase and `.env`

### 6b. Supabase Edge Function → serverless scheduler

Replaces the APScheduler in-process cron.  Runs every hour via a Supabase
cron job (no server required when deployed serverlessly).

```
Supabase pg_cron / Edge Function cron
          │  (every hour)
          ▼
POST {PUBLIC_BASE_URL}/internal/notify
  Authorization: Bearer {INTERNAL_NOTIFY_SECRET}
          │
          ▼
services/notifications.py → run_notification_job()
  • upcoming tasks (within 3 days)  → Telegram + WhatsApp
  • overdue tasks                    → Telegram + WhatsApp
  • college deadlines approaching    → Telegram
  • keyword nudges (scholarship/visa)
```

See `supabase/functions/notify-cron/` for the Edge Function source.  
See `supabase/schedule.sql` for the pg_cron setup.

---

## 7. Telegram Bot — Full Conversation Flow

```
User opens Telegram, sends any message
          │
          ▼
routes/telegram.py → telegram_webhook(request)

  ┌─── /start [esid]  ────────────────────────────────────────────────┐
  │  If ESID provided in deep-link:                                    │
  │    → handle_esid_link(chat_id, esid)                               │
  │    → upsert linked_channels                                        │
  │    → reply: "✅ Linked! Hi {name} · Score: {score}/100            │
  │             Your colleges: MIT, Stanford…                          │
  │             You'll receive deadline reminders here."               │
  │  If no ESID:                                                        │
  │    → reply: "Welcome! Please send your ESID (e.g. AB0042)         │
  │             Find it in your EduScout chat on ChatGPT."             │
  └────────────────────────────────────────────────────────────────────┘

  ┌─── "AB0042" (bare ESID format) ───────────────────────────────────┐
  │    → same as /start AB0042 above                                   │
  └────────────────────────────────────────────────────────────────────┘

  ┌─── /link {code}  (OTP code from MCP tool create_link_code) ───────┐
  │    → redeem_link_code(code, "telegram", chat_id)                   │
  │    → upsert linked_channels                                        │
  │    → reply: "Telegram linked successfully."                        │
  └────────────────────────────────────────────────────────────────────┘

  ┌─── /status  ───────────────────────────────────────────────────────┐
  │    → get_user_by_chat_id(chat_id)                                  │
  │    → list_subscriptions(user_id)                                   │
  │    → list_tasks(plan_id) filtered pending/overdue                  │
  │    → reply: structured summary of colleges + task counts           │
  └────────────────────────────────────────────────────────────────────┘

  ┌─── /colleges  ─────────────────────────────────────────────────────┐
  │    → list_subscriptions(user_id)                                   │
  │    → reply: each college with deadline + match_score               │
  └────────────────────────────────────────────────────────────────────┘

  ┌─── /tasks  ────────────────────────────────────────────────────────┐
  │    → get_upcoming_tasks + get_overdue_tasks for user               │
  │    → reply: grouped list (overdue first, then upcoming 7 days)     │
  └────────────────────────────────────────────────────────────────────┘

  ┌─── any other text (linked user) ───────────────────────────────────┐
  │    → show brief summary: colleges count + next deadline            │
  └────────────────────────────────────────────────────────────────────┘

  ┌─── any other text (unlinked user) ─────────────────────────────────┐
  │    → reply: "Please send your ESID to link your account."          │
  └────────────────────────────────────────────────────────────────────┘
```

**How college selections from GPT forms reach Telegram:**  
When user selects a university in the ChatGPT widget or via MCP tool
`add_university_to_plan` → DB `universities` INSERT → Supabase DB webhook
→ `_handle_university_event()` → `notify_user()` → Telegram message.  
When user calls `subscribe_to_college` → DB `college_subscriptions` INSERT
→ Supabase webhook → Telegram subscription confirmation.

---

## 8. Google Calendar Sync

See `google-sync.md` for full OAuth setup and implementation guide.

**Short summary:**

```
User grants Google Calendar permission (once)
          │
          ▼
DB: users.google_calendar_token (encrypted refresh token)

When a task or university deadline is created/updated:
          │
          ▼
services/google_calendar.py → upsert_calendar_event(user_id, event)
          │
          ▼
Google Calendar API → event created/updated in user's calendar
          │
          ▼
DB: calendar_events (plan_id, event_id=gcal_event_id, title)
  (so we can update/delete events later without creating duplicates)
```

---

## 9. Database Schema — Table Relationships

```
users
  │
  ├── study_plans (user_id FK)
  │       │
  │       ├── profiles (plan_id PK FK)
  │       ├── universities (plan_id FK)
  │       │       │
  │       │       └── college_subscriptions (university_id FK, user_id FK)
  │       ├── tasks (plan_id FK)
  │       ├── calendar_events (plan_id FK)
  │       ├── documents (plan_id FK)
  │       └── onboarding_stages (plan_id FK)
  │
  ├── linked_channels (user_id FK)  ← Telegram / WhatsApp chat IDs
  └── link_codes (user_id FK)       ← OTP codes for linking
```

**Write path for every entity:**
```
MCP tool call / widget POST
  → app/services/<entity>.py  (business logic, validation)
    → app/query/<table>.py    (Supabase client, one file per table)
      → Supabase REST API
        → PostgreSQL
          → DB Webhook (if configured) → /webhooks/supabase → notify
```

**Read path:**
```
MCP tool call / widget GET
  → app/services/<entity>.py
    → app/query/<table>.py
      → Supabase REST API (PostgREST with joins via foreign key embedding)
```

---

## 10. Endpoint Reference

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/health` | Status + config dump | None |
| GET | `/sse` | MCP SSE connector (ChatGPT) | FastMCP OAuth |
| GET | `/mcp` | MCP streamable HTTP (Claude) | FastMCP OAuth |
| POST | `/messages` | MCP message handler | FastMCP OAuth |
| GET | `/auth/success` | OAuth success page | None |
| GET | `/auth/setup` | OAuth setup checklist JSON | None |
| POST | `/api/onboarding/start` | Create plan + profile | None (user_id in body) |
| GET | `/api/onboarding/profile/{plan_id}` | Get profile + stage progress | None |
| POST | `/api/onboarding/stage1` | Save academic + budget + countries | None |
| POST | `/api/onboarding/stage2` | Save exams | None |
| POST | `/api/onboarding/stage3` | Save experience + prefs | None |
| POST | `/api/onboarding/submit_all` | Save all stages in one call | None |
| POST | `/api/onboarding/save` | Partial flat profile save (widget) | None |
| POST | `/api/onboarding/submit` | Final submit + validation check | None |
| POST | `/telegram/webhook` | Telegram bot messages | Telegram token verify |
| POST | `/whatsapp/webhook` | WhatsApp messages | WhatsApp token verify |
| GET | `/whatsapp/webhook` | WhatsApp webhook verification | WhatsApp token verify |
| POST | `/webhooks/supabase` | Supabase DB event push | HMAC-SHA256 signature |
| POST | `/internal/notify` | Trigger notification sweep | Bearer secret |
| GET | `/auth/google/calendar` | Start Google Calendar OAuth | Session cookie |
| GET | `/auth/google/calendar/callback` | Google Calendar OAuth callback | Google |

---

## 11. Environment Variables

```env
# Supabase — required
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=service_role_secret
SUPABASE_WEBHOOK_SECRET=hmac_secret_matching_supabase_dashboard

# Google MCP OAuth — for ChatGPT/Claude sign-in
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx
MCP_OAUTH_ENABLED=true
PUBLIC_BASE_URL=https://your-ngrok-or-domain.com

# Google Calendar OAuth — separate credentials, calendar scope
GOOGLE_CALENDAR_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CALENDAR_CLIENT_SECRET=GOCSPX-xxx
GOOGLE_CALENDAR_REDIRECT_URI=${PUBLIC_BASE_URL}/auth/google/calendar/callback

# Internal scheduler trigger — set same value in Supabase Edge Function env
INTERNAL_NOTIFY_SECRET=long_random_secret

# Telegram
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_BOT_USERNAME=StudyAbroadAgentBot

# WhatsApp
WHATSAPP_TOKEN=
WHATSAPP_PHONE_ID=
WHATSAPP_VERIFY_TOKEN=study-abroad-verify
```

---

## 12. Deployment Checklist

```
1. Supabase project created
2. supabase/schema.sql executed in SQL Editor
3. supabase/schedule.sql executed (pg_cron for hourly notifier)
4. supabase/functions/notify-cron/ deployed (supabase functions deploy notify-cron)
5. .env filled with all keys above
6. Three Supabase DB Webhooks created:
     tasks INSERT+UPDATE      → {BASE_URL}/webhooks/supabase
     universities INSERT+UPDATE → {BASE_URL}/webhooks/supabase
     college_subscriptions INSERT → {BASE_URL}/webhooks/supabase
7. Telegram bot @BotFather webhook set:
     curl -X POST "https://api.telegram.org/bot{TOKEN}/setWebhook" \
          -d "url={BASE_URL}/telegram/webhook"
8. Google Cloud Console:
     - OAuth consent screen (openid, email, profile, calendar.events)
     - Two OAuth Client IDs:
         a. MCP sign-in:      redirect = {BASE_URL}/auth/callback
         b. Calendar sync:    redirect = {BASE_URL}/auth/google/calendar/callback
9. uvicorn app.main:app --host 0.0.0.0 --port 8000
   (or docker run --env-file .env study-abroad-agent)
```