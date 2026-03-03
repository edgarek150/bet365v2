from typing import List, Optional
from models import BetRule, CombiRule

_bet_rules_cache: Optional[List[BetRule]] = None
_combi_rules_cache_N: Optional[List[CombiRule]] = None


def get_bet_rules() -> List[BetRule]:
    try:
        from rules.loader_saver import load_bet_rules
        return load_bet_rules()
    except Exception as e:
        from utils.logging import log_error
        log_error(f"Failed to load single bet rules: {e}")
        return []


def get_combi_rules_N() -> List[CombiRule]:
    try:
        from rules.loader_saver import load_combi_rules_N
        return load_combi_rules_N()
    except Exception as e:
        from utils.logging import log_error
        log_error(f"Failed to load N-leg combi rules: {e}")
        return []
