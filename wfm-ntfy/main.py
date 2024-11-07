import asyncio
import websockets
import json
import datetime
import aiohttp
from typing import Dict, Any


TAGS = {'weapon', 'warframe', 'component', 'prime', 'blueprint'}
WEBSOCKET_URL = 'wss://warframe.market/socket?platform=pc'
NTFY_URL = 'https://ntfy.sh/some-topic-name-here'


def is_order_valid(order: Dict[str, Any]) -> bool:
    if order['order_type'] != 'sell':
        return False

    item = order['item']
    if not set(item['tags']).issubset(TAGS):
        return False

    ducats = item['ducats']
    platinum = int(order['platinum'])
    return ((ducats >= 45 and platinum == 1) or
            (ducats >= 90 and platinum <= 2))


def get_order_format(order: Dict[str, Any]) -> str:
    seller = order['user']['ingame_name']
    name = order['item']['en']['item_name']
    ducats = order['item']['ducats']
    platinum = int(order['platinum'])
    time = datetime.datetime.now().strftime('%H:%M:%S')
    return f'[{time}] {name}: {platinum} plat, {ducats} ducats, seller: {seller}'


async def send_notification(session: aiohttp.ClientSession, data: str):
    try:
        await session.post(NTFY_URL, data=data)
    except Exception as e:
        print(f'Failed to send notification: {e}')


async def process_message(payload: Dict[str, Any], session: aiohttp.ClientSession):
    try:
        order = payload['payload']['order']
        if is_order_valid(order):
            data = get_order_format(order)
            print(data)
            await send_notification(session, data)
    except KeyError:
        pass


async def main():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with websockets.connect(
                    WEBSOCKET_URL, open_timeout=60, close_timeout=60
                ) as ws:
                    print('Connected to the websocket.')
                    
                    message = {"type":"@WS/SUBSCRIBE/MOST_RECENT"}
                    await ws.send(json.dumps(message))

                    while True:
                        payload = json.loads(await ws.recv())
                        await process_message(payload, session)
            except (
                TimeoutError,
                websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.ConnectionClosedOK,
                websockets.exceptions.InvalidStatusCode,
            ):
                print('WebSocket disconnected, attempting reconnect...')
                await asyncio.sleep(3)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Disconnected from the websocket.')
