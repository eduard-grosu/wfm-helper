from quart import Blueprint, g, request, redirect, url_for
from models.item import _insert_item, _delete_item, _update_item


blueprint = Blueprint('items', __name__)


@blueprint.post('/add-item')
async def add_item():
    """Add a new item and refresh the page."""

    data = await request.form
    item_name = data.get('item-name')
    item_price = data.get('item-price')
    if item_name and item_price and item_price.isdigit():  # maybe add better validation
        await _insert_item(g.connection, item_name, f'<= {item_price}')

    return redirect(url_for('index'))


@blueprint.post('/edit-item/<int:item_id>')
async def edit_item(item_id: int):
    """Edit an existing item and refresh the page."""

    data = await request.form
    platinum = data.get('platinum')
    if platinum and platinum.isdigit():
        await _update_item(g.connection, item_id, f'<= {platinum}')

    return redirect(url_for('index'))


@blueprint.post('/delete-item/<int:item_id>')
async def delete_item(item_id: int):
    """Delete an item and refresh the page."""

    await _delete_item(g.connection, item_id)
    return redirect(url_for('index'))
