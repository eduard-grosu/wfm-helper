from quart import Quart, render_template
from quart_db import QuartDB
import logging
import json
import aiohttp

from blueprints.items import blueprint as items_blueprint
from blueprints.websocket import blueprint as websocket_blueprint
from models.item import Item
from utils.user_agent import get_random_user_agent


logging.basicConfig(level=logging.INFO)


app = Quart(__name__)
app.config.from_object('config.DevelopmentConfig')
quart_db = QuartDB(app)

app.register_blueprint(items_blueprint)
app.register_blueprint(websocket_blueprint)


@app.before_serving
async def on_start():
    app.session = aiohttp.ClientSession()
    app.user_agent = get_random_user_agent()
    headers = {'Language': 'en', 'Accept': 'application/json', 'User-Agent': app.user_agent}
    async with app.session.get(app.config['WF_API_URL'], headers=headers) as request:
        response = await request.json()
        # get url_name of items and pass it down below in a dict
        # then pass the dict to the frontend and use the first key as the item name
        # and the value as the url_name
        items = {item["id"]: {k: v for k, v in item.items() if k != "id"} for item in response["data"]}
        app.wf_items = items

    app.user_items = {}
    async with quart_db.connection() as connection:
        rows = await connection.fetch_all('SELECT * FROM items')
        for row in rows:
            app.user_items[row['id']] = Item(**row)
            app.logger.info(f'Loaded item: {row["name"]}')


@app.after_serving
async def on_close():
    await app.session.close()


@app.route("/")
async def index():
    """Render the homepage with the current list of items."""

    user_items = dict(sorted(app.user_items.items(), key=lambda v: v[1].name))
    items = [
        v['i18n']['en']['name'] for _, v in app.wf_items.items() if set(v['tags']) <= app.config['WF_TAGS']
    ]
    return await render_template("index.html", items=json.dumps(items), user_items=user_items)


if __name__ == "__main__":
    app.run()
