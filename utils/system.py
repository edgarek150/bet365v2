import os
import signal
import subprocess
import time
from threading import Timer

import config
from utils.logging import log_error


def handler(signum, frame):
    kill_session(False)


def kill_session(send_message: bool = True):
    if send_message:
        print("Sending KILLED message")
    exit(1)


def set_timer_slow_in_hour():
    if config.app_state.TIMER:
        config.app_state.TIMER.cancel()
        config.app_state.TIMER = None
    config.app_state.TIMER = Timer(3600, set_search_sleep, [145, 180])
    config.app_state.TIMER.start()


def set_search_sleep(a: int, b: int):
    config.app_state.SEARCH_SLEEP[0] = a
    config.app_state.SEARCH_SLEEP[1] = b


def play_notification_sound():
    try:
        sound_file = "/usr/share/sounds/freedesktop/stereo/complete.oga"
        if os.path.exists(sound_file):
            subprocess.Popen(['paplay', sound_file])
            time.sleep(0.2)
            subprocess.Popen(['paplay', sound_file])
    except Exception as e:
        log_error(f"Failed to play notification sound: {e}")


signal.signal(signal.SIGINT, handler)
