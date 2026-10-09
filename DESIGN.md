## Stage 1

TABLE item
id          INTEGER PRIMARY KEY (assigned by the database)
name        text required, trimmed, must not be blank
brand       text required, trimmed, must not be blank
category    text required, one of the category values below
bought_date date optional (YYYY-MM-DD), null = unknown, must not be in the future
notes       text optional, trimmed, null = no notes (whitespace-only becomes null)
retired_at  timestamp optional, null = not retired, set only by /retire
created_at  timestamp required, set by the database

Category values (exact, lowercase, case-sensitive):
rope, protection, soft_goods, hardware, shelter, sleep, cooking, other

CONVENTIONS
- Timestamps are ISO 8601 UTC with Z, e.g. 2026-10-08T22:17:13Z (stored as text in this format).
- Dates are YYYY-MM-DD. "Future" means later than today's UTC date.
- Blank = empty or whitespace-only. name, brand, and notes are trimmed before validation and storage.
  Blank notes are stored as null.
- Item response = all columns: {id, name, brand, category, bought_date, notes, retired_at, created_at}.
  Optional fields with no value are returned as null.
- Errors return {"error": "<code>", "message": "<human-readable detail>"}.

ERROR CODES
422 validation_error  bad body, query param, cursor, or path id (e.g. non-integer id)
404 not_found         no item with that id

CONSTRAINTS
- name, brand: NOT NULL, CHECK trimmed value is not empty
- category: NOT NULL, CHECK category IN (the category values above)
- id, created_at, retired_at cannot be set through the API

INDEXES
None in Stage 1.

ENDPOINTS
POST /gear
  input {name, brand, category, bought_date?, notes?}
  - Explicit null for bought_date or notes is the same as leaving it out.
  -> 201 + item
  errors 422 validation_error (missing/blank required field, bad category, bad or future date,
                               unknown or read-only field such as id/created_at/retired_at)

GET /gear?category=&cursor=
  -> 200 + {"items": [item, ...], "next_cursor": "<string>" | null}
  - Retired items hidden. Page size is fixed at 20.
  - Sorted newest first: id DESC (ids increase with each insert, so this is creation order).
  - category optional: only items in that category.
  - cursor optional: omit for the first page; pass the previous response's next_cursor to get the next page.
  - next_cursor is null when there are no more items. An empty items list is fine.
  - The cursor is opaque to clients. It encodes the id of the last item on the page;
    the next page returns items with a smaller id.
  errors 422 validation_error (bad category, malformed cursor)

GET /gear/{id}
  -> 200 + item (retired items included)
  errors 404 not_found, 422 validation_error (non-integer id)

PATCH /gear/{id}
  input any non-empty subset of {name, brand, category, bought_date, notes}; partial update
  - Fields not sent are unchanged.
  - Sending null clears an optional field (bought_date, notes). null for name, brand, or category is invalid.
  - Retired items can be patched.
  -> 200 + updated item
  errors 404 not_found,
         422 validation_error (empty body, unknown or read-only field such as id/created_at/retired_at,
                               or any value breaking the field rules above)

POST /gear/{id}/retire
  no input
  -> 200 + updated item
  - Sets retired_at to now. If already retired, returns 200 and keeps the original retired_at.
  errors 404 not_found, 422 validation_error (non-integer id)

OUT OF SCOPE (Stage 1)
DELETE, un-retire, listing retired items, configurable page size.

## Stage 2  
## Stage 3  
## Stage 4  
## Stage 5  
## Stage 6  
## Stage 7
## Stage 8

