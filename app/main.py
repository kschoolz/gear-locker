import base64
import re
from datetime import date, datetime, timezone
from typing import Literal

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.db import get_connection

app = FastAPI()


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    field = ".".join(str(part) for part in first["loc"][1:])
    reason = str(first["ctx"]["error"]) if first["type"] == "value_error" else first["msg"]
    message = f"{field}: {reason}" if field else reason
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "message": message},
    )


@app.get("/health")
def health():
    return {"ok": True}


Category = Literal[
    "rope", "protection", "soft_goods", "hardware", "shelter", "sleep", "cooking", "other"
]


class ItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str
    brand: str
    category: Category
    bought_date: date | None = None
    notes: str | None = None

    @field_validator("name", "brand")
    @classmethod
    def not_blank(cls, value):
        if value is None:
            raise ValueError("must not be null")
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("bought_date", mode="before")
    @classmethod
    def date_format(cls, value):
        if value is not None and not (isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)):
            raise ValueError("must be a date in YYYY-MM-DD format")
        return value

    @field_validator("bought_date")
    @classmethod
    def not_in_future(cls, value):
        if value is not None and value > datetime.now(timezone.utc).date():
            raise ValueError("must not be in the future")
        return value

    @field_validator("notes")
    @classmethod
    def blank_notes_to_null(cls, value):
        return value or None


@app.post("/gear", status_code=201)
def create_gear(item: ItemCreate, conn=Depends(get_db)):
    cursor = conn.execute(
        "INSERT INTO item (name, brand, category, bought_date, notes) VALUES (?, ?, ?, ?, ?)",
        (
            item.name,
            item.brand,
            item.category,
            item.bought_date.isoformat() if item.bought_date else None,
            item.notes,
        ),
    )
    conn.commit()
    return conn.execute("SELECT * FROM item WHERE id = ?", (cursor.lastrowid,)).fetchone()


def not_found(item_id):
    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "message": f"item {item_id} not found"},
    )


@app.get("/gear/{item_id}")
def get_gear(item_id: int, conn=Depends(get_db)):
    row = conn.execute("SELECT * FROM item WHERE id = ?", (item_id,)).fetchone()
    return row if row else not_found(item_id)



class ItemUpdate(ItemCreate):
    name: str | None = None
    brand: str | None = None
    category: Category | None = None

    @field_validator("category")
    @classmethod
    def category_not_null(cls, value):
        if value is None:
            raise ValueError("must not be null")
        return value

    @model_validator(mode="after")
    def not_empty(self):
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        return self


@app.patch("/gear/{item_id}")
def update_gear(item_id: int, item: ItemUpdate, conn=Depends(get_db)):
    if not conn.execute("SELECT 1 FROM item WHERE id = ?", (item_id,)).fetchone():
        return not_found(item_id)
    changes = item.model_dump(include=item.model_fields_set)
    if changes.get("bought_date"):
        changes["bought_date"] = changes["bought_date"].isoformat()
    assignments = ", ".join(f"{column} = ?" for column in changes)
    conn.execute(f"UPDATE item SET {assignments} WHERE id = ?", (*changes.values(), item_id))
    conn.commit()
    return conn.execute("SELECT * FROM item WHERE id = ?", (item_id,)).fetchone()


@app.post("/gear/{item_id}/retire")
def retire_gear(item_id: int, conn=Depends(get_db)):
    conn.execute(
        "UPDATE item SET retired_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')"
        " WHERE id = ? AND retired_at IS NULL",
        (item_id,),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM item WHERE id = ?", (item_id,)).fetchone()
    return row if row else not_found(item_id)



PAGE_SIZE = 20


def encode_cursor(item_id):
    return base64.urlsafe_b64encode(str(item_id).encode()).decode()


def decode_cursor(cursor):
    try:
        item_id = int(base64.b64decode(cursor, altchars=b"-_", validate=True).decode())
    except ValueError:
        return None
    return item_id if item_id > 0 else None


@app.get("/gear")
def list_gear(category: Category | None = None, cursor: str | None = None, conn=Depends(get_db)):
    sql = "SELECT * FROM item WHERE retired_at IS NULL"
    params = []
    if category is not None:
        sql += " AND category = ?"
        params.append(category)
    if cursor is not None:
        after_id = decode_cursor(cursor)
        if after_id is None:
            return JSONResponse(
                status_code=422,
                content={"error": "validation_error", "message": "cursor: invalid cursor"},
            )
        sql += " AND id < ?"
        params.append(after_id)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(PAGE_SIZE + 1)
    rows = conn.execute(sql, params).fetchall()
    next_cursor = encode_cursor(rows[PAGE_SIZE - 1]["id"]) if len(rows) > PAGE_SIZE else None
    return {"items": rows[:PAGE_SIZE], "next_cursor": next_cursor}
