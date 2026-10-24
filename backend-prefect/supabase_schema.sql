-- Ejecutar en Supabase > SQL Editor
create table if not exists public.users (
    id uuid primary key default gen_random_uuid(),
    username text unique not null,
    password_hash text not null,
    mfa_status text not null default 'DISABLED'
        check (mfa_status in ('DISABLED', 'PENDING_VERIFICATION', 'ACTIVE')),
    totp_secret text,
    backup_codes jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

-- El backend usa la service_role key, así que RLS puede quedar activado sin políticas
-- públicas: nadie desde el cliente anónimo puede leer secretos ni hashes.
alter table public.users enable row level security;
