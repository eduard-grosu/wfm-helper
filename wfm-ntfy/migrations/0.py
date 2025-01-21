from quart_db import Connection


async def migrate(connection: Connection) -> None:
    await connection.execute("""
        CREATE TABLE items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            ducats TEXT,
            price TEXT
        )
    """)

    await connection.execute("""
        INSERT INTO items (name, ducats, price)
        VALUES ('*', '>= 45', '== 1'),
                ('*', '>= 90', '<= 2')
    """)
