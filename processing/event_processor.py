from typing import Any, List, Dict

import config
from models import TournamentEvent, Link
from utils.io import save_json_to_file
from utils.logging import log_error


def initialize_urls(data):
    """Populate app_state.URLS from persisted data.json."""
    for tournament in data:
        for event in tournament.get('events', []):
            url = Link(tournament['name'], event['name'], event['url'], None)
            config.app_state.URLS.append(url)


def get_data_filepath():
    return config.DATA_JSON


def odds_existence(event: TournamentEvent, data: List[Dict[str, Any]]) -> int:
    """
    Checks if a tournament/event already exists in data, updates it or creates it,
    then calls check_matches for notification logic.
    Returns 1 if changes occurred, 0 otherwise.
    """
    from rules.matching import check_matches  # late import to avoid circular deps

    index = next(
        (i for i, t in enumerate(data) if t["name"] == event.tournament),
        None
    )

    if index is not None:
        tournament_data = data[index]
        existing_event = next(
            (e for e in tournament_data["events"] if e["name"] == event.event),
            None
        )

        if existing_event:
            if check_matches(existing_event["matches"], event):
                existing_event["matches"] = event.json()
                save_json_to_file(data, get_data_filepath())
                return 1
        else:
            check_matches([], event)
            tournament_data["events"].append({
                "name": event.event,
                "matches": event.json(),
                "url": event.url,
            })
            save_json_to_file(data, get_data_filepath())
            return 1
    else:
        new_tournament = {
            "name": event.tournament,
            "events": [{
                "name": event.event,
                "matches": event.json(),
                "url": event.url,
            }]
        }
        check_matches([], event)
        data.append(new_tournament)
        save_json_to_file(data, get_data_filepath())

        if config.app_state.TIMER:
            config.app_state.TIMER.cancel()
            config.app_state.TIMER = None
        return 1

    return 0
