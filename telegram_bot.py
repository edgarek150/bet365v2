import asyncio
import requests
import config
from models import app_state

SPEED_MODES = {
    "fast":   {"SEARCH_SLEEP": [5, 7],   "LABEL_SLEEP": [5, 7]},
    "medium": {"SEARCH_SLEEP": [10, 15], "LABEL_SLEEP": [10, 15]},
    "slow":   {"SEARCH_SLEEP": [25, 35], "LABEL_SLEEP": [25, 35]},
}


def _send(chat_id: str, text: str):
    try:
        requests.get(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            params={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception as e:
        print(f"Telegram send error: {e}")


async def telegram_command_listener():
    offset = 0
    print("Telegram command listener started")
    while True:
        try:
            r = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(
                    f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates",
                    params={"offset": offset, "timeout": 30, "allowed_updates": ["message"]},
                    timeout=40,
                ),
            )
            if not r.ok:
                await asyncio.sleep(5)
                continue

            updates = r.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "").strip().lower()

                if chat_id != config.ADMIN_CHAT_ID:
                    continue

                if text in ("/fast", "/medium", "/slow"):
                    mode = text[1:]
                    settings = SPEED_MODES[mode]
                    app_state.SEARCH_SLEEP = list(settings["SEARCH_SLEEP"])
                    app_state.LABEL_SLEEP = list(settings["LABEL_SLEEP"])
                    app_state.SPEED_MODE = mode
                    lo, hi = settings["SEARCH_SLEEP"]
                    _send(chat_id, f"Speed mode set to {mode} (sleep {lo}-{hi}s)")
                    print(f"Speed mode changed to: {mode}")

                elif text == "/mode":
                    lo, hi = app_state.SEARCH_SLEEP
                    _send(chat_id, f"Current mode: {app_state.SPEED_MODE} (sleep {lo}-{hi}s)")

        except Exception as e:
            print(f"Telegram listener error: {e}")
            await asyncio.sleep(5)
