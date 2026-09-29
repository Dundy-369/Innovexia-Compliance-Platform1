-- Innovexia prototype backend schema.
-- Run in Supabase SQL Editor only after reviewing existing tables.
-- Existing tables are not altered here. New tables are created only if absent.

create table if not exists public.tenders (
  id uuid primary key default gen_random_uuid(),
  tender_number text not null unique,
  title text not null,
  description text,
  requirements jsonb not null default '{}'::jsonb,
  status text not null default 'draft',
  created_by uuid,
  created_at timestamptz not null default now()
);

-- If your project already has public.bids, do not replace it.
-- This table definition is for a fresh prototype database only.
create table if not exists public.bids (
  id uuid primary key default gen_random_uuid(),
  bidder_id uuid not null references public.bidders(id) on delete cascade,
  tender_id uuid references public.tenders(id) on delete set null,
  tender_number text,
  tender_title text,
  tender_requirements jsonb not null default '{}'::jsonb,
  status text not null default 'submitted',
  decision_remarks text,
  decision_by uuid,
  decision_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.bidder_documents (
  id uuid primary key default gen_random_uuid(),
  bid_id uuid not null references public.bids(id) on delete cascade,
  document_type text not null check (document_type in ('PAN','GST','UDYAM','OTHER')),
  file_name text not null,
  storage_path text not null,
  mime_type text,
  upload_status text not null default 'UPLOADED',
  created_at timestamptz not null default now()
);

create table if not exists public.notifications (
  id uuid primary key default gen_random_uuid(),
  bid_id uuid references public.bids(id) on delete cascade,
  recipient_id uuid,
  title text not null,
  message text not null,
  is_read boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  bid_id uuid references public.bids(id) on delete set null,
  actor_id uuid,
  actor_role text,
  action text not null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_bids_bidder_id on public.bids(bidder_id);
create index if not exists idx_bidder_documents_bid_id on public.bidder_documents(bid_id);
create index if not exists idx_notifications_recipient_id on public.notifications(recipient_id);
create index if not exists idx_audit_logs_bid_id on public.audit_logs(bid_id);

-- Create the private storage bucket manually in Supabase Storage:
-- bidder-documents
-- Do not expose uploaded bidder documents publicly.
