from typing import Tuple, Optional, Dict, Any, List
from itertools import combinations, permutations

from models import Match, CombiRuleLeg, BetRule, CombiRule
from rules.manager import get_bet_rules, get_combi_rules_N
from rules.loader_saver import save_bet_rules, save_combi_rules_N
from notifications.telegram import send_message, add_to_message
from messages.sendAll import send_message_all
from utils.logging import log_error
from utils.system import play_notification_sound
from utils.io import calculate_max_stake_from_odds


def _match_one_leg_for_N_combi(
        rule_leg_spec: CombiRuleLeg,
        new_match_obj: Match,
        is_handicap_event: bool
) -> Tuple[Optional[str], Optional[float]]:
    p_sub = rule_leg_spec.player_substring
    o_sub = rule_leg_spec.opponent_substring
    min_odd = rule_leg_spec.min_odd

    p1_upper = new_match_obj.player1.upper()
    p2_upper = new_match_obj.player2.upper()
    odd1 = new_match_obj.odd1_float
    odd2 = new_match_obj.odd2_float

    is_rule_handicap = '-' in p_sub or '+' in p_sub

    if odd1 is not None and odd1 >= min_odd and is_handicap_event == is_rule_handicap:
        if p_sub in p1_upper and (not o_sub or o_sub in p2_upper):
            return new_match_obj.player1, odd1

    if odd2 is not None and odd2 >= min_odd and is_handicap_event == is_rule_handicap:
        if p_sub in p2_upper and (not o_sub or o_sub in p1_upper):
            return new_match_obj.player2, odd2

    return None, None


def _match_single_pick_rules(match_obj: Match, bet_rules_single: List[Any], is_handicap_event: bool) -> List[Dict[str, Any]]:
    p1_upper = match_obj.player1.upper()
    p2_upper = match_obj.player2.upper()
    odd1 = match_obj.odd1_float
    odd2 = match_obj.odd2_float

    all_matching_rules = []
    best_notifications = {}

    for s_rule in bet_rules_single:
        if s_rule.sent == 1:
            continue

        p_sub = s_rule.player_substring
        o_sub = s_rule.opponent_substring
        thresh = s_rule.threshold_odd
        val = s_rule.bet_value

        if p_sub:
            is_rule_handicap = '-' in p_sub or '+' in p_sub
            is_match_handicap = '-' in p1_upper or '+' in p1_upper or '-' in p2_upper or '+' in p2_upper
            if is_handicap_event and not is_rule_handicap:
                continue
            if not is_handicap_event and is_rule_handicap:
                continue
            if is_match_handicap and not is_rule_handicap:
                continue

        if p_sub in p1_upper and (not o_sub or o_sub in p2_upper) and odd1 is not None and odd1 >= thresh:
            all_matching_rules.append(s_rule)
            if match_obj.player1 not in best_notifications or thresh > best_notifications[match_obj.player1]['threshold']:
                stake = calculate_max_stake_from_odds(odd1) if val.upper() == "MAX" else None
                best_notifications[match_obj.player1] = {
                    'player_name': match_obj.player1,
                    'odd': odd1,
                    'threshold': thresh,
                    'bet_value': f"{stake:.2f} (MAX)" if stake else val,
                    'rule': s_rule,
                }
        elif p_sub in p2_upper and (not o_sub or o_sub in p1_upper) and odd2 is not None and odd2 >= thresh:
            all_matching_rules.append(s_rule)
            if match_obj.player2 not in best_notifications or thresh > best_notifications[match_obj.player2]['threshold']:
                stake = calculate_max_stake_from_odds(odd2) if val.upper() == "MAX" else None
                best_notifications[match_obj.player2] = {
                    'player_name': match_obj.player2,
                    'odd': odd2,
                    'threshold': thresh,
                    'bet_value': f"{stake:.2f} (MAX)" if stake else val,
                    'rule': s_rule,
                }

    for rule in all_matching_rules:
        rule.sent = 1

    return list(best_notifications.values())


def check_matches(old_matches: List[List[str]], event: Any) -> int:
    bet_rules_single = get_bet_rules()
    combi_rules_N = get_combi_rules_N()

    update_lines = []
    header = f"*{event.tournament}* - *{event.event}*\n\n"
    update_lines.append(header)
    send_update = False
    has_new_matches = False
    has_changes = False
    pick_lines = []
    newly_identified: List[Match] = []
    is_handicap_event = "HANDICAP" in event.event.upper()

    for match_obj in event.matches:
        existed = False
        for old in old_matches:
            if match_obj.player1 == old[0] and match_obj.player2 == old[1]:
                existed = True
                old_odd1, old_odd2 = old[2], old[3]
                old_were_1_10 = (old_odd1 == "1.10" and old_odd2 == "1.10")

                if old_odd1 != match_obj.odd1 or old_odd2 != match_obj.odd2:
                    if old_were_1_10:
                        msg = add_to_message(match_obj, True)
                        if msg:
                            update_lines.append(msg)
                        send_update = True
                        has_new_matches = True
                        has_changes = True
                        newly_identified.append(match_obj)
                        notifications = _match_single_pick_rules(match_obj, bet_rules_single, is_handicap_event)
                        if notifications:
                            save_bet_rules(bet_rules_single)
                            for n in notifications:
                                is_max = n['rule'].bet_value.upper() == "MAX"
                                suffix = " (MAX)" if is_max else ""
                                pick_lines.append(f"🎯 Pick → *{n['player_name']}* @ {n['odd']:.2f} – Value: {n['bet_value']}{suffix}\n")
                    else:
                        msg = add_to_message(match_obj, False)
                        if msg:
                            update_lines.append(msg)
                        send_update = True
                        has_changes = True
                break

        if not existed:
            msg = add_to_message(match_obj, True)
            if msg:
                update_lines.append(msg)
            send_update = True
            has_new_matches = True
            has_changes = True
            play_notification_sound()
            newly_identified.append(match_obj)

            notifications = _match_single_pick_rules(match_obj, bet_rules_single, is_handicap_event)
            if notifications:
                save_bet_rules(bet_rules_single)
                for n in notifications:
                    is_max = n['rule'].bet_value.upper() == "MAX"
                    suffix = " (MAX)" if is_max else ""
                    pick_lines.append(f"🎯 Pick → *{n['player_name']}* @ {n['odd']:.2f} – Value: {n['bet_value']}{suffix}\n")

    # N-leg combi picks
    all_triggered_combis: List[Dict[str, Any]] = []
    if newly_identified and combi_rules_N:
        for combi_rule in combi_rules_N:
            if combi_rule.sent == 1:
                continue
            num_legs = len(combi_rule.legs)
            if num_legs == 0 or len(newly_identified) < num_legs:
                continue

            for selected in combinations(newly_identified, num_legs):
                for perm in permutations(selected, num_legs):
                    legs_details = []
                    product = 1.0
                    all_matched = True
                    for i in range(num_legs):
                        player_name, actual_odd = _match_one_leg_for_N_combi(combi_rule.legs[i], perm[i], is_handicap_event)
                        if player_name is None:
                            all_matched = False
                            break
                        legs_details.append({"player_name": player_name, "odd": actual_odd})
                        product *= actual_odd

                    if all_matched and product >= combi_rule.combined_threshold_odd:
                        all_triggered_combis.append({"rule": combi_rule, "legs_info": legs_details, "combined_odd": product})

    if all_triggered_combis:
        unique_rules = []
        for pick in all_triggered_combis:
            if pick["rule"] not in unique_rules:
                unique_rules.append(pick["rule"])
        marked = False
        for r in unique_rules:
            if r.sent == 0:
                r.sent = 1
                marked = True
        if marked:
            save_combi_rules_N(combi_rules_N)

        unique_combis = {}
        for pick in all_triggered_combis:
            key = tuple(sorted(leg['player_name'] for leg in pick['legs_info']))
            if key not in unique_combis or pick['rule'].combined_threshold_odd > unique_combis[key]['rule'].combined_threshold_odd:
                unique_combis[key] = pick

        for _, best in unique_combis.items():
            is_max = best['rule'].bet_value.upper() == "MAX"
            if is_max:
                stake = calculate_max_stake_from_odds(best['combined_odd'])
                line = f"🎯 *New COMBI Pick* — Value: {stake:.2f} (MAX)\n"
            else:
                line = f"🎯 *New COMBI Pick* — Value: {best['rule'].bet_value}\n"
            for leg in best['legs_info']:
                line += f"  — *{leg['player_name']}* @ {leg['odd']:.2f}\n"
            line += f"*Combined Odds:* {best['combined_odd']:.2f}\n"
            pick_lines.append(line)

    if send_update:
        try:
            send_message("".join(update_lines), notify=has_new_matches)
        except Exception as e:
            log_error(f"Failed to send update message: {e}")

    if pick_lines:
        header_picks = f"🔥 *Picks Alert!* 🔥\nEvent: {event.tournament} - {event.event}\n\n"
        try:
            send_message_all(header_picks + "".join(pick_lines), notify=True)
        except Exception as e:
            log_error(f"Failed to broadcast picks: {e}")

    return 1 if has_changes else 0
