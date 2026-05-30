from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from drg_rules import group_drg_case, resolve_diagnosis_code, resolve_procedure_code


def _as_cases(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    raise ValueError("JSON 顶层必须是病例对象或病例数组")


def _diagnosis_name(value: Any) -> str:
    return value.get("疾病名称", "") if isinstance(value, dict) else str(value or "")


def _diagnosis_code(value: Any) -> str:
    return value.get("疾病编码", "") if isinstance(value, dict) else ""


def _procedure_name(value: Any) -> str:
    return value.get("手术名称", "") if isinstance(value, dict) else ""


def _procedure_code(value: Any) -> str:
    return value.get("手术编码", "") if isinstance(value, dict) else ""


def _record_text(case_data: dict[str, Any]) -> str:
    primary = case_data.get("主要诊断") or {}
    procedure = case_data.get("主要手术") or {}
    secondary_names = [
        _diagnosis_name(item)
        for item in case_data.get("次要诊断列表", [])
    ]
    return (
        f"主诊断：{_diagnosis_name(primary)}；"
        f"次要诊断：{'、'.join(secondary_names)}；"
        f"主要手术：{_procedure_name(procedure)}。"
    )


def group_json_case(case_data: dict[str, Any]) -> dict[str, str]:
    primary = case_data.get("主要诊断") or {}
    procedure = case_data.get("主要手术") or {}
    primary_name = _diagnosis_name(primary)
    procedure_name = _procedure_name(procedure)
    secondary_codes = [
        resolve_diagnosis_code(_diagnosis_name(item), _diagnosis_code(item))
        for item in case_data.get("次要诊断列表", [])
    ]
    return group_drg_case(
        resolve_diagnosis_code(primary_name, _diagnosis_code(primary)),
        primary_name,
        resolve_procedure_code(procedure_name, _procedure_code(procedure)),
        procedure_name,
        secondary_codes,
        _record_text(case_data),
    )


def _expected_complication(value: str) -> str:
    return "无CC/MCC" if value == "NONE" else value


def verify_case(case_data: dict[str, Any], index: int) -> bool:
    grouped = group_json_case(case_data)
    expected = case_data.get("result") or {}
    print(f"\nCASE #{index}")
    print(f"MDC: {grouped['mdc_code']} / {grouped['mdc_name']}")
    print(f"ADRG: {grouped['adrg_code']} / {grouped['adrg_name']}")
    print(f"DRG: {grouped['drg_code']} / {grouped['drg_name']}")
    print(f"并发症等级: {grouped['complication_level']}")
    print(f"状态: {grouped['status']}")
    print("入组说明:")
    print(grouped["group_reason"])

    if not expected:
        print("未提供 result 期望值，仅打印实际结果。")
        return True

    checks = {
        "mdc": grouped["mdc_code"],
        "adrg": grouped["adrg_code"],
        "drg": grouped["drg_code"],
        "complication": grouped["complication_level"],
    }
    passed = True
    for key, actual in checks.items():
        expected_value = expected.get(key)
        if key == "complication":
            expected_value = _expected_complication(expected_value)
        ok = actual == expected_value
        passed = passed and ok
        mark = "PASS" if ok else "FAIL"
        print(f"{mark} {key}: expected={expected_value} actual={actual}")
    return passed


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: python quick_verify_drg.py case.json")
        return 2
    json_path = Path(sys.argv[1])
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    cases = _as_cases(payload)
    all_passed = True
    for index, case_data in enumerate(cases, start=1):
        all_passed = verify_case(case_data, index) and all_passed
    print("\n验证通过。" if all_passed else "\n验证失败，请检查上面的 FAIL 项。")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
