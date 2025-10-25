class Config:
    QUART_DB_DATABASE_URL = "sqlite:///items.db"
    QUART_DB_DATA_PATH = "migrations/data.py"

    # utils/wfm.py
    WF_PROFILE_URL = 'https://warframe.market/profile/{0}'
    WF_API_URL = 'https://api.warframe.market/v2/items'
    WF_WEBSOCKET_URL = 'wss://warframe.market/socket-v2'
    WF_TAGS = {'weapon', 'warframe', 'component', 'prime', 'blueprint'}
    WF_NTFY_URL = 'https://ntfy.sh/some-topic-name-here'


class DevelopmentConfig(Config):
    DEBUG = True
