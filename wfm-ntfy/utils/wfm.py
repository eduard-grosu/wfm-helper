import asyncio
import websockets
import json
import datetime
from typing import Dict, Any

from quart import current_app
from models.item import _get_item_wildcards, _get_item_by_name


def is_order_valid(order: Dict[str, Any]) -> bool:
    if order['type'] != 'sell':
        return False

    conditions = []
    item = current_app.wf_items[order['itemId']]

    ducats = item.get('ducats')  # some items don't have ducats
    platinum = order['platinum']

    if ducats:
        wildcard_items = _get_item_wildcards()
        for wildcard_item in wildcard_items:
            conditions.append(f'{ducats} {wildcard_item.ducats} and {platinum} {wildcard_item.price}')

    specific_item = _get_item_by_name(item['i18n']['en']['name'])
    if specific_item:
        condition = f'{platinum} {specific_item.price}'
        if specific_item.ducats:
            condition += f' and {ducats} {specific_item.ducats}'
        conditions.append(condition)

    # this is prone to RCE injection, I know
    # maybe rework later, but for now since the project is not exposed to the internet, it's fine
    return any(eval(condition) for condition in conditions)


# todo: rework this function
def get_order_format(order: Dict[str, Any]) -> str:
    seller = order['user']['ingameName']
    item = current_app.wf_items[order['itemId']]
    name = item['i18n']['en']['name']
    ducats = item['ducats']
    platinum = order['platinum']
    time = datetime.datetime.now().strftime('%H:%M:%S')

    seller_profile_url = current_app.config['WF_PROFILE_URL'].format(seller)
    return (
        f'[{time}] {name}: {platinum} platinum, {ducats} ducats, seller: {seller}',
        f'<span class="text-gray-400">[<code>{time}</code>]</span> '
        f'<a href="{seller_profile_url}" target="_blank" class="hover:underline">'
        f'<span class="text-yellow-400">{name}</span>: '
        f'<span class="text-green-400">{platinum} platinum</span>, '
        f'<span class="text-pink-400">{ducats} ducats</span>, '
        f'seller: <span class="text-blue-400">{seller}</span></a>',
    )


async def send_notification(data: str):
    try:
        await current_app.session.post(current_app.config['WF_NTFY_URL'], data=data)
    except Exception as e:
        current_app.logger.error(f'Failed to send NTFY notification: {e}')


async def process_message(payload: Dict[str, Any], broker):
    try:
        order = payload['payload']
        if is_order_valid(order):
            data, html = get_order_format(order)
            current_app.logger.info(data)
            await send_notification(data)
            await broker.publish(html)
    except KeyError:
        pass


async def background_task(broker):
    while True:
        try:
            async with websockets.connect(
                current_app.config['WF_WEBSOCKET_URL'],
                open_timeout=60,
                close_timeout=60,
                user_agent_header=current_app.user_agent,
            ) as ws:
                current_app.logger.info('Connected to WF websocket.')

                # message = {"type":"@WS/SUBSCRIBE/MOST_RECENT"}  # v1
                message = {
                    "route": "@wfm|cmd/subscribe/newOrders",
                    "payload": {"platform": "pc", "crossplay": True},
                    "id": "3qKjOKfExUM",
                }
                await ws.send(json.dumps(message))

                while True:
                    try:
                        payload = json.loads(await ws.recv())
                    except websockets.ConnectionClosed:
                        current_app.logger.warning('WF connection closed, attempting reconnect...')
                        break

                    await process_message(payload, broker)
        except (TimeoutError, websockets.InvalidStatus):
            current_app.logger.warning('WF websocket disconnected, attempting reconnect...')
        except Exception as e:
            current_app.logger.error(f'WF websocket error: {e}')

        # sleep for a bit before reconnecting
        await asyncio.sleep(3)
