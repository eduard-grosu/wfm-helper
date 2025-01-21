from dataclasses import dataclass
from quart_db import Connection
from quart import current_app


@dataclass
class Item:
    id: int
    name: str
    ducats: str | None
    price: str | None


async def _insert_item(db: Connection, name: str, price: str) -> None:
    result = await db.fetch_one('INSERT INTO items(name, price) VALUES ($1, $2) RETURNING id', (name, price))
    current_app.user_items[result['id']] = Item(id=result['id'], name=name, ducats=None, price=price)


async def _delete_item(db: Connection, item_id: int) -> None:
    if item_id in current_app.user_items:
        del current_app.user_items[item_id]
    await db.execute('DELETE FROM items WHERE id = $1', (item_id,))


async def _update_item(db: Connection, item_id: int, platinum: str) -> None:
    current_app.user_items[item_id].price = platinum
    await db.execute('UPDATE items SET price = $1 WHERE id = $2', (platinum, item_id))


def _get_item_by_id(item_id: int) -> None:
    return current_app.user_items.get(item_id, None)


def _get_item_by_name(name: str) -> None:
    return next((item for item in current_app.user_items.values() if item.name == name), None)


def _get_item_wildcards() -> list:
    return [item for item in current_app.user_items.values() if item.name == '*']
