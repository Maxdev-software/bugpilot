# BugPilot — AI-powered Bug Tracker

Django REST Framework + Celery + OpenRouter LLM

## Stack

| Layer | Tech |
|---|---|
| Backend | Django 4.2, DRF |
| Async tasks | Celery 5 + Redis |
| LLM | OpenRouter (any OpenAI-compatible) |
| DB | SQLite (dev) / PostgreSQL (prod) |
| Auth | Token-based (DRF) |

## Roles

| Role | Permissions |
|---|---|
| **Admin** | Full CRUD, user management, role changes |
| **Teamlead** | Full ticket CRUD, trigger reanalysis, manage projects |
| **Developer** | Read all tickets, update assigned tickets, add comments |

## Quick start

```bash
cp .env.example .env
# Fill OPENROUTER_API_KEY in .env

# Dev (SQLite, no Docker)
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Run Celery worker (separate terminal)
celery -A config worker --loglevel=info

# Or with Docker
docker compose up
```

## Seed accounts

| User | Password | Role |
|---|---|---|
| admin | admin123 | Admin |
| teamlead | lead123 | Teamlead |
| alice | dev123 | Developer |
| bob | dev123 | Developer |

## API reference

### Auth
```
POST /api/v1/auth/register/      { username, email, password, password_confirm, role }
POST /api/v1/auth/login/         { username, password }  → { token, user }
POST /api/v1/auth/logout/
GET  /api/v1/auth/me/
GET  /api/v1/auth/users/                   [Admin]
PATCH /api/v1/auth/users/{id}/role/        [Admin]
```

### Ingest (external apps)
```
POST /api/v1/ingest/log/
Header: X-Ingest-Token: <INGEST_API_TOKEN>

{
  "app_name": "payment-service",
  "environment": "production",
  "level": "ERROR",             # DEBUG|INFO|WARNING|ERROR|CRITICAL
  "message": "Exception text",
  "stacktrace": "Traceback...",
  "metadata": {},               # optional
  "project_slug": "my-project" # optional
}

→ 202 { log_id, task_id, status: "queued" }
```

### Tickets
```
GET    /api/v1/tickets/?priority=critical&status=open&search=redis
POST   /api/v1/tickets/                    [Teamlead+]
GET    /api/v1/tickets/{id}/
PATCH  /api/v1/tickets/{id}/
DELETE /api/v1/tickets/{id}/               [Teamlead+]
POST   /api/v1/tickets/{id}/reanalyse/     [Teamlead+]  → AI re-runs in background
PATCH  /api/v1/tickets/{id}/assign/        { assignee_id }
PATCH  /api/v1/tickets/{id}/status/        { status }
```

### Comments
```
GET    /api/v1/tickets/{id}/comments/
POST   /api/v1/tickets/{id}/comments/      { body }
PATCH  /api/v1/tickets/{id}/comments/{id}/
DELETE /api/v1/tickets/{id}/comments/{id}/
```

### Projects
```
GET    /api/v1/projects/
POST   /api/v1/projects/            [Teamlead+]  { name, slug, description }
POST   /api/v1/projects/{id}/members/{user_id}/   add member
DELETE /api/v1/projects/{id}/members/{user_id}/   remove member
```

### Stats
```
GET /api/v1/stats/
→ { total, open, in_progress, resolved, critical, bug, warning, ai_analysed }
```

## How AI analysis works

1. External app POSTs crash log → `IngestLog` created
2. Celery task `analyse_ingest_log` fires immediately (async)
3. Task calls OpenRouter with the stacktrace
4. LLM returns `{ summary, root_cause, fix_suggestion, priority }`
5. `Ticket` auto-created with priority and full AI analysis attached
6. If LLM fails → task retries 3× with 30 s delay

OpenRouter free models that work well:
- `mistralai/mistral-7b-instruct:free`
- `google/gemma-3-1b-it:free`
- `meta-llama/llama-3.1-8b-instruct:free`
