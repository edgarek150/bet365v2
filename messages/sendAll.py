import re
import requests
import config

ESCAPE_RE = re.compile(r'([_\[\]\(\)~`>#\+\-=\|\{\}\.!])')


def escape_md2(text: str) -> str:
    return ESCAPE_RE.sub(r'\\\1', text)


def send_message_all(text: str, notify: bool = True):
    safe = escape_md2(text) + "\n"
    params = {
        "parse_mode": "MarkdownV2",
        "disable_notification": not notify,
        "text": safe,
    }

    if config.TEST_MODE:
        # TEST_MODE: only admin (edgar)
        chat_ids = [config.ADMIN_CHAT_ID]
    else:
        # Production: query DB for active bet365 tippers (edgar NOT included)
        from db import get_tipper_chat_ids
        chat_ids = get_tipper_chat_ids()
        if not chat_ids:
            print("send_message_all: no active bet365 tippers found in DB")
            return

    for chat_id in chat_ids:
        params["chat_id"] = chat_id
        r = requests.get(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            params=params,
        )
        if not r.ok:
            print(f"Failed to send to chat_id {chat_id}: {r.text}")
