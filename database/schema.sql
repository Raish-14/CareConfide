-- =====================================================================
-- CareConfide Database Schema
-- Target: Supabase PostgreSQL
--
-- Design principle: identity information and clinical information are
-- stored in physically separate tables (identity_vault vs
-- clinical_profiles / intake_sessions) so that access to clinical data
-- does not automatically expose identity data. This is a logical /
-- architectural separation for the hackathon demo, NOT a cryptographic
-- anonymity guarantee. CareConfide never claims full anonymity.
-- =====================================================================

create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------
-- users
-- Mirrors Supabase auth.users (id must match auth.users.id).
-- Holds only the minimum info needed to route the account.
-- ---------------------------------------------------------------------
create table if not exists users (
  id uuid primary key default uuid_generate_v4(), -- should equal auth.users.id
  email text unique not null,
  role text not null check (role in ('patient', 'professional', 'admin')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_users_role on users(role);

-- ---------------------------------------------------------------------
-- identity_vault
-- Real-world identity information. Separated from clinical_profiles.
-- Only accessible to: the owning patient, and a professional with an
-- active, consented consultation (enforced at the API layer / RLS).
-- ---------------------------------------------------------------------
create table if not exists identity_vault (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references users(id) on delete cascade,
  full_name text not null,
  date_of_birth date,
  phone text,
  identity_verified boolean not null default false,
  verification_method text, -- e.g. 'demo', 'document_upload' (demo only)
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id)
);

-- ---------------------------------------------------------------------
-- patients
-- Non-identifying patient profile. References users, not identity.
-- ---------------------------------------------------------------------
create table if not exists patients (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references users(id) on delete cascade,
  display_id text not null unique, -- e.g. "Patient #A19F2" shown to doctors
  preferred_language text default 'en',
  created_at timestamptz not null default now(),
  unique(user_id)
);

create index if not exists idx_patients_user on patients(user_id);

-- ---------------------------------------------------------------------
-- professionals
-- Doctor / clinician profile.
-- ---------------------------------------------------------------------
create table if not exists professionals (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references users(id) on delete cascade,
  full_name text not null, -- professionals' names are intentionally public
  specialty text not null,
  languages text[] not null default '{}',
  consultation_modes text[] not null default '{}', -- e.g. {'chat','video'}
  bio text,
  is_demo boolean not null default false,
  created_at timestamptz not null default now(),
  unique(user_id)
);

create index if not exists idx_professionals_specialty on professionals(specialty);

-- ---------------------------------------------------------------------
-- intake_sessions
-- One per patient's described concern / AI-assisted intake flow.
-- ---------------------------------------------------------------------
create table if not exists intake_sessions (
  id uuid primary key default uuid_generate_v4(),
  patient_id uuid not null references patients(id) on delete cascade,
  status text not null default 'in_progress'
    check (status in ('in_progress', 'ready_for_review', 'shared', 'closed')),
  concern_category text,
  ai_mode text not null default 'live' check (ai_mode in ('live', 'demo')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_intake_sessions_patient on intake_sessions(patient_id);

-- ---------------------------------------------------------------------
-- intake_messages
-- Conversation turns between patient and the AI intake assistant.
-- ---------------------------------------------------------------------
create table if not exists intake_messages (
  id uuid primary key default uuid_generate_v4(),
  session_id uuid not null references intake_sessions(id) on delete cascade,
  sender text not null check (sender in ('patient', 'ai')),
  content text not null,
  structured_json jsonb, -- structured extraction attached to AI turns
  created_at timestamptz not null default now()
);

create index if not exists idx_intake_messages_session on intake_messages(session_id);

-- ---------------------------------------------------------------------
-- clinical_profiles
-- The reviewed, patient-confirmed structured clinical summary that
-- gets shared with a matched professional. No identity fields here.
-- ---------------------------------------------------------------------
create table if not exists clinical_profiles (
  id uuid primary key default uuid_generate_v4(),
  intake_session_id uuid not null references intake_sessions(id) on delete cascade,
  patient_id uuid not null references patients(id) on delete cascade,
  concern_category text,
  symptoms text[] default '{}',
  duration text,
  medical_history text[] default '{}',
  medications text[] default '{}',
  allergies text[] default '{}',
  additional_notes text,
  ai_summary text,
  confirmed_by_patient boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_clinical_profiles_patient on clinical_profiles(patient_id);

-- ---------------------------------------------------------------------
-- consultations
-- Links a patient's clinical_profile to a professional.
-- ---------------------------------------------------------------------
create table if not exists consultations (
  id uuid primary key default uuid_generate_v4(),
  patient_id uuid not null references patients(id) on delete cascade,
  professional_id uuid not null references professionals(id) on delete cascade,
  clinical_profile_id uuid not null references clinical_profiles(id) on delete cascade,
  mode text not null default 'chat' check (mode in ('chat', 'video', 'audio')),
  status text not null default 'requested'
    check (status in ('requested', 'accepted', 'active', 'completed', 'declined', 'cancelled')),
  scheduled_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_consultations_patient on consultations(patient_id);
create index if not exists idx_consultations_professional on consultations(professional_id);
create index if not exists idx_consultations_status on consultations(status);

-- ---------------------------------------------------------------------
-- consultation_messages
-- Simulated in-consultation chat transcript.
-- ---------------------------------------------------------------------
create table if not exists consultation_messages (
  id uuid primary key default uuid_generate_v4(),
  consultation_id uuid not null references consultations(id) on delete cascade,
  sender_role text not null check (sender_role in ('patient', 'professional')),
  content text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_consultation_messages_consultation on consultation_messages(consultation_id);

-- ---------------------------------------------------------------------
-- consents
-- Explicit consent state: what the patient agreed a professional may
-- see, and when identity access is authorized.
-- ---------------------------------------------------------------------
create table if not exists consents (
  id uuid primary key default uuid_generate_v4(),
  patient_id uuid not null references patients(id) on delete cascade,
  professional_id uuid references professionals(id) on delete cascade,
  consultation_id uuid references consultations(id) on delete cascade,
  scope text not null check (scope in ('clinical_data', 'identity_data')),
  granted boolean not null default false,
  granted_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists idx_consents_patient on consents(patient_id);
create index if not exists idx_consents_consultation on consents(consultation_id);

-- ---------------------------------------------------------------------
-- audit_logs
-- Append-only log of sensitive actions (identity access, consent
-- changes, clinical data views).
-- ---------------------------------------------------------------------
create table if not exists audit_logs (
  id uuid primary key default uuid_generate_v4(),
  actor_user_id uuid references users(id),
  actor_role text,
  action text not null, -- e.g. 'VIEW_IDENTITY', 'VIEW_CLINICAL', 'GRANT_CONSENT'
  target_type text,      -- e.g. 'patient', 'consultation', 'clinical_profile'
  target_id uuid,
  metadata jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_audit_logs_actor on audit_logs(actor_user_id);
create index if not exists idx_audit_logs_action on audit_logs(action);
create index if not exists idx_audit_logs_created_at on audit_logs(created_at desc);

-- =====================================================================
-- Notes on Row Level Security (RLS)
-- For the hackathon prototype, enable RLS in Supabase with policies such as:
--   - patients can select/update only rows where user_id = auth.uid()
--   - professionals can select clinical_profiles / consultations only
--     where a matching consultations row exists with their professional_id
--   - identity_vault is selectable only by the owning patient, or by a
--     professional joined through an ACTIVE consultation with a granted
--     'identity_data' consent row.
-- These policies are documented here; for demo speed the FastAPI backend
-- enforces the equivalent checks using the service role key.
-- =====================================================================
