from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import group_drg_case, resolve_diagnosis_code, resolve_procedure_code


EXAMPLE_FILES = [
    PROJECT_ROOT / "drg_example(1).json",
    PROJECT_ROOT / "drg_example_nocode(1).json",
]


def get_diagnosis_name(value: Any) -> str:
    if isinstance(value, dict):
        return value.get("疾病名称", "")
    return str(value or "")


def get_diagnosis_code(value: Any) -> str:
    if isinstance(value, dict):
        return value.get("疾病编码", "")
    return ""


def get_procedure_name(value: dict[str, Any]) -> str:
    return value.get("手术名称", "")


def get_procedure_code(value: dict[str, Any]) -> str:
    return value.get("手术编码", "")


def build_record_text(case_data: dict[str, Any]) -> str:
    primary_name = get_diagnosis_name(case_data.get("主要诊断"))
    procedure_name = get_procedure_name(case_data.get("主要手术") or {})
    secondary_names = [item.get("疾病名称", "") for item in case_data.get("次要诊断列表", [])]
    return f"患者主要诊断为{primary_name}，次要诊断包括{'、'.join(secondary_names)}，主要手术为{procedure_name}。"


def group_example_case(case_data: dict[str, Any]) -> dict[str, str]:
    primary_value = case_data.get("主要诊断")
    primary_name = get_diagnosis_name(primary_value)
    primary_code = resolve_diagnosis_code(primary_name, get_diagnosis_code(primary_value))
    procedure_value = case_data.get("主要手术") or {}
    procedure_name = get_procedure_name(procedure_value)
    procedure_code = resolve_procedure_code(procedure_name, get_procedure_code(procedure_value))
    secondary_codes = [
        resolve_diagnosis_code(item.get("疾病名称", ""), item.get("疾病编码", ""))
        for item in case_data.get("次要诊断列表", [])
    ]
    return group_drg_case(
        primary_code,
        primary_name,
        procedure_code,
        procedure_name,
        secondary_codes,
        build_record_text(case_data),
    )


def assert_example_file_matches_expected(example_path: Path) -> None:
    cases = json.loads(example_path.read_text(encoding="utf-8"))
    assert len(cases) == 3, example_path
    for index, case_data in enumerate(cases, start=1):
        expected = case_data["result"]
        grouped = group_example_case(case_data)
        expected_complication = "无CC/MCC" if expected["complication"] == "NONE" else expected["complication"]
        assert grouped["mdc_code"] == expected["mdc"], (example_path.name, index, grouped)
        assert grouped["adrg_code"] == expected["adrg"], (example_path.name, index, grouped)
        assert grouped["drg_code"] == expected["drg"], (example_path.name, index, grouped)
        assert grouped["complication_level"] == expected_complication, (example_path.name, index, grouped)
        assert grouped["status"] == "已完成", (example_path.name, index, grouped)


def test_drg_example_with_codes_matches_expected_results() -> None:
    assert_example_file_matches_expected(EXAMPLE_FILES[0])


def test_drg_example_without_codes_matches_expected_results() -> None:
    assert_example_file_matches_expected(EXAMPLE_FILES[1])


def run_all_tests() -> None:
    tests = [
        test_drg_example_with_codes_matches_expected_results,
        test_drg_example_without_codes_matches_expected_results,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All 2 DRG JSON example tests passed.")


if __name__ == "__main__":
    run_all_tests()
