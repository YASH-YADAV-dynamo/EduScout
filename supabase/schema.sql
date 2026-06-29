-- EduScout Supabase Schema
-- Run this in your Supabase project: Dashboard → SQL Editor → Run

-- ============================================================
-- TABLES
-- ============================================================

create table if not exists users (
    id               bigserial primary key,
    email            text unique not null,
    name             text not null,
    public_id        text unique,
    google_sub       text unique,
    esid             text unique,
    overall_score    real default 0
);

create table if not exists study_plans (
    id       bigserial primary key,
    user_id  bigint not null references users(id),
    title    text not null,
    status   text not null default 'active'
);

create table if not exists profiles (
    plan_id                 bigint primary key references study_plans(id),
    degree                  text,
    major                   text,
    cgpa                    real,
    budget                  real,
    budget_range            text,
    target_intake           text,
    priority                text,
    region                  text,
    resume_url              text,
    -- V2 deep profile
    university_name         text,
    institution_tier        text,
    target_degree           text,
    target_field            text,
    gpa_scale               text,
    exams_json              text,
    research_json           text,
    work_json               text,
    extracurriculars_json   text,
    budget_usd              real,
    living_budget_usd       real,
    scholarship_seeking     integer default 0,
    funding_open            integer default 0,
    preferred_countries_json text,
    campus_type             text,
    campus_size             text,
    visa_constraints        text,
    post_study_goal         text,
    candidate_score_json    text,
    profile_completeness    real default 0,
    intake_semester         text,
    resume_outline_json     text,
    transcript_outline_json text,
    form_stage_complete     integer default 0
);

create table if not exists universities (
    id                      bigserial primary key,
    plan_id                 bigint not null references study_plans(id),
    university_name         text not null,
    category                text not null default 'target',
    program_name            text,
    degree_type             text,
    country                 text,
    qs_rank                 integer,
    subject_rank            integer,
    acceptance_rate         real,
    tuition_usd             real,
    deadline                text,
    funding_notes           text,
    match_score             real,
    match_breakdown_json    text,
    risk_note               text,
    research_metadata_json  text
);

create table if not exists tasks (
    id        bigserial primary key,
    plan_id   bigint not null references study_plans(id),
    title     text not null,
    due_date  text,
    status    text not null default 'pending'
);

create table if not exists calendar_events (
    id        bigserial primary key,
    plan_id   bigint not null references study_plans(id),
    event_id  text not null,
    title     text not null
);

create table if not exists link_codes (
    id         bigserial primary key,
    user_id    bigint not null references users(id),
    code       text not null unique,
    expires_at text not null,
    used       integer not null default 0
);

create table if not exists linked_channels (
    id            bigserial primary key,
    user_id       bigint not null references users(id),
    channel_type  text not null,
    external_id   text not null,
    unique(channel_type, external_id)
);

create table if not exists onboarding_stages (
    id                  bigserial primary key,
    plan_id             bigint not null references study_plans(id),
    stage               integer not null,
    completed_at        text,
    data_snapshot_json  text,
    unique(plan_id, stage)
);

create table if not exists college_subscriptions (
    id              bigserial primary key,
    user_id         bigint not null references users(id),
    university_id   bigint not null references universities(id),
    subscribed_at   text not null default (to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')),
    unique(user_id, university_id)
);

create table if not exists documents (
    id                  bigserial primary key,
    plan_id             bigint not null references study_plans(id),
    doc_type            text not null,
    format              text not null default 'markdown',
    content             text not null,
    target_university   text,
    version             integer not null default 1,
    created_at          text not null default (to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'))
);

-- ============================================================
-- INDEXES
-- ============================================================

create index if not exists idx_study_plans_user_id      on study_plans(user_id);
create index if not exists idx_universities_plan_id     on universities(plan_id);
create index if not exists idx_tasks_plan_id            on tasks(plan_id);
create index if not exists idx_tasks_due_date           on tasks(due_date);
create index if not exists idx_documents_plan_id        on documents(plan_id);
create index if not exists idx_linked_channels_user_id  on linked_channels(user_id);
create index if not exists idx_college_subs_user_id     on college_subscriptions(user_id);
create index if not exists idx_onboarding_stages_plan   on onboarding_stages(plan_id);

-- ============================================================
-- ROW LEVEL SECURITY (optional — disable if using service key only)
-- ============================================================
-- alter table users enable row level security;
-- ... add policies as needed for your auth setup
