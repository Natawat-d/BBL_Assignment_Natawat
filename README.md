# Appointment Booking App

A small full-stack app where users log in and book appointment time slots.

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL, JWT bearer authentication.
- **Frontend:** React (Vite) SPA served by nginx.
- **Infra:** Docker Compose (Postgres + backend + frontend).
- **Tests:** pytest run against a real PostgreSQL database.

The focus is on **authentication** and **authorization**: admins can view all
appointments, while regular users can only manage their own bookings.

---

## Quick start (Docker)

Requires Docker Desktop.

```bash
docker compose up --build
```

Then open:

| URL | What |
|-----|------|
| http://localhost:8080 | Frontend (login + booking UI) |
| http://localhost:8000/docs | Interactive API docs (Swagger UI) |
| http://localhost:8000/api/health | Backend health check |

Stop the stack with `Ctrl-C`, or `docker compose down`. To also wipe the
database volume (fresh start): `docker compose down -v`.

### Seed accounts

Created automatically on first startup:

| Username | Password | Admin |
|----------|----------|-------|
| `admin`  | `admin123` | ✅ |
| `alice`  | `alice123` | — |
| `bob`    | `bob123`   | — |

Log in as `alice` to see only your own bookings; log in as `admin` to see
everyone's.

### How demo users are created

They are seeded **in code at startup**, not baked into a database dump:

1. [`crud.DEFAULT_USERS`](backend/app/crud.py) lists the three accounts.
2. [`crud.seed_default_users()`](backend/app/crud.py) inserts any that are missing,
   bcrypt-hashing each password (idempotent — safe to run every boot).
3. The FastAPI lifespan hook in [`main.py`](backend/app/main.py) calls it after
   creating tables — **but only when `SEED_DEMO_USERS=true`** (the default in
   development; forced off in production).

For production you disable demo seeding and instead bootstrap a single admin
from environment variables via `crud.ensure_admin()`:

```bash
ENVIRONMENT=production SEED_DEMO_USERS=false \
ADMIN_USERNAME=admin ADMIN_PASSWORD='<strong-password>' \
SECRET_KEY="$(openssl rand -hex 32)" \
docker compose up -d
```

---

## Running the tests

The suite runs against a dedicated `appointments_test` database inside the
Postgres container.

```bash
docker compose --profile test run --rm backend-test
```

This starts Postgres (if needed) and runs `pytest -v` in the backend image.
Expected: **12 passed**.

The tests cover:

- Login success/failure and the admin flag.
- Unauthenticated / invalid-token requests are rejected (401).
- A regular user sees and manages **only their own** bookings.
- A regular user **cannot** read/update/delete another user's booking (404).
- An **admin** sees **all** bookings and can manage any of them.

---

## API overview

Base path: `/api`. All booking routes require an `Authorization: Bearer <token>` header.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/login` | public | Returns `{ access_token, token_type, user }` |
| GET | `/api/me` | user | Current user profile |
| GET | `/api/bookings` | user | Admin → all bookings; user → only their own |
| POST | `/api/bookings` | user | Create a booking for the current user |
| GET | `/api/bookings/{id}` | user | Owner or admin only |
| PUT | `/api/bookings/{id}` | user | Update time slot (owner or admin) |
| DELETE | `/api/bookings/{id}` | user | Delete booking (owner or admin) |

### Example (curl)

```bash
# Log in and capture the token
TOKEN=$(curl -s -X POST http://localhost:8000/api/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"alice123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# Create a booking
curl -X POST http://localhost:8000/api/bookings \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"time_slot":"10am-11am"}'

# List your bookings
curl http://localhost:8000/api/bookings -H "Authorization: Bearer $TOKEN"
```

---

## Authorization rules

- `GET /api/bookings` returns **all** bookings for admins, but only the caller's
  own bookings for regular users — this fulfills "only admins can view all appointments."
- A regular user may only read/update/delete their **own** bookings. Requesting a
  booking they don't own returns **404** (rather than 403) so the API doesn't leak
  whether that booking exists.
- Admins may manage any booking (a reasonable superset of "view all").
- The JWT only carries the username; `is_admin` is always re-read from the
  database on each request, so a token can't grant privileges the account lacks.

---

## Project structure

```
.
├── docker-compose.yml            # db + backend + frontend (+ test profile)
├── docker/init-test-db.sql       # creates the appointments_test database
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py               # FastAPI app, lifespan: create tables + seed
│   │   ├── config.py             # env-driven settings (DATABASE_URL, SECRET_KEY, …)
│   │   ├── db.py                 # engine, session, get_db dependency
│   │   ├── models.py             # User, Booking ORM models
│   │   ├── schemas.py            # Pydantic request/response models
│   │   ├── crud.py               # DB helpers + bcrypt password hashing
│   │   ├── security.py           # JWT + current-user / admin dependencies
│   │   └── routers/
│   │       ├── auth.py           # /api/login, /api/me
│   │       └── bookings.py       # booking CRUD with authorization
│   └── tests/
│       ├── conftest.py           # schema setup + per-test truncate/reseed
│       └── test_app.py           # auth + authorization tests
└── frontend/
    ├── Dockerfile                # Vite build -> nginx
    ├── nginx.conf                # serves SPA, proxies /api to backend
    ├── package.json
    ├── vite.config.js            # dev proxy /api -> localhost:8000
    └── src/
        ├── main.jsx / App.jsx    # router + providers
        ├── auth.jsx              # auth context + ProtectedRoute
        ├── api.js                # fetch wrapper (attaches bearer token)
        └── pages/
            ├── Login.jsx         # username/password form
            └── Booking.jsx       # create / list / edit / delete bookings
```

---

## Running without Docker (optional)

**Backend** (needs a Postgres reachable at `DATABASE_URL`):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/appointments
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173, proxies /api to localhost:8000
```

**Tests** (point at a running Postgres):

```bash
cd backend
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/appointments_test pytest -v
```

---

## Configuration

Environment variables (see `.env.example`). docker-compose reads a `.env` file
automatically, so override any of these there without editing YAML.

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENVIRONMENT` | `development` | `production` enables the startup safety checks below |
| `DATABASE_URL` | local Postgres | SQLAlchemy connection URL |
| `SECRET_KEY` | `dev-secret-change-me` | JWT signing key — **override in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime |
| `CORS_ORIGINS` | localhost dev origins | Allowed browser origins |
| `SEED_DEMO_USERS` | `true` (dev) / `false` (prod) | Create admin/alice/bob on startup |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | unset | Bootstrap one admin in production |

---

## Production considerations

**Built in and enforced:**

- **Fail-fast config validation** ([`config.validate_config`](backend/app/config.py)):
  when `ENVIRONMENT=production`, the app refuses to start if `SECRET_KEY` is the
  default/weak, if demo seeding is on, or if CORS still allows localhost.
- **No default credentials in production** — demo users are gated behind
  `SEED_DEMO_USERS`; the first admin is bootstrapped from env instead.
- **Passwords** bcrypt-hashed; hashes never leave the API. The JWT carries only
  the username, so `is_admin` is always re-read from the DB (a token can't
  escalate privileges).
- **Containers** run as a non-root user; images have `.dockerignore`, healthchecks,
  and `restart: unless-stopped`; the frontend nginx adds gzip, cache headers, and
  baseline security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`).

**Recommended before a real production deploy (not included here):**

- **Database migrations** — this app uses `Base.metadata.create_all` for
  simplicity. Introduce **Alembic** so schema changes are versioned and reviewable.
- **TLS/HTTPS** terminated at a load balancer or reverse proxy; set
  `X-Forwarded-Proto` and mark cookies/redirects secure.
- **Token storage** — the SPA keeps the JWT in `localStorage` (simple, but exposed
  to XSS). For higher security, switch to httpOnly, `Secure`, `SameSite` cookies.
- **Login brute-force protection** — add rate limiting on `/api/login`
  (e.g. a reverse-proxy limiter or Redis-backed counter).
- **Secrets management** — inject `SECRET_KEY` / DB credentials from a secrets
  manager (not a committed `.env`).
- **Horizontal scaling** — run the API under multiple workers
  (`uvicorn --workers` or gunicorn + `UvicornWorker`) behind the load balancer;
  the app is already stateless, so this is a config change.
- **Observability** — structured logging, request tracing, and metrics.

## Notes

- Data persists in the `pgdata` Docker volume across restarts. Reset with
  `docker compose down -v`.
- Passwords are hashed with bcrypt; the API never returns password hashes.
