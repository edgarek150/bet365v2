import re
import requests
import config

ESCAPE_RE = re.compile(r'([_\[\]\(\)\~\`\>\#\+\-\=\|\{\}\\.!])')


def escape_md2(text: str) -> str:
    return ESCAPE_RE.sub(r'\\\1', text)


CHAT_IDS = {
    "AdrianSVK": "-4721477378",
    "Pedro":     "-4602354087",
    "Timber":    "-4660319418",
    "Flechas":   "-4903122447",
    "Shelby":    "-4755678116",
    "edgar":     "1817518795",
}

TARGET_CHATS = ["edgar"]


def send_message_all(text: str, notify: bool = True):
    safe = escape_md2(text) + "\n"
    params = {
        "parse_mode": "MarkdownV2",
        "disable_notification": not notify,
        "text": safe,
    }
    for name in TARGET_CHATS:
        chat_id = CHAT_IDS.get(name)
        if not chat_id:
            print(f"Unknown chat: {name}")
            continue
        params["chat_id"] = chat_id
        r = requests.get(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            params=params
        )
        if not r.ok:
            print(f"Failed to send to {name} ({chat_id}): {r.text}")
