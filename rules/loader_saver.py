import csv
import os
from typing import List

import config
from models import BetRule, CombiRule, CombiRuleLeg
from utils.io import parse_float_robust, parse_int_robust, write_csv_file, read_csv_file
from utils.logging import log_error


def load_combi_rules_N(path: str = None) -> List[CombiRule]:
    if path is None:
        path = config.COMBI_THRESHOLDS_CSV
    default_header = ["PlayerSubstrings", "OpponentSubstrings", "MinOddsPerLeg",
                      "CombinedThresholdOdd", "BetValue", "Sent"]
    if not os.path.exists(path):
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=default_header).writeheader()
        except IOError as e:
            log_error(f"Could not create N-leg combi rules CSV at {path}: {e}")
        return []

    rows = read_csv_file(path)
    if not rows:
        return []

    reader_fieldnames_norm = {name.strip().lower(): name for name in rows[0].keys()}
    required = ["playersubstrings", "opponentsubstrings", "minoddsperleg",
                "combinedthresholdodd", "betvalue", "sent"]
    missing = [c for c in required if c not in reader_fieldnames_norm]
    if missing:
        log_error(f"N-leg combi CSV '{path}' missing columns: {missing}")
        return []

    parsed = []
    for i, row in enumerate(rows):
        try:
            def get(norm_key, fallback):
                return row.get(reader_fieldnames_norm.get(norm_key, fallback), "").strip()

            p_str = get("playersubstrings", "PlayerSubstrings")
            o_str = get("opponentsubstrings", "OpponentSubstrings")
            m_str = get("minoddsperleg", "MinOddsPerLeg")

            if not p_str:
                continue

            p_subs = [s.strip().upper() for s in p_str.split('#')]
            o_subs = [s.strip().upper() for s in o_str.split('#')]
            m_odds = [s.strip() for s in m_str.split('#')]

            num_legs = len(p_subs)
            if not (0 < num_legs == len(o_subs) == len(m_odds)):
                log_error(f"Skipping N-combi rule row {i+2}: mismatched leg counts")
                continue

            legs = []
            valid = True
            for k in range(num_legs):
                if not p_subs[k]:
                    valid = False
                    break
                legs.append(CombiRuleLeg(
                    player_substring=p_subs[k],
                    opponent_substring=o_subs[k],
                    min_odd=parse_float_robust(m_odds[k], 1.0)
                ))
            if not valid:
                continue

            parsed.append(CombiRule(
                legs=legs,
                combined_threshold_odd=parse_float_robust(get("combinedthresholdodd", "CombinedThresholdOdd"), 999.0),
                bet_value=get("betvalue", "BetValue"),
                sent=parse_int_robust(get("sent", "Sent"), 0),
                _source_row_dict=dict(row)
            ))
        except Exception as e:
            log_error(f"Error parsing N-combi rule row {i+2}: {e}")

    print(f"Loaded {len(parsed)} N-combi rules from {path}")
    return parsed


def save_combi_rules_N(rules: List[CombiRule], path: str = None) -> None:
    if path is None:
        path = config.COMBI_THRESHOLDS_CSV
    default_header = ["PlayerSubstrings", "OpponentSubstrings", "MinOddsPerLeg",
                      "CombinedThresholdOdd", "BetValue", "Sent"]
    header = list(rules[0]._source_row_dict.keys()) if rules and rules[0]._source_row_dict else default_header
    for col in default_header:
        if col not in header:
            header.append(col)

    rows = []
    for r in rules:
        d = r._source_row_dict.copy()
        d['PlayerSubstrings'] = '#'.join(leg.player_substring for leg in r.legs)
        d['OpponentSubstrings'] = '#'.join(leg.opponent_substring for leg in r.legs)
        d['MinOddsPerLeg'] = '#'.join(f"{leg.min_odd:.2f}" for leg in r.legs)
        d['CombinedThresholdOdd'] = f"{r.combined_threshold_odd:.2f}"
        d['BetValue'] = r.bet_value
        sent_key = next((k for k in d if k.strip().lower() == 'sent'), 'Sent')
        d[sent_key] = str(r.sent)
        rows.append(d)

    write_csv_file(path, rows, header)


def load_bet_rules(path: str = None) -> List[BetRule]:
    if path is None:
        path = config.THRESHOLDS_CSV
    default_header = ["PlayerSubstring", "OpponentSubstring", "ThresholdOdd", "BetValue", "Sent"]
    if not os.path.exists(path):
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=default_header).writeheader()
        except IOError as e:
            log_error(f"Could not create bet rules CSV at {path}: {e}")
        return []

    rules = []
    for i, row in enumerate(read_csv_file(path)):
        try:
            p_sub = row.get("PlayerSubstring", "").strip().upper()
            if not p_sub:
                continue
            rules.append(BetRule(
                player_substring=p_sub,
                opponent_substring=row.get("OpponentSubstring", "").strip().upper(),
                threshold_odd=parse_float_robust(row.get("ThresholdOdd", ""), 0.0),
                bet_value=row.get("BetValue", "").strip(),
                sent=parse_int_robust(row.get("Sent", "0"), 0),
            ))
        except Exception as e:
            log_error(f"Error parsing bet rule row {i+2}: {e}")

    print(f"Loaded {len(rules)} single bet rules from {path}")
    return rules


def save_bet_rules(rules: List[BetRule], path: str = None) -> None:
    if path is None:
        path = config.THRESHOLDS_CSV
    header = ["PlayerSubstring", "OpponentSubstring", "ThresholdOdd", "BetValue", "Sent"]
    rows = [{
        "PlayerSubstring": r.player_substring,
        "OpponentSubstring": r.opponent_substring,
        "ThresholdOdd": f"{r.threshold_odd:.2f}",
        "BetValue": r.bet_value,
        "Sent": str(r.sent),
    } for r in rules]
    write_csv_file(path, rows, header)
