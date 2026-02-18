from datetime import datetime
import config


def log_error(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] ERROR: {message}\n"
    try:
        with open(config.ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_message)
    except Exception as e:
        print(f"FAILED TO WRITE TO LOG FILE: {config.ERROR_LOG_FILE}. Original: {message}. Write error: {e}")
    print(log_message.strip())
