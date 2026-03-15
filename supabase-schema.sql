create table if not exists public.cars (
  id text primary key,
  current_spot jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists public.parking_history (
  id bigint generated always as identity primary key,
  car_id text not null references public.cars(id) on delete cascade,
  spot jsonb not null,
  saved_at timestamptz not null default now()
);

create index if not exists parking_history_car_id_saved_at_idx
  on public.parking_history (car_id, saved_at desc);

alter table public.cars enable row level security;
alter table public.parking_history enable row level security;

drop policy if exists "anon cars read" on public.cars;
create policy "anon cars read"
  on public.cars
  for select
  to anon
  using (true);

drop policy if exists "anon cars write" on public.cars;
create policy "anon cars write"
  on public.cars
  for all
  to anon
  using (true)
  with check (true);

drop policy if exists "anon history read" on public.parking_history;
create policy "anon history read"
  on public.parking_history
  for select
  to anon
  using (true);

drop policy if exists "anon history write" on public.parking_history;
create policy "anon history write"
  on public.parking_history
  for all
  to anon
  using (true)
  with check (true);
