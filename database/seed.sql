-- =====================================================================
-- CareConfide Demo Seed Data
-- All data below is FICTIONAL and for hackathon demonstration only.
-- Run this AFTER schema.sql and AFTER creating the corresponding
-- Supabase Auth users (see README for the demo credential list).
-- Replace the placeholder UUIDs with the real auth.users ids you get
-- back from Supabase when you create each demo user.
-- =====================================================================

-- Demo professionals (no auth login required for these three; they are
-- shown in the matching page as bookable demo professionals).

insert into users (id, email, role) values
  ('11111111-1111-1111-1111-111111111101', 'dr.amara.owens@demo.careconfide.app', 'professional'),
  ('11111111-1111-1111-1111-111111111102', 'dr.rajesh.menon@demo.careconfide.app', 'professional'),
  ('11111111-1111-1111-1111-111111111103', 'dr.lucia.ferreira@demo.careconfide.app', 'professional')
on conflict (id) do nothing;

insert into professionals (user_id, full_name, specialty, languages, consultation_modes, bio, is_demo) values
  ('11111111-1111-1111-1111-111111111101', 'Dr. Amara Owens', 'Sexual & Reproductive Health',
    array['English', 'French'], array['chat', 'video'],
    'Focuses on confidential, judgment-free reproductive health consultations.', true),
  ('11111111-1111-1111-1111-111111111102', 'Dr. Rajesh Menon', 'Mental Health & Counseling',
    array['English', 'Hindi', 'Tamil'], array['chat', 'audio'],
    'Specializes in anxiety, stress, and sensitive personal concerns.', true),
  ('11111111-1111-1111-1111-111111111103', 'Dr. Lucia Ferreira', 'General & Sensitive Health',
    array['English', 'Portuguese', 'Spanish'], array['chat', 'video', 'audio'],
    'General practitioner with a focus on stigmatized health topics.', true)
on conflict (user_id) do nothing;

-- Demo patients

insert into users (id, email, role) values
  ('22222222-2222-2222-2222-222222222201', 'demo.patient1@demo.careconfide.app', 'patient'),
  ('22222222-2222-2222-2222-222222222202', 'demo.patient2@demo.careconfide.app', 'patient')
on conflict (id) do nothing;

insert into patients (user_id, display_id, preferred_language) values
  ('22222222-2222-2222-2222-222222222201', 'Patient #A19F2', 'en'),
  ('22222222-2222-2222-2222-222222222202', 'Patient #B77C4', 'en')
on conflict (user_id) do nothing;

insert into identity_vault (user_id, full_name, date_of_birth, phone, identity_verified, verification_method) values
  ('22222222-2222-2222-2222-222222222201', 'Jordan Ellis', '1996-04-12', '+1-555-0100', true, 'demo'),
  ('22222222-2222-2222-2222-222222222202', 'Priya Nathan', '1991-11-02', '+1-555-0101', true, 'demo')
on conflict (user_id) do nothing;

-- A fictional completed intake + clinical profile + consultation, so
-- judges can see the doctor-side view immediately without doing intake.

with p1 as (select id from patients where user_id = '22222222-2222-2222-2222-222222222201'),
     doc1 as (select id from professionals where user_id = '11111111-1111-1111-1111-111111111102')
insert into intake_sessions (id, patient_id, status, concern_category, ai_mode)
select '33333333-3333-3333-3333-333333333301', p1.id, 'shared', 'Anxiety & Stress', 'demo' from p1
on conflict (id) do nothing;

insert into intake_messages (session_id, sender, content) values
  ('33333333-3333-3333-3333-333333333301', 'patient', 'I have been feeling constantly anxious for the past three weeks and it is affecting my sleep.'),
  ('33333333-3333-3333-3333-333333333301', 'ai', 'Thank you for sharing that. Can you tell me if anything specific triggers the anxiety, and whether you have experienced this before?')
on conflict do nothing;

with p1 as (select id from patients where user_id = '22222222-2222-2222-2222-222222222201')
insert into clinical_profiles (id, intake_session_id, patient_id, concern_category, symptoms, duration, medical_history, medications, allergies, additional_notes, ai_summary, confirmed_by_patient)
select
  '44444444-4444-4444-4444-444444444401',
  '33333333-3333-3333-3333-333333333301',
  p1.id,
  'Anxiety & Stress',
  array['persistent worry', 'difficulty sleeping', 'racing thoughts'],
  '3 weeks',
  array['no prior diagnosed mental health condition'],
  array['none currently'],
  array['none reported'],
  'Symptoms appear linked to a recent job change.',
  'Patient reports a 3-week history of persistent anxiety and sleep disruption, with no prior diagnosis, possibly linked to a recent life change. Recommend professional follow-up; this is not a diagnosis.',
  true
from p1
on conflict (id) do nothing;

with p1 as (select id from patients where user_id = '22222222-2222-2222-2222-222222222201'),
     doc1 as (select id from professionals where user_id = '11111111-1111-1111-1111-111111111102')
insert into consultations (id, patient_id, professional_id, clinical_profile_id, mode, status)
select '55555555-5555-5555-5555-555555555501', p1.id, doc1.id, '44444444-4444-4444-4444-444444444401', 'chat', 'active'
from p1, doc1
on conflict (id) do nothing;

insert into consultation_messages (consultation_id, sender_role, content) values
  ('55555555-5555-5555-5555-555555555501', 'professional', 'Hello, I have reviewed your intake summary. How have you been sleeping the last couple of nights?'),
  ('55555555-5555-5555-5555-555555555501', 'patient', 'A little better, but I still wake up around 3am most nights.')
on conflict do nothing;

with p1 as (select id from patients where user_id = '22222222-2222-2222-2222-222222222201'),
     doc1 as (select id from professionals where user_id = '11111111-1111-1111-1111-111111111102')
insert into consents (patient_id, professional_id, consultation_id, scope, granted, granted_at)
select p1.id, doc1.id, '55555555-5555-5555-5555-555555555501', 'clinical_data', true, now()
from p1, doc1
on conflict do nothing;

with p1 as (select id from patients where user_id = '22222222-2222-2222-2222-222222222201'),
     doc1 as (select id from professionals where user_id = '11111111-1111-1111-1111-111111111102')
insert into consents (patient_id, professional_id, consultation_id, scope, granted, granted_at)
select p1.id, doc1.id, '55555555-5555-5555-5555-555555555501', 'identity_data', false, null
from p1, doc1
on conflict do nothing;

insert into audit_logs (actor_user_id, actor_role, action, target_type, target_id, metadata) values
  ('11111111-1111-1111-1111-111111111102', 'professional', 'VIEW_CLINICAL', 'clinical_profile', '44444444-4444-4444-4444-444444444401', '{"note": "demo seed"}');
