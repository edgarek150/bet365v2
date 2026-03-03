import psycopg2
import config
from utils.logging import log_error


def get_tipper_chat_ids() -> list:
    """Return list of chat_id strings for active bet365 tippers."""
    try:
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
        )
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM tippers WHERE active = TRUE AND bet365 = TRUE")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [str(row[0]) for row in rows]
    except Exception as e:
        log_error(f"DB error in get_tipper_chat_ids: {e}")
        return []
