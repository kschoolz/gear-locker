CREATE TABLE item (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL CHECK (trim(name) <> ''),
    brand       TEXT NOT NULL CHECK (trim(brand) <> ''),
    category    TEXT NOT NULL CHECK (category IN
                  ('rope','protection','soft_goods','hardware','shelter','sleep','cooking','other')),
    bought_date TEXT,
    notes       TEXT,
    retired_at  TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
