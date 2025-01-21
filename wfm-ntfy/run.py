from quart import Quart, render_template
from quart_db import QuartDB
import logging
import json
import aiohttp

from blueprints.items import blueprint as items_blueprint
from blueprints.websocket import blueprint as websocket_blueprint
from models.item import Item


logging.basicConfig(level=logging.INFO)


app = Quart(__name__)
app.config.from_object('config.DevelopmentConfig')
quart_db = QuartDB(app)

app.register_blueprint(items_blueprint)
app.register_blueprint(websocket_blueprint)


@app.before_serving
async def on_start():
    app.session = aiohttp.ClientSession()
    headers = {'Language': 'en', 'Accept': 'application/json'}
    async with app.session.get(app.config['WF_API_URL'], headers=headers) as request:
        response = await request.json()
        # keep only blueprints for now until I figure out how to handle other items
        wf_items = [
            item['item_name'] for item in response['payload']['items']
            if 'Blueprint' in item['item_name']
        ]
        app.wf_items = wf_items

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
    return await render_template("index.html", items=json.dumps(app.wf_items), user_items=app.user_items)


if __name__ == "__main__":
    app.run()
