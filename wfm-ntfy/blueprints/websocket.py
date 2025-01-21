from quart import Blueprint, websocket, current_app
import asyncio

from utils.broker import Broker
from utils.wfm import background_task


blueprint = Blueprint('websocket', __name__)
broker = Broker()


@blueprint.before_app_serving
async def before_serving():
    current_app.background_task = asyncio.create_task(background_task(broker))


@blueprint.after_app_serving
async def after_serving():
    current_app.background_task.cancel()
    try:
        await current_app.background_task
    except asyncio.CancelledError:
        pass


@blueprint.websocket("/ws")
async def ws() -> None:
    """Send our messages to the frontend"""

    await websocket.accept()
    async for message in broker.subscribe():
        await websocket.send(message)
