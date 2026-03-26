-- Initial Supabase schema

create extension if not exists "pgcrypto";

create table if not exists public.accounts (
    id uuid primary key default gen_random_uuid(),
    account_id text not null unique,
    display_name text,
    phase text,
    is_shadowbanned boolean not null default false,
    ai_provider text,
    ai_model text,
    forbidden_content text[] not null default '{}',
    forbidden_actions text[] not null default '{}',
    post_frequency integer,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.posts (
    id uuid primary key default gen_random_uuid(),
    account_id text not null references public.accounts(account_id) on update cascade on delete cascade,
    content text not null,
    purpose text,
    media_paths text[] not null default '{}',
    scheduled_at timestamptz,
    posted_at timestamptz,
    is_posted boolean not null default false,
    is_failed boolean not null default false,
    likes integer not null default 0,
    retweets integer not null default 0,
    replies integer not null default 0,
    bookmarks integer not null default 0,
    impressions integer not null default 0,
    tweet_id text,
    created_at timestamptz not null default now()
);

create table if not exists public.knowledge (
    id uuid primary key default gen_random_uuid(),
    scope text not null,
    account_id text references public.accounts(account_id) on update cascade on delete cascade,
    content text not null,
    confidence text not null,
    category text,
    validation_count integer not null default 0,
    last_validated_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint knowledge_scope_account_check check (
        (scope = 'global' and account_id is null)
        or (scope = 'account-specific' and account_id is not null)
    )
);

create table if not exists public.tactics (
    id uuid primary key default gen_random_uuid(),
    account_id text not null references public.accounts(account_id) on update cascade on delete cascade,
    description text not null,
    knowledge_id uuid references public.knowledge(id) on update cascade on delete set null,
    success_count integer not null default 0,
    fail_count integer not null default 0,
    score_threshold integer not null default 50,
    created_at timestamptz not null default now()
);

create table if not exists public.daily_reports (
    id uuid primary key default gen_random_uuid(),
    account_id text not null references public.accounts(account_id) on update cascade on delete cascade,
    report_date date not null,
    reflection text,
    hypothesis text,
    pm_instruction text,
    created_at timestamptz not null default now(),
    constraint daily_reports_account_date_unique unique (account_id, report_date)
);

create table if not exists public.weekly_reports (
    id uuid primary key default gen_random_uuid(),
    week_start date not null,
    follower_summary jsonb,
    impression_summary jsonb,
    tactics_summary text,
    evaluation text,
    next_week_plan text,
    created_at timestamptz not null default now(),
    constraint weekly_reports_week_start_unique unique (week_start)
);

create table if not exists public.schedules (
    id uuid primary key default gen_random_uuid(),
    account_id text not null references public.accounts(account_id) on update cascade on delete cascade,
    post_id uuid references public.posts(id) on update cascade on delete set null,
    scheduled_at timestamptz not null,
    is_checked boolean not null default false,
    created_at timestamptz not null default now()
);

create table if not exists public.notifications (
    id uuid primary key default gen_random_uuid(),
    type text not null,
    account_id text references public.accounts(account_id) on update cascade on delete set null,
    message text not null,
    is_read boolean not null default false,
    created_at timestamptz not null default now()
);

create table if not exists public.ai_action_models (
    id uuid primary key default gen_random_uuid(),
    action_name text not null unique,
    ai_provider text not null,
    ai_model text not null,
    updated_at timestamptz not null default now()
);

-- Required indexes
create index if not exists idx_posts_account_id on public.posts (account_id);
create index if not exists idx_posts_scheduled_at on public.posts (scheduled_at);
create index if not exists idx_posts_posted_at on public.posts (posted_at);

create index if not exists idx_knowledge_scope on public.knowledge (scope);
create index if not exists idx_knowledge_account_id on public.knowledge (account_id);
create index if not exists idx_knowledge_confidence on public.knowledge (confidence);

create index if not exists idx_daily_reports_account_id on public.daily_reports (account_id);
create index if not exists idx_daily_reports_report_date on public.daily_reports (report_date);

create index if not exists idx_notifications_is_read on public.notifications (is_read);
create index if not exists idx_notifications_created_at on public.notifications (created_at);

create index if not exists idx_schedules_account_id on public.schedules (account_id);
create index if not exists idx_schedules_scheduled_at on public.schedules (scheduled_at);
create index if not exists idx_schedules_is_checked on public.schedules (is_checked);

-- Enable RLS on all tables
alter table public.accounts enable row level security;
alter table public.posts enable row level security;
alter table public.knowledge enable row level security;
alter table public.tactics enable row level security;
alter table public.daily_reports enable row level security;
alter table public.weekly_reports enable row level security;
alter table public.schedules enable row level security;
alter table public.notifications enable row level security;
alter table public.ai_action_models enable row level security;
