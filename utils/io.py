import json
import os
import csv
from typing import Any, Dict, List, Optional
from utils.logging import log_error


def parse_float_robust(val_str: Any, default_float: float) -> float:
    if val_str is None:
        return default_float
    stripped = str(val_str).strip()
    if not stripped:
        return default_float
    try:
        return float(stripped)
    except ValueError:
        return default_float


def parse_int_robust(val_str: Any, default_int: int) -> int:
    if val_str is None:
        return default_int
    stripped = str(val_str).strip()
    if not stripped:
        return default_int
    try:
        return int(stripped)
    except ValueError:
        return default_int


def save_json_to_file(data: Any, filepath: str) -> None:
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_error(f"Error saving JSON to {filepath}: {e}")


def load_json_from_file(filepath: str) -> Optional[Any]:
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) < 3:
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log_error(f"Error decoding JSON from {filepath}: {e}")
        return None
    except Exception as e:
        log_error(f"Error loading JSON from {filepath}: {e}")
        return None


def write_csv_file(filepath: str, data: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    tmp_path = filepath + ".tmp"
    try:
        with open(tmp_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            if data:
                writer.writerows(data)
        os.replace(tmp_path, filepath)
    except Exception as e:
        log_error(f"Error writing CSV to {filepath}: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def read_csv_file(filepath: str) -> List[Dict[str, str]]:
    parsed_rows = []
    if not os.path.exists(filepath):
        return parsed_rows
    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                log_error(f"Warning: CSV file '{filepath}' is empty or has no header.")
                return []
            for row in reader:
                parsed_rows.append(row)
    except Exception as e:
        log_error(f"Failed to open or read CSV file '{filepath}': {e}")
    return parsed_rows


def calculate_max_stake_from_odds(odds: float) -> float:
    odds_to_max_stake = {
        1.2: 625.0, 1.22: 568.182, 1.25: 500.0, 1.28: 446.429,
        1.3: 416.667, 1.33: 378.788, 1.36: 347.222, 1.4: 312.5,
        1.44: 284.091, 1.5: 250.0, 1.53: 235.849, 1.57: 219.298,
        1.61: 204.918, 1.66: 189.394, 1.72: 173.611, 1.8: 156.25,
        1.83: 150.602, 1.9: 138.889, 2.0: 125.0, 2.1: 113.636,
        2.25: 100.0, 2.37: 91.241, 2.5: 83.333, 2.62: 77.16,
        2.75: 71.429, 3.0: 62.5, 3.25: 55.556, 3.4: 52.083,
        3.75: 45.455, 4.0: 41.667, 4.33: 37.538, 4.5: 35.714,
        5.0: 31.25, 5.5: 27.778, 6.0: 25.0, 6.5: 22.727,
        7.0: 20.833, 8.5: 16.667, 9.0: 15.625, 11.0: 12.5,
    }
    if odds in odds_to_max_stake:
        return odds_to_max_stake[odds]
    if odds < min(odds_to_max_stake.keys()):
        return max(odds_to_max_stake.values())
    if odds > max(odds_to_max_stake.keys()):
        return min(odds_to_max_stake.values())
    sorted_odds = sorted(odds_to_max_stake.keys())
    closest_lower = None
    for k in sorted_odds:
        if k <= odds:
            closest_lower = k
        else:
            break
    if closest_lower is not None:
        return odds_to_max_stake[closest_lower]
    return min(odds_to_max_stake.values())
