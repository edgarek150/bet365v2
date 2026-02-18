from typing import List, Optional
from models import BetRule, CombiRule

_bet_rules_cache: Optional[List[BetRule]] = None
_combi_rules_cache_N: Optional[List[CombiRule]] = None


def get_bet_rules() -> List[BetRule]:
    global _bet_rules_cache
    if _bet_rules_cache is None:
        try:
            from rules.loader_saver import load_bet_rules
            _bet_rules_cache = load_bet_rules()
        except Exception as e:
            from utils.logging import log_error
            log_error(f"Failed to load single bet rules: {e}")
            _bet_rules_cache = []
    return _bet_rules_cache


def get_combi_rules_N() -> List[CombiRule]:
    global _combi_rules_cache_N
    if _combi_rules_cache_N is None:
        try:
            from rules.loader_saver import load_combi_rules_N
            _combi_rules_cache_N = load_combi_rules_N()
        except Exception as e:
            from utils.logging import log_error
            log_error(f"Failed to load N-leg combi rules: {e}")
            _combi_rules_cache_N = []
    return _combi_rules_cache_N
