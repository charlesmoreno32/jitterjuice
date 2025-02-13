create table
  public.potions (
    id integer generated by default as identity,
    sku text not null,
    price integer null,
    inventory integer null,
    potion_type integer[] null,
    constraint catalog_pkey primary key (id),
    constraint potions_potion_type_check check ((array_length(potion_type, 1) = 4))
  ) tablespace pg_default;

create table
  public.globals (
    red_ml integer not null default 0,
    gold integer not null default 100,
    green_ml integer generated by default as identity,
    blue_ml integer generated by default as identity,
    dark_ml integer null default 0,
    constraint global_inventory_pkey primary key (gold)
  ) tablespace pg_default;

create table
  public.carts (
    cart_id integer generated by default as identity,
    customer_name text not null,
    constraint carts_pkey primary key (cart_id),
    constraint carts_cart_id_key unique (cart_id)
  ) tablespace pg_default;

create table
  public.cart_items (
    cart_id integer generated by default as identity,
    potion_id integer not null,
    quantity integer null,
    constraint cart_items_pkey primary key (cart_id, potion_id),
    constraint cart_items_cart_id_fkey foreign key (cart_id) references carts (cart_id) on update cascade on delete cascade,
    constraint cart_items_potion_id_fkey foreign key (potion_id) references potions (id) on update cascade on delete cascade
  ) tablespace pg_default;