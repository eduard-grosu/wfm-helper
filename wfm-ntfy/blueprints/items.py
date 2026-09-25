import re

from quart import Blueprint, g, redirect, request, url_for

from models.item import _delete_item, _insert_item, _update_item

blueprint = Blueprint('items', __name__)


def parse_condition(value_str: str, default_op: str = '<=') -> tuple[str | None, int | None]:
    if not value_str:
        return None, None

    match = re.match(r'^(<=|>=|==|=|<|>)?\s*(\d+)$', value_str.strip())
    if not match:
        return None, None

    op, val_str = match.groups()
    if not op:
        op = default_op

    return op, int(val_str)


@blueprint.post('/add-item')
async def add_item():
    """Add a new item and refresh the page."""

    data = await request.form
    item_name = data.get('item-name')
    item_price = data.get('item-price')
    op, val = parse_condition(item_price)
    if item_name and op and val is not None:
        await _insert_item(g.connection, item_name, op, val)

    return redirect(url_for('index'))


@blueprint.post('/edit-item/<int:item_id>')
async def edit_item(item_id: int):
    """Edit an existing item and refresh the page."""

    data = await request.form
    platinum = data.get('platinum')
    op, val = parse_condition(platinum)
    if op and val is not None:
        await _update_item(g.connection, item_id, op, val)

    return redirect(url_for('index'))


@blueprint.post('/delete-item/<int:item_id>')
async def delete_item(item_id: int):
    """Delete an item and refresh the page."""

    await _delete_item(g.connection, item_id)
    return redirect(url_for('index'))
