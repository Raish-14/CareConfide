# CareConfide

**Talk Freely. Heal Confidently.**

CareConfide is a hackathon prototype of a privacy-first healthcare platform
for sensitive health concerns. It is **not** an anonymous platform and never
claims full anonymity or untraceability — the goal is *minimum necessary
identity exposure* while still allowing compliant, professional care.

> ⚠️ **This is a hackathon MVP, not a production healthcare application.**
> It does not perform real diagnosis, does not issue prescriptions, and
> should never be used for real medical decisions or emergencies.

---

## 1. What it demonstrates

- Patient registration/login and a patient dashboard
- An AI-assisted intake conversation that structures a patient's sensitive
  concern into a clear summary — without diagnosing
- A review step where the patient confirms exactly what will be shared
- Matching with demo healthcare professionals by specialty/language/mode
- A professional dashboard and case view where identity information is
  **visually and architecturally separated** from clinical information,
  and only shown if the patient has explicitly consented
- A simulated consultation interface (chat + placeholder audio/video controls)
- Consent state and a basic audit log of sensitive actions (identity views,
  clinical views, consent changes)

---

## 2. Architecture

```
React (Vite) Frontend
        |
        | HTTPS REST API
        v
FastAPI Backend
        |
   ┌────┼───────────────┐
   v    v               v
  AI   Supabase      Auth / Consent
      PostgreSQL
        |
   ┌────┴────────────┐
   v                 v
Identity Vault   Clinical Data
```

Identity information (`identity_vault`) and clinical information
(`clinical_profiles`, `intake_sessions`) live in separate tables. The API
only attaches identity data to a doctor's case view when an explicit
`identity_data` consent record has been granted for that consultation, and
every such access is written to `audit_logs`.

### Data mode: Supabase (real) vs. in-memory demo (fallback)

The backend has a real Supabase persistence layer (`app/services/supabase_db.py`)
that reads and writes the actual Postgres tables created by `database/schema.sql`:
`users`, `patients`, `identity_vault`, `professionals`, `intake_sessions`,
`intake_messages`, `clinical_profiles`, `consultations`, `consultation_messages`,
`consents`, and `audit_logs`.

`app/services/db.py` selects the active backend **once**, at process startup:

- If `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are both set, every API
  route reads/writes real Supabase tables via `SupabaseDatabase`. If a
  Supabase call fails (bad credentials, network issue, constraint
  violation, RLS denial, etc.), it raises `DatabaseError`, which
  `app/main.py`'s exception handler turns into an explicit **HTTP 503**
  with the real underlying error — the app never silently falls back to
  memory after startup, and a 200/201 response always means the row
  genuinely exists in Supabase.
- If they are not set, the backend falls back to `MemoryDatabase`
  (`app/services/memory_db.py`), an explicit, documented demo mode backed
  by `app/core/store.py`'s `InMemoryStore` (pre-seeded with the same
  fictional demo data as before). This mode still works end-to-end for a
  quick demo with zero setup, but data does not survive a restart.

Both implementations expose the exact same set of methods (e.g.
`create_patient`, `get_consultation`, `add_consultation_message`,
`log_audit`, ...), so the API route handlers in `app/api/*.py` call `db.*`
without needing to know or care which backend is active.

**One deliberate, non-schema-changing compromise:** `professionals.availability`
is not a column in `database/schema.sql` (it was only ever a display
convenience in the original prototype). Rather than modify the schema for
that, `SupabaseDatabase` derives a reasonable value at read time (fixed
office-hours text for seeded demo professionals, "By request" for newly
registered ones) — see the comment on `_availability_for` in
`app/services/supabase_db.py`. No other field required this treatment.

**Known limitation:** passwords are intentionally never written to the
`users` table (per the schema's own note: "Do not store passwords
manually. Use Supabase Auth."). Since this prototype does not wire up
full Supabase Auth, password verification still uses the same
process-local, in-memory map as before (`app/api/auth.py`'s
`_passwords`). This means the *account* (row in `users`/`patients`/etc.)
persists correctly in Supabase across a restart, but a freshly-registered
account's password check resets on restart (any password will then be
accepted for it, same as the pre-seeded demo accounts). This is called
out again in Limitations below.

### AI intake: live vs. demo mode

`POST /api/ai/intake` calls the Anthropic Messages API when `AI_API_KEY` is
set. If it is not set, or the live call fails for any reason, the backend
automatically falls back to a deterministic **"Demo AI mode"** so the app
never crashes and judges can try the full flow without any credentials.

---

## 3. Project structure

```
careconfide/
  frontend/
    src/
      components/   Button, Card, Disclaimer, Logo, VeilMotif, ProtectedRoute
      pages/         Landing, HowItWorks, Login, Register, patient/*, doctor/*
      layouts/       PublicLayout, PatientLayout, DoctorLayout
      services/      api.js (REST client)
      hooks/         useAuth.jsx
  backend/
    app/
      main.py
      api/           auth, patient, ai, professionals, consultations, doctor
      schemas/       Pydantic request/response models
      services/
        db.py            selects SupabaseDatabase or MemoryDatabase at startup
        supabase_db.py   real Supabase persistence (all 11 tables)
        supabase_client.py  lazy Supabase client factory (service-role key)
        memory_db.py     in-memory fallback, same method surface
        db_errors.py     DatabaseError — surfaced as HTTP 503, never swallowed
        ai_intake.py     live + mock AI
      core:          config.py, store.py (in-memory seed data), security.py
    tests/           test_supabase_db.py, test_memory_db.py, fake_supabase.py
    scripts/         verify_persistence.py (end-to-end restart-survival check)
  database/
    schema.sql
    seed.sql
  .env.example
  .gitignore
  README.md
```

---

## 4. Local development

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # fill in AI_API_KEY / Supabase vars if you have them
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000`. Check `http://localhost:8000/api/health`
to see whether it's running in demo or live mode for data/AI.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env      # VITE_API_URL=http://localhost:8000
npm run dev
```

The app is now at `http://localhost:5173`.

### Try it immediately (no setup)

On first login, the login page lists pre-seeded demo accounts (one patient,
three professionals). **Any password works for these accounts.** A demo
patient case is pre-populated so the professional dashboard is never empty.

---

## 5. Supabase setup (optional, for persistent data)

1. Create a Supabase project.
2. In the SQL editor, run `database/schema.sql`, then `database/seed.sql`
   (after creating matching Supabase Auth users for the seeded ids — see
   comments at the top of `seed.sql`).
3. Set `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY`
   in `backend/.env`.
4. Enable Row Level Security and add policies as described in the comment
   block at the bottom of `database/schema.sql`.

Without this setup, the backend automatically uses its in-memory demo store.

---

## 6. AI setup (optional, for live AI intake)

Set `AI_API_KEY` (and optionally `AI_MODEL`, default `claude-sonnet-4-6`) in
`backend/.env`. The key is used **only server-side** — it is never sent to
or readable from the frontend. Without it, intake automatically runs in
"Demo AI mode" with deterministic responses.

---

## 6.5. Testing the persistence layer

Two layers of tests are included:

**Unit tests (no network, no real Supabase project needed).** These run
the real `SupabaseDatabase` code against a fake in-process Postgrest
client (`tests/fake_supabase.py`), including a test that throws away the
database instance and builds a fresh one against the same backing data —
simulating a backend restart — to prove nothing needed for persistence
was being kept only in Python memory.

```bash
cd backend
python3 tests/test_supabase_db.py   # SupabaseDatabase logic + restart simulation
python3 tests/test_memory_db.py     # in-memory fallback sanity checks
```

(Both are also plain `pytest`-discoverable if you have `pytest` installed:
`pytest tests/`.)

**End-to-end verification against your real Supabase project.** This
drives the actual running backend over HTTP and checks the Supabase
Table Editor / a real restart:

```bash
# terminal 1
cd backend && uvicorn app.main:app --reload --port 8000

# terminal 2
cd backend
python3 scripts/verify_persistence.py seed
# -> registers a patient, runs an intake, confirms it, requests a
#    consultation, sends a message; prints the ids to look up in the
#    Supabase Table Editor.

# now actually restart the backend (Ctrl+C, then start it again)

python3 scripts/verify_persistence.py check
# -> logs back in and confirms every one of the records created above
#    is still readable — proving it came from Supabase, not memory.
```

---

## 7. Environment variables

| Variable | Where | Required | Purpose |
|---|---|---|---|
| `SUPABASE_URL` | backend | No | Supabase project URL |
| `SUPABASE_ANON_KEY` | backend | No | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | backend | No | Supabase service role key (server-only) |
| `AI_API_KEY` | backend | No | Anthropic API key for live AI intake |
| `AI_MODEL` | backend | No | Model name (default `claude-sonnet-4-6`) |
| `CORS_ORIGINS` | backend | No | Comma-separated allowed frontend origins |
| `VITE_API_URL` | frontend | No | Backend base URL (default `http://localhost:8000`) |

---

## 8. Deployment

- **Frontend → Vercel**: import the `frontend/` directory, set the build
  command to `npm run build` and output directory to `dist`, and set
  `VITE_API_URL` to your deployed backend URL.
- **Backend → Render**: create a Web Service pointing at `backend/`, build
  command `pip install -r requirements.txt`, start command
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set the environment
  variables from the table above (`CORS_ORIGINS` should include your Vercel
  domain).
- **Database → Supabase**: as described in section 5.

---

## 9. Demo credentials

Any pre-seeded account works with **any password**:

| Role | Email |
|---|---|
| Patient | `demo.patient1@demo.careconfide.app` |
| Professional (Mental Health) | (see `/api/auth/demo-accounts`) |
| Professional (Reproductive Health) | (see `/api/auth/demo-accounts`) |
| Professional (General) | (see `/api/auth/demo-accounts`) |

The login page also renders these as one-click buttons.

---

## 10. Limitations

- Demo authentication issues a simple opaque session token equal to the
  user id, rather than verifying a real Supabase Auth JWT — documented in
  `backend/app/core/security.py`. This is independent of the data
  backend: it's true whether Supabase or the in-memory store is active.
  Swap in Supabase JWT verification for production use.
- **Passwords are not persisted in Supabase** (by design — the schema's
  own comment says not to store them there; that's Supabase Auth's job,
  which this prototype does not fully wire up). The account itself
  (`users`/`patients`/`identity_vault`/`professionals` rows) persists
  correctly and survives a restart; the *password check* for accounts
  registered via `/api/auth/register` resets on restart, after which any
  password is accepted for that account — the same behavior the
  pre-seeded demo accounts have always had. Wiring up real Supabase Auth
  would close this gap but is a larger, separate change.
- `professionals.availability` has no column in `database/schema.sql`; it
  is derived at read time rather than stored (see the persistence section
  above). Purely cosmetic — no other field required this treatment.
- When Supabase is NOT configured, the in-memory data store still resets
  whenever the backend process restarts — this is the explicit, intended
  behavior of demo mode, not a bug.
- The consultation interface is a UI simulation only: no real WebRTC
  audio/video is implemented.
- No real identity verification, payment processing, or medical-record
  integrations are implemented, by design (see project scope rules).
- This prototype does not provide medical diagnosis, prescriptions, or
  emergency care. In an emergency, contact local emergency services.

## 11. Features that require external credentials

- **Live AI intake** requires `AI_API_KEY` (Anthropic). Without it, intake
  runs in deterministic Demo AI mode.
- **Real, restart-surviving persistence** requires `SUPABASE_URL` and
  `SUPABASE_SERVICE_ROLE_KEY`. Without them, the backend uses its
  built-in in-memory demo store and data does not survive a restart.
