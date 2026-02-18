from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Match:
    player1: str
    player2: str
    odd1: str
    odd2: str
    start_time: str = ""

    def json(self):
        return [self.player1, self.player2, self.odd1, self.odd2]

    def __repr__(self):
        return f"{self.player1}: @{self.odd1} / {self.player2}: @{self.odd2} -> {self.start_time}"

    @property
    def odd1_float(self) -> Optional[float]:
        try:
            return float(self.odd1)
        except (ValueError, TypeError):
            return None

    @property
    def odd2_float(self) -> Optional[float]:
        try:
            return float(self.odd2)
        except (ValueError, TypeError):
            return None


class TournamentEvent:
    def __init__(self, tournament, event, matches, url):
        self.tournament = tournament
        self.event = event
        self.matches = matches
        self.url = url

    def json(self):
        return [match.json() for match in self.matches]

    def __repr__(self):
        ret = f"{self.tournament} {self.event}\n"
        for m in self.matches:
            ret += str(m) + "\n"
        return ret


class Link:
    def __init__(self, tournament, event, url, timestamp):
        self.tournament = tournament
        self.event = event
        self.url = url
        self.timestamp = timestamp

    def __repr__(self):
        return f"{self.tournament} - {self.event} -> {self.url} - {self.timestamp}"


@dataclass
class BetRule:
    player_substring: str
    opponent_substring: str
    threshold_odd: float
    bet_value: str
    sent: int


@dataclass
class CombiRuleLeg:
    player_substring: str
    opponent_substring: str
    min_odd: float


@dataclass
class CombiRule:
    legs: List[CombiRuleLeg]
    combined_threshold_odd: float
    bet_value: str
    sent: int
    _source_row_dict: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppState:
    URLS: list = field(default_factory=list)
    LOOPS_COUNTER: int = 0
    SEARCH_SLEEP: list = field(default_factory=lambda: [10, 15])
    LABEL_SLEEP: list = field(default_factory=lambda: [10, 15])
    CURRENT_LANGUAGE: str = 'sk'
    PROCESSED_LIVE_MATCHES: set = field(default_factory=set)
    TIMER: Any = None


app_state = AppState()
