import os
from models import app_state

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# False  = connect to existing Chrome via CDP (production — start Chrome manually first)
# True   = let Playwright launch your system Chrome in headless mode
HEADLESS = False
import platform
_system = platform.system()
CHROME_EXECUTABLE = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if _system == "Darwin"
    else r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if _system == "Windows"
    else "/usr/bin/google-chrome"
)

TELEGRAM_BOT_TOKEN = "8007135077:AAHD2NR7Y4fq2AnZBVnkkSmFKr7cHYDeIpA"
TELEGRAM_CHAT_ID = "1817518795"
TELEGRAM_GROUP_CHAT_ID = "-4775004560"

SEND_TEXT_URL = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage"
SEND_TEXT_SILENT_URL = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage"
FAST_TEXT_URL = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage"
FAST_TEXT_SILENT_URL = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage"

THRESHOLDS_CSV = os.path.join(DATA_DIR, "thresholds.csv")
COMBI_THRESHOLDS_CSV = os.path.join(DATA_DIR, "combi_thresholds.csv")
DATA_JSON = os.path.join(DATA_DIR, "data.json")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error_log.txt")

MESSAGE_ON = 0  # 0 = me only, 1 = group, 2 = both

TRANSLATIONS = {
    'TOTALS': {
        'en': 'Total match points',
        'es': 'Partido: total de puntos',
        'cz': 'Celkem bodů v zápasu',
        'sk': 'Celkový počet bodov v zápase'
    },
    'HANDICAPS': {
        'en': 'Match Handicap (Games)',
        'es': 'Handicap de partido (juegos)',
        'cz': 'Sázky na handicep - Sety',
        'sk': 'Stávky na hendikep - sety'
    },
    'TO_WIN_MATCH': {
        'en': 'To Win Match',
        'es': 'Ganará el encuentro',
        'cz': 'Vyhraje utkaní',
        'sk': 'Vyhrá zápas'
    },
}

SPORT_URLS = {
    'cz': 'https://www.bet365.com/#/AS/B107/',
    'es': 'https://www.bet365.es/#/AS/B107/',
    'sk': 'https://www.bet365.com/#/AS/B107/',
}

IGNORE_TOURN = []
IGNORE_HANDICAPS = 0

HAND_EMOJI = "👉"
EQUALS_EMOJI = " = "
CLOCK_EMOJI = "⏰"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Callback set by main.py for language-switch reload
reload_data = None
