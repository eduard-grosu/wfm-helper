from quart_db import Connection


async def migrate(connection: Connection) -> None:
    await connection.execute("""
        CREATE TABLE items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            ducats_op TEXT,
            ducats_val INTEGER,
            price_op TEXT,
            price_val INTEGER
        )
    """)

    await connection.execute("""
        INSERT INTO items (name, ducats_op, ducats_val, price_op, price_val)
        VALUES ('*', '>=', 45, '==', 1),
                ('*', '>=', 90, '<=', 2)
    """)
