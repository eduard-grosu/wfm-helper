import asyncio
import websockets
import json
import datetime
from typing import Dict, Any

from quart import current_app
from models.item import _get_item_wildcards, _get_item_by_name


def is_order_valid(order: Dict[str, Any]) -> bool:
    if order['order_type'] != 'sell':
        return False

    item = order['item']
    if not set(item['tags']).issubset(current_app.config['WF_TAGS']):
        return False

    ducats = item['ducats']
    platinum = order['platinum']

    wildcard_items = _get_item_wildcards()
    conditions = [f'{ducats} {item.ducats} and {platinum} {item.price}' for item in wildcard_items]
    
    specific_item = _get_item_by_name(item['en']['item_name'])
    if specific_item:
        condition = f'{platinum} {specific_item.price}'
        if specific_item.ducats != '*':
            condition += f' and {ducats} {specific_item.ducats}'
        conditions.append(condition)

    # this is prone to RCE injection, I know
    # maybe rework later, but for now since the project is not exposed to the internet, it's fine
    return any(eval(condition) for condition in conditions)


# todo: rework this function
def get_order_format(order: Dict[str, Any], *, html=False) -> str:
    seller = order['user']['ingame_name']
    name = order['item']['en']['item_name']
    ducats = order['item']['ducats']
    platinum = order['platinum']
    time = datetime.datetime.now().strftime('%H:%M:%S')
    if html:
        seller_profile_url = current_app.config['WF_PROFILE_URL'].format(seller)
        return (f'<span class="text-gray-400">[<code>{time}</code>]</span> '
                f'<a href="{seller_profile_url}" class="hover:underline">'
                f'<span class="text-yellow-400">{name}</span>: '
                f'<span class="text-green-400">{platinum} platinum</span>, '
                f'<span class="text-pink-400">{ducats} ducats</span>, '
                f'seller: <span class="text-blue-400">{seller}</span></a>')

    return f'[{time}] {name}: {platinum} platinum, {ducats} ducats, seller: {seller}'


async def send_notification(data: str):
    try:
        await current_app.session.post(current_app.config['WF_NTFY_URL'], data=data)
    except Exception as e:
        current_app.logger.error(f'Failed to send NTFY notification: {e}')


async def process_message(payload: Dict[str, Any], broker):
    try:
        order = payload['payload']['order']
        if is_order_valid(order):
            data = get_order_format(order)
            current_app.logger.info(data)
            await send_notification(data)
            await broker.publish(get_order_format(order, html=True))
    except KeyError:
        pass


async def background_task(broker):
    while True:
        try:
            async with websockets.connect(
                current_app.config['WF_WEBSOCKET_URL'], open_timeout=60, close_timeout=60
            ) as ws:
                current_app.logger.info('Connected to WF websocket.')
                
                message = {"type":"@WS/SUBSCRIBE/MOST_RECENT"}
                await ws.send(json.dumps(message))

                while True:
                    payload = json.loads(await ws.recv())
                    await process_message(payload, broker)
        except (
            TimeoutError,
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.ConnectionClosedOK,
            websockets.exceptions.InvalidStatusCode,
        ):
            current_app.logger.warning('WF websocket disconnected, attempting reconnect...')
            await asyncio.sleep(3)
