from __future__ import annotations

import json
from pathlib import Path

from quick_verify_drg import group_json_case


CASE_FILES = [
    Path(__file__).resolve().parent / "case_ec29.json",
    Path(__file__).resolve().parent / "case_hc15.json",
]


def test_new_json_case_files_match_expected_result() -> None:
    for path in CASE_FILES:
        case_data = json.loads(path.read_text(encoding="utf-8"))
        expected = case_data.get("result")
        if not expected:
            continue
        grouped = group_json_case(case_data)
        assert grouped["mdc_code"] == expected["mdc"], (path.name, grouped)
        assert grouped["adrg_code"] == expected["adrg"], (path.name, grouped)
        assert grouped["drg_code"] == expected["drg"], (path.name, grouped)
        assert grouped["complication_level"] == expected["complication"], (path.name, grouped)


if __name__ == "__main__":
    test_new_json_case_files_match_expected_result()
    print("DRG JSON case tests passed.")
