"""
本地教学版 DRG 规则单元测试。

运行方式：
    python tests/test_drg_rules.py

该脚本零第三方依赖，直接使用 assert 验证以下函数的行为：
- match_mdc
- match_adrg
- detect_complication_level
- group_drg_case
覆盖 8 个教学版 MDC 大类以及 CC / MCC / 无 CC/MCC 三种情形。
"""

from __future__ import annotations

import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import (
    SIMPLIFIED_ADRG_RULES,
    SIMPLIFIED_MDC_RULES,
    detect_complication_level,
    group_drg_case,
    match_adrg,
    match_mdc,
)


def test_match_mdc_known_neurology() -> None:
    result = match_mdc("A01.002+G01")
    assert result["mdc_code"] == "MDCB", result


def test_match_mdc_known_circulatory() -> None:
    result = match_mdc("I21.0")
    assert result["mdc_code"] == "MDCE", result


def test_match_mdc_known_urinary() -> None:
    result = match_mdc("N17.9")
    assert result["mdc_code"] == "MDCL", result


def test_match_mdc_unknown_falls_back() -> None:
    result = match_mdc("Z99.9")
    assert result["mdc_code"] == "MDCQ", result


def test_match_adrg_surgical_hit() -> None:
    result = match_adrg("MDCE", "36.10")
    assert result["adrg_code"] == "FB1", result
    assert result["matched"] is True


def test_match_adrg_falls_back_to_medical_group() -> None:
    result = match_adrg("MDCA", "")
    assert result["adrg_code"] == "AZ1", result


def test_match_adrg_unknown_mdc() -> None:
    result = match_adrg("MDCQ", "")
    assert result["adrg_code"] == "QZ1", result


def test_detect_complication_level_mcc() -> None:
    result = detect_complication_level("A01.002+G01", ["J96.0"])
    assert result["level"] == "MCC", result


def test_detect_complication_level_cc_only() -> None:
    result = detect_complication_level("A01.002+G01", ["E87.1"])
    assert result["level"] == "CC", result


def test_detect_complication_level_none() -> None:
    result = detect_complication_level("E11.621", [])
    assert result["level"] == "无CC/MCC", result


def test_group_drg_case_neurology_with_mcc() -> None:
    grouped = group_drg_case(
        "A01.002+G01",
        "伤寒性脑膜炎",
        "38.1000X002",
        "动脉内膜剥脱术",
        ["J96.0"],
        "测试病例 A",
    )
    assert grouped["mdc_code"] == "MDCB", grouped
    assert grouped["adrg_code"] == "BB1", grouped
    assert grouped["drg_code"].endswith("1"), grouped
    assert grouped["complication_level"] == "MCC", grouped
    assert grouped["status"] == "已完成", grouped
    assert grouped["risk_level"] == "高", grouped


def test_group_drg_case_circulatory_with_cc() -> None:
    grouped = group_drg_case(
        "I21.0",
        "急性心肌梗死",
        "36.10",
        "冠状动脉搭桥术",
        ["I10"],
        "测试病例 B",
    )
    assert grouped["mdc_code"] == "MDCE", grouped
    assert grouped["adrg_code"] == "FB1", grouped
    assert grouped["complication_level"] == "CC", grouped
    assert grouped["drg_code"].endswith("3"), grouped


def test_group_drg_case_urinary_without_complication() -> None:
    grouped = group_drg_case(
        "N20.0",
        "肾结石",
        "56.0",
        "输尿管取石术",
        [],
        "测试病例 C",
    )
    assert grouped["mdc_code"] == "MDCL", grouped
    assert grouped["adrg_code"] == "LB1", grouped
    assert grouped["complication_level"] == "无CC/MCC", grouped
    assert grouped["drg_code"].endswith("5"), grouped


def test_group_drg_case_unknown_needs_review() -> None:
    grouped = group_drg_case(
        "Z99.9",
        "未知疾病",
        "",
        "",
        [],
        "测试病例 D",
    )
    assert grouped["status"] == "需复核", grouped
    assert grouped["risk_level"] == "高", grouped


def test_rule_catalog_has_eight_mdcs() -> None:
    codes = {rule["mdc_code"] for rule in SIMPLIFIED_MDC_RULES}
    assert codes == {"MDCA", "MDCB", "MDCD", "MDCE", "MDCF", "MDCG", "MDCH", "MDCL"}, codes
    for code in codes:
        assert SIMPLIFIED_ADRG_RULES.get(code), code


ALL_TESTS = [value for name, value in list(globals().items()) if name.startswith("test_") and callable(value)]


def main() -> int:
    failures: list[tuple[str, BaseException]] = []
    for test in ALL_TESTS:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as error:
            failures.append((test.__name__, error))
            print(f"FAIL {test.__name__}: {error}")
    print()
    if failures:
        print(f"{len(failures)} failed / {len(ALL_TESTS)} total")
        return 1
    print(f"All {len(ALL_TESTS)} DRG rule tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
