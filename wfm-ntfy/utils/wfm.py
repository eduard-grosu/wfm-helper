import asyncio
import datetime
import json
import operator
from typing import Any, Dict

import websockets
from quart import current_app

from models.item import _get_item_by_name, _get_item_wildcards

OPERATORS = {
    '<=': operator.le,
    '>=': operator.ge,
    '==': operator.eq,
    '<': operator.lt,
    '>': operator.gt,
}


def evaluate_condition(val: int | None, op: str | None, target_val: int | None) -> bool:
    if val is None or op is None or target_val is None:
        return False

    func = OPERATORS.get(op)
    if not func:
        return False

    return func(val, target_val)


def _matches_wildcard_rule(rule, ducats: int, platinum: int) -> bool:
    """Basic rule match
    Both ducats and platinum constraints must pass.

    Example rule:
        ducats >= 45
        platinum <= 1
    """
    return (
        evaluate_condition(ducats, rule.ducats_op, rule.ducats_val)
        and evaluate_condition(platinum, rule.price_op, rule.price_val),
    )


def _is_probable_user_error(rule, ducats: int, platinum: int) -> bool:
    """Detects likely mispriced or mistyped listings

    Idea:
    - Extremely high ducats for the same low platinum price
    - Usually indicates incorrect listing input

    Example:
        rule: >=45 ducats @ 1p
        listing: 100 ducats @ 1p  -> likely mistake
    """

    suspicious_threshold = min(2 * rule.ducats_val, 100)  # safety cap
    return ducats >= suspicious_threshold and platinum == rule.price_val


def _is_shadowed_by_lower_tier(rule, ducats: int, platinum: int) -> bool:
    """Handles overlapping wildcard tiers

    Wildcard rules are intentionally broad, e.g.:

        Tier A: >=45 ducats @ ==1p
        Tier B: >=90 ducats @ <=2p

    A listing like:
        90 ducats @ 1p

    matches BOTH rules.

    We avoid duplicate/incorrect attribution by preferring
    the stricter (lower price) tier.

    So if a cheaper rule already captures the listing,
    we skip the broader rule.
    """

    return platinum < rule.price_val and ducats >= rule.ducats_val


def is_order_valid(order: Dict[str, Any]) -> bool:
    if order['type'] != 'sell':
        return False

    item = current_app.wf_items[order['itemId']]
    ducats = item.get('ducats')  # some items don't have ducats
    platinum = order['platinum']

    specific_item = _get_item_by_name(item['i18n']['en']['name'])
    if specific_item:
        # we only care about platinum for comparison
        if evaluate_condition(platinum, specific_item.price_op, specific_item.price_val):
            return True

    if ducats is None:
        return False

    wildcard_rules = _get_item_wildcards()
    wildcard_rules.sort(key=lambda r: r.ducats_val, reverse=True)

    for rule in wildcard_rules:
        if not _matches_wildcard_rule(rule, ducats, platinum):
            continue

        if _is_probable_user_error(rule, ducats, platinum):
            continue

        if _is_shadowed_by_lower_tier(rule, ducats, platinum):
            continue

        return True

    return False


# todo: rework this function
def get_order_format(order: Dict[str, Any]) -> tuple[str, str]:
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
                    'route': '@wfm|cmd/subscribe/newOrders',
                    'payload': {'platform': 'pc', 'crossplay': True},
                    'id': '3qKjOKfExUM',
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
