# Study Abroad Agent

Backend for Claude MCP, ChatGPT Apps SDK, WhatsApp, and Telegram notifications.

## Prerequisites

- Python 3.12+
- Virtual environment (recommended)
- [Supabase](https://supabase.com) project (free tier works)

## Setup

```powershell
cd D:\studyabroad
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and fill in your Supabase credentials and any WhatsApp/Telegram tokens.

## Database setup (Supabase)

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **Dashboard → SQL Editor**
3. Open and run `supabase/schema.sql` — this creates all tables and indexes
4. Copy your credentials from **Dashboard → Project Settings → API**:
   - `SUPABASE_URL` → Project URL
   - `SUPABASE_SERVICE_KEY` → `service_role` secret key (**not** the anon key)

## Supabase Database Webhooks (optional but recommended)

Webhooks let Supabase push real-time events to the app, triggering instant
notifications instead of relying solely on the hourly scheduler.

**Setup in Supabase Dashboard → Database → Webhooks → Create new webhook:**

| Name | Table | Events | URL |
|------|-------|--------|-----|
| `task-events` | `tasks` | INSERT, UPDATE | `{PUBLIC_BASE_URL}/webhooks/supabase` |
| `university-deadline` | `universities` | INSERT, UPDATE | `{PUBLIC_BASE_URL}/webhooks/supabase` |
| `college-subscribed` | `college_subscriptions` | INSERT | `{PUBLIC_BASE_URL}/webhooks/supabase` |

**To protect the webhook endpoint (recommended):**
1. In Supabase webhook config, add a signing secret
2. Copy it to `SUPABASE_WEBHOOK_SECRET` in `.env`
3. Supabase will sign each request with `X-Supabase-Signature: sha256=<hmac>`
   and the app will reject any unsigned/tampered calls

The app logs every received webhook at `INFO` level so you can verify they arrive.

## Start the server

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Or:

```powershell
python -m app.main
```

Verify it is running:

```powershell
curl http://127.0.0.1:8000/health
```

The health response includes `supabase_webhook_url` showing the exact URL to use in Supabase.

## Connect MCP clients

| Client | URL |
|--------|-----|
| ChatGPT Apps SDK | `http://localhost:8000/sse` |
| Claude (streamable HTTP) | `http://localhost:8000/mcp` |

## Port already in use / WinError 10013

If you see:

```text
ERROR: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions
```

Port `8000` is likely blocked or already taken. Try another port:

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Then use `http://localhost:8080/sse` for ChatGPT.

## Docker

```powershell
docker build -t study-abroad-agent .
docker run -p 8000:8000 --env-file .env study-abroad-agent
```

## Main routes

- `GET /health` — health check (includes webhook URL)
- `GET /sse` — MCP SSE (ChatGPT)
- `POST /messages` — MCP messages
- `GET /mcp` — MCP streamable HTTP (Claude)
- `POST /webhooks/supabase` — Supabase database webhook receiver
- `POST /whatsapp/webhook` — WhatsApp webhook
- `POST /telegram/webhook` — Telegram webhook

## Project structure

```
app/
  query/          ← one file per table; all Supabase client calls live here
    users.py
    study_plans.py
    profiles.py
    universities.py
    tasks.py
    documents.py
    links.py
    onboarding_stages.py
    college_subscriptions.py
    calendar.py
  services/       ← business logic; calls query/ modules only
  routes/
    webhooks.py   ← Supabase database webhook handlers
    ...
  database/
    db.py         ← Supabase client factory (get_client())
supabase/
  schema.sql      ← run once in Supabase SQL Editor
```

## User identity & linking

Each user gets a permanent ID like `ESC-A1B2C3`.

- **Account widget**: agent calls `show_account` — shows ID, profile, linked channels
- **WhatsApp**: send `LINK ESC-A1B2C3` to your bot
- **Telegram**: send `/link ESC-A1B2C3`

## Google OAuth (MCP sign-in)

**Google sign-in happens only once — when adding the MCP connector** (ChatGPT Settings → Connectors, or Claude MCP settings). You choose **OAuth: Yes**, then Google login runs at connect time.

| OAuth at connect | What happens |
|------------------|--------------| 
| **Yes** + Google creds in `.env` | User signs in with Google → all tool calls use their Google identity → same `ESC-` ID every session |
| **No** | Anonymous guest user each session (still gets `ESC-` ID, can link WhatsApp/Telegram) |

### What you need from Google (only if OAuth: Yes)

1. **Google Cloud project** — [console.cloud.google.com](https://console.cloud.google.com)
2. **OAuth consent screen** — External, scopes: `openid`, `email`, `profile`
3. **OAuth 2.0 Client ID** — Web application
4. **Public HTTPS URL** (ngrok for dev)
5. Add to `.env`:

```env
BASE_URL=https://your-public-url.com
GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxx
```

6. In ChatGPT/Claude: add connector URL → **OAuth: Yes** → complete Google sign-in
