from dataclasses import dataclass

from quart import current_app
from quart_db import Connection


@dataclass
class Item:
    id: int
    name: str
    ducats_op: str | None
    ducats_val: int | None
    price_op: str | None
    price_val: int | None


async def _insert_item(db: Connection, name: str, price_op: str, price_val: int) -> None:
    result = await db.fetch_one(
        'INSERT INTO items(name, price_op, price_val) VALUES ($1, $2, $3) RETURNING id',
        (name, price_op, price_val),
    )
    current_app.user_items[result['id']] = Item(
        id=result['id'], name=name, ducats_op=None, ducats_val=None, price_op=price_op, price_val=price_val
    )


async def _delete_item(db: Connection, item_id: int) -> None:
    if item_id in current_app.user_items:
        del current_app.user_items[item_id]
    await db.execute('DELETE FROM items WHERE id = $1', (item_id,))


async def _update_item(db: Connection, item_id: int, price_op: str, price_val: int) -> None:
    current_app.user_items[item_id].price_op = price_op
    current_app.user_items[item_id].price_val = price_val
    await db.execute(
        'UPDATE items SET price_op = $1, price_val = $2 WHERE id = $3', (price_op, price_val, item_id)
    )


def _get_item_by_id(item_id: int) -> None:
    return current_app.user_items.get(item_id, None)


def _get_item_by_name(name: str) -> None:
    return next((item for item in current_app.user_items.values() if item.name == name), None)


def _get_item_wildcards() -> list:
    return [item for item in current_app.user_items.values() if item.name == '*']
