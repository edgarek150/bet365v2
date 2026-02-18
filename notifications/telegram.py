import requests
import config
from utils.logging import log_error


def send_message(message: str, notify: bool) -> bool:
    print("SENDING MESSAGE")
    try:
        escaped = (message
                   .replace("_", "\\_").replace("[", "\\[").replace("]", "\\]")
                   .replace("(", "\\(").replace(")", "\\)").replace("~", "\\~")
                   .replace("`", "\\`").replace(">", "\\>").replace("#", "\\#")
                   .replace("+", "\\+").replace("-", "\\-").replace("=", "\\=")
                   .replace("|", "\\|").replace("{", "\\{").replace("}", "\\}")
                   .replace(".", "\\.").replace("!", "\\!"))

        params = {"parse_mode": "MarkdownV2", "text": escaped}

        if config.MESSAGE_ON == 0:
            params["chat_id"] = config.TELEGRAM_CHAT_ID
            if not notify:
                params["disable_notification"] = True
            requests.get(config.SEND_TEXT_URL, params=params)
        elif config.MESSAGE_ON == 2:
            params["chat_id"] = config.TELEGRAM_GROUP_CHAT_ID
            if not notify:
                params["disable_notification"] = True
            requests.get(config.FAST_TEXT_URL, params=params)

        return True
    except Exception as e:
        log_error(f"Failed to send Telegram message: {e}")
        return False


def add_to_message(match, send_time: bool) -> str:
    player1 = (match.player1 or "").strip()
    player2 = (match.player2 or "").strip()
    if not player1 or not player2:
        return ""
    msg = f"{config.HAND_EMOJI} {player1}: {config.EQUALS_EMOJI}*@{match.odd1}* \n"
    msg += f"{config.HAND_EMOJI} {player2}: {config.EQUALS_EMOJI}*@{match.odd2}* \n"
    if send_time:
        msg += f"{config.CLOCK_EMOJI}*{match.start_time}* \n\n"
    else:
        msg += "\n"
    return msg
