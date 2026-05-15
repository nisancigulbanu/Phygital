create table if not exists brands (
    id bigserial primary key,
    name text unique not null,
    eco_score integer check (eco_score between 1 and 10),
    source text,
    updated_at timestamptz default now()
);

create table if not exists analyses (
    id uuid primary key,
    user_id text not null,
    fabric_data jsonb not null,
    quality text not null,
    product_name text,
    brand text,
    source_url text,
    price double precision default 0,
    recommendation text not null,
    created_at timestamptz default now()
);

insert into brands (name, eco_score, source)
values
    ('zara', 3, 'seed'),
    ('hm', 4, 'seed'),
    ('mango', 5, 'seed'),
    ('uniqlo', 6, 'seed'),
    ('patagonia', 9, 'seed'),
    ('lcw', 4, 'seed')
on conflict (name) do update
set eco_score = excluded.eco_score,
    source = excluded.source,
    updated_at = now();
