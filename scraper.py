import asyncio
import re
from typing import List, Tuple, Any, Dict, Optional

import config
from models import Match, TournamentEvent, Link
from utils.logging import log_error


# ---------------------------------------------------------------------------
# Playwright equivalent of the old Selenium `Label` class
# ---------------------------------------------------------------------------

async def query_label(ctx, class_name: str, timeout: float = 6.0) -> Tuple[List[str], List]:
    """
    Wait for elements matching `.class_name`, return (texts, elements).
    Playwright replacement for: Label("class_name ", driver, timeout)
    """
    selector = f".{class_name.strip()}"
    try:
        await ctx.wait_for_selector(selector, timeout=int(timeout * 1000))
    except Exception:
        pass  # Timeout is fine — elements may simply not exist
    elements = await ctx.query_selector_all(selector)
    texts = []
    for el in elements:
        try:
            t = await el.inner_text()
            texts.append(t.strip() if t else "")
        except Exception:
            texts.append("")
    return texts, elements


# ---------------------------------------------------------------------------
# Pure-Python helpers (direct ports — no Selenium/Playwright)
# ---------------------------------------------------------------------------

def parse_czech_date(date_text: str) -> Optional[str]:
    czech_months = {
        'led': '01', 'úno': '02', 'bře': '03', 'dub': '04',
        'kvě': '05', 'čer': '06', 'čvc': '07', 'srp': '08',
        'zář': '09', 'říj': '10', 'lis': '11', 'pro': '12'
    }
    m = re.search(r'(\w+)\s+(\d+)\s+(\w+)', date_text)
    if not m:
        return None
    day = m.group(2)
    month_abbr = m.group(3).lower()
    if month_abbr in czech_months:
        return f"{day.zfill(2)}-{czech_months[month_abbr]}"
    return None


def create_pairs_from_links(links: List[Link]) -> List[Tuple[str, str]]:
    return [(link.tournament, link.event) for link in links]


def create_new_pairs(name_of_tournaments: List[str], name_of_events: List[str]) -> List[Tuple[str, str]]:
    """Map event texts to standardised names (To Win Match / Handicaps) and pair with tournaments."""
    if not name_of_events:
        return []

    lang = config.app_state.CURRENT_LANGUAGE
    event_name_map = {}
    for ev in name_of_events:
        if ev == config.TRANSLATIONS['TO_WIN_MATCH'].get(lang, 'To Win Match'):
            event_name_map[ev] = 'To Win Match'
        elif ev == config.TRANSLATIONS['HANDICAPS'].get(lang, 'Match Handicap (Games)'):
            event_name_map[ev] = 'Handicaps'
        else:
            event_name_map[ev] = ev

    pairs = []
    current_tourn_idx = 0
    for ev_orig in name_of_events:
        ev_std = event_name_map.get(ev_orig, ev_orig)
        if ev_std == 'To Win Match':
            if current_tourn_idx < len(name_of_tournaments):
                pairs.append((name_of_tournaments[current_tourn_idx].strip(), ev_std))
                current_tourn_idx += 1
            else:
                log_error(f"Tournament index {current_tourn_idx} out of bounds (total {len(name_of_tournaments)})")
        else:
            if 0 < current_tourn_idx <= len(name_of_tournaments):
                pairs.append((name_of_tournaments[current_tourn_idx - 1].strip(), ev_std))
    return pairs


def compare_pairs(old_pairs: List[Tuple], new_pairs: List[Tuple]) -> List[Tuple]:
    old_set = set(old_pairs)
    new_set = set(new_pairs)
    to_remove = [u for u in config.app_state.URLS if (u.tournament, u.event) in old_set - new_set]
    for u in to_remove:
        config.app_state.URLS.remove(u)
    return list(new_set - old_set)


def create_matches(
        num_players: int,
        players: List[str],
        odds: List[str],
        times: List[str],
        live_players: List
) -> List[Match]:
    new_matches = []
    live_set: set = set()
    for item in live_players:
        if isinstance(item, frozenset):
            live_set.update(item)
        else:
            live_set.add(item)

    num_matches = num_players // 2
    for i in range(num_matches):
        p1_idx, p2_idx = i * 2, i * 2 + 1
        if p2_idx >= len(players):
            break
        if players[p1_idx] is None or players[p2_idx] is None:
            break

        player1 = players[p1_idx].strip()
        player2 = players[p2_idx].strip()

        if player1 in live_set or player2 in live_set:
            continue

        odd1_idx = i
        odd2_idx = num_matches + i
        if odd1_idx >= len(odds) or odd2_idx >= len(odds):
            log_error(f"Odds index out of bounds for match {player1} vs {player2}")
            continue
        if odds[odd1_idx] is None or odds[odd2_idx] is None:
            continue

        odd1 = odds[odd1_idx].strip()
        odd2 = odds[odd2_idx].strip()
        if not odd1 or not odd2:
            continue

        match_time = times[i].strip() if i < len(times) and times[i] is not None else ""
        new_matches.append(Match(player1, player2, odd1, odd2, match_time))

    return new_matches


# ---------------------------------------------------------------------------
# Async Playwright functions
# ---------------------------------------------------------------------------

async def accept_cookies(page) -> None:
    """Click cookie consent button if present."""
    cookie_texts = ["Přijmout vše", "Aceptar todo", "Accept all", "Prijať všetky"]
    for text in cookie_texts:
        try:
            btn = await page.query_selector(f"button:has-text('{text}')")
            if btn:
                await btn.click()
                print(f"Accepted cookies ({text})")
                await asyncio.sleep(1)
                return
        except Exception:
            continue


async def handicap_names(players: List[str], page) -> List[str]:
    """Add handicap signs (+/-) to player names for handicap events."""
    signs, _ = await query_label(page, "src-ParticipantCenteredStacked80_Handicap", 5)
    if not signs:
        log_error("No handicap signs found on page")
        return players

    num_matches = len(players) // 2
    for i in range(len(players)):
        match_index = i // 2
        sign_idx = match_index if i % 2 == 0 else num_matches + match_index
        if sign_idx < len(signs) and signs[sign_idx] is not None:
            players[i] += signs[sign_idx].strip()
        else:
            log_error(f"Handicap sign index {sign_idx} out of bounds for player {players[i]}")
    return players


async def get_tourn_a_event(page) -> Tuple[List[str], Tuple[List[str], List]]:
    """
    Returns (tournament_texts, (event_texts, event_elements)).
    Filters TOTALS, normalises HANDICAPS/TO_WIN_MATCH translations.
    """
    lang = config.app_state.CURRENT_LANGUAGE
    tournaments, _ = await query_label(page, "sm-SplashMarketGroupButton_Text", 6)
    if not tournaments:
        return [], ([], [])

    event_texts, event_elements = await query_label(page, "sm-CouponLink_Title", 6)

    # Filter out TOTALS
    totals_text = config.TRANSLATIONS['TOTALS'].get(lang, '')
    filtered = [(t, e) for t, e in zip(event_texts, event_elements) if t != totals_text]
    if filtered:
        event_texts, event_elements = zip(*filtered)
        event_texts = list(event_texts)
        event_elements = list(event_elements)
    else:
        event_texts, event_elements = [], []

    # Normalise handicap/match names
    handicap_local = config.TRANSLATIONS['HANDICAPS'].get(lang, 'Match Handicap (Games)')
    win_match_local = config.TRANSLATIONS['TO_WIN_MATCH'].get(lang, 'To Win Match')
    event_texts = [
        'Handicaps' if t == handicap_local else
        'To Win Match' if t == win_match_local else t
        for t in event_texts
    ]

    # Strip brackets from tournament names
    tournaments = [t.replace('(', '').replace(')', '').replace('[', '').replace(']', '') for t in tournaments]

    return tournaments, (event_texts, event_elements)


async def look_odds(page, data: List[Dict[str, Any]], link: Link) -> None:
    """
    Navigate to link.url, scrape players/odds/times, detect live matches,
    build Match objects and call odds_existence.
    """
    from processing.event_processor import odds_existence  # late import

    try:
        print(f"\n🔍 PROCESSING: {link.tournament} - {link.event}")
        print(f"📍 URL: {link.url}")

        await page.goto(link.url, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # --- Detect live matches ---
        containers = await page.query_selector_all(".rcl-ParticipantFixtureDetails_LhsContainerInner")
        print(f"📊 Found {len(containers)} match containers")

        match_count = 0
        live_match_count = 0
        for container in containers:
            try:
                team_divs = await container.query_selector_all("div.rcl-ParticipantFixtureDetailsTeam_TeamName")
                if len(team_divs) < 2:
                    continue
                name1 = (await team_divs[0].inner_text()).strip()
                name2 = (await team_divs[1].inner_text()).strip()
                if not name1 or not name2:
                    continue
                match_count += 1

                live_el = await container.query_selector("div.pi-ScoreVariantInColumnsWithSets")
                if live_el:
                    pair = frozenset({name1, name2})
                    if pair not in config.app_state.PROCESSED_LIVE_MATCHES:
                        config.app_state.PROCESSED_LIVE_MATCHES.add(pair)
                        live_match_count += 1
                        print(f"    🔴 LIVE: {name1} vs {name2}")
                    else:
                        print(f"    🔴 LIVE (already tracked): {name1} vs {name2}")
                else:
                    print(f"    ⏰ Scheduled: {name1} vs {name2}")
            except Exception as e:
                log_error(f"Error processing container: {e}")
                continue

        print(f"📈 {match_count} total ({live_match_count} live, {match_count - live_match_count} scheduled)")

        # --- Player names ---
        all_players, _ = await query_label(page, "rcl-ParticipantFixtureDetailsTeam_TeamName", 5)
        all_players = [p for p in all_players if p]
        if not all_players:
            raise Exception(f"No player names found for {link.event}")

        # --- Live score count ---
        live_score_texts, _ = await query_label(page, "pi-ScoreVariantInColumnsWithSets_ScoreContainer", 0.15)
        num_live = len(live_score_texts) // 2

        # --- Odds ---
        if link.event == "Handicaps":
            all_players = await handicap_names(all_players, page)
        all_odds, _ = await query_label(page, "src-ParticipantCenteredStacked80_Odds", 5)
        all_odds = [o for o in all_odds if o]
        if not all_odds:
            raise Exception(f"No odds found for {link.event}")

        # --- Times ---
        all_times_raw, _ = await query_label(page, "rcl-ParticipantFixtureDetails_BookCloses", 2)
        all_times = [t for t in all_times_raw if t]

        # --- Date from market header ---
        try:
            date_els = await page.query_selector_all(".rcl-MarketHeaderLabel.rcl-MarketHeaderLabel-leftalign")
            if date_els:
                date_text = (await date_els[0].inner_text()).strip()
                parsed_date = parse_czech_date(date_text)
                if parsed_date:
                    all_times = [f"{parsed_date} {t}" for t in all_times]
                    print(f"Date parsed: {parsed_date}")
        except Exception as e:
            print(f"Date parse error: {e}")

        # --- Slice out live matches ---
        players_for_creation = all_players
        odds_for_creation = all_odds

        if num_live > 0:
            players_for_creation = all_players[2 * num_live:]
            num_total = len(all_odds) // 2
            if num_live <= num_total:
                p1_odds = all_odds[num_live:num_total]
                p2_odds = all_odds[num_total + num_live:]
                odds_for_creation = p1_odds + p2_odds
            else:
                log_error(f"More live matches ({num_live}) than total ({num_total}) — skipping odds slice")
                odds_for_creation = []

        # --- Build Match objects ---
        live_snapshot = list(config.app_state.PROCESSED_LIVE_MATCHES)
        print(f"🎯 Creating matches: {len(players_for_creation)} players, {len(odds_for_creation)} odds, {len(all_times)} times")

        matches = create_matches(len(players_for_creation), players_for_creation, odds_for_creation, all_times, live_snapshot)
        print(f"✅ {len(matches)} matches created for {link.tournament} - {link.event}")
        for i, m in enumerate(matches, 1):
            print(f"  📝 {i}: {m.player1} vs {m.player2} | {m.odd1} - {m.odd2} | {m.start_time}")

        event_obj = TournamentEvent(
            tournament=link.tournament,
            event=link.event,
            matches=matches,
            url=link.url,
        )
        odds_existence(event_obj, data)

    except Exception as e:
        log_error(f"look_odds error for {link.tournament} - {link.event}: {e}")
        # Remove broken link so we don't get stuck on it
        to_remove = [u for u in config.app_state.URLS if u.tournament == link.tournament and u.event == link.event]
        for u in to_remove:
            config.app_state.URLS.remove(u)
