from __future__ import annotations

import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from drg_case_utils import (
    compute_distribution,
    filter_drg_cases,
    get_case_distributions,
    get_distribution_track_class,
    paginate_items,
    sort_drg_cases,
)


SAMPLE_CASES = [
    {
        "id": 1,
        "case_code": "CASE-001",
        "patient_name": "张某某",
        "diagnosis": "伤寒性脑膜炎（A01.002+G01）",
        "primary_diagnosis_code": "A01.002+G01",
        "primary_diagnosis_name": "伤寒性脑膜炎",
        "procedure_code": "38.1000X002",
        "procedure_name": "动脉内膜剥脱术",
        "mdc_code": "MDCB",
        "risk_level": "高",
        "status": "已完成",
        "created_at": "2026-04-18 10:00:00",
    },
    {
        "id": 2,
        "case_code": "CASE-002",
        "patient_name": "李某某",
        "diagnosis": "急性心肌梗死（I21.0）",
        "primary_diagnosis_code": "I21.0",
        "primary_diagnosis_name": "急性心肌梗死",
        "procedure_code": "36.10",
        "procedure_name": "冠状动脉搭桥术",
        "mdc_code": "MDCE",
        "risk_level": "中",
        "status": "分析中",
        "created_at": "2026-04-18 11:00:00",
    },
    {
        "id": 3,
        "case_code": "CASE-003",
        "patient_name": "赵某某",
        "diagnosis": "肾结石（N20.0）",
        "primary_diagnosis_code": "N20.0",
        "primary_diagnosis_name": "肾结石",
        "procedure_code": "56.0",
        "procedure_name": "输尿管取石术",
        "mdc_code": "MDCL",
        "risk_level": "低",
        "status": "需复核",
        "created_at": "2026-04-18 12:00:00",
    },
]


def test_filter_drg_cases_filters_by_mdc() -> None:
    result = filter_drg_cases(SAMPLE_CASES, "MDCE", "")
    assert [item["case_code"] for item in result] == ["CASE-002"], result


def test_filter_drg_cases_keyword_matches_diagnosis_and_procedure() -> None:
    by_diagnosis = filter_drg_cases(SAMPLE_CASES, "", "心肌")
    assert [item["case_code"] for item in by_diagnosis] == ["CASE-002"], by_diagnosis
    by_procedure = filter_drg_cases(SAMPLE_CASES, "", "取石")
    assert [item["case_code"] for item in by_procedure] == ["CASE-003"], by_procedure


def test_filter_drg_cases_combines_mdc_and_keyword() -> None:
    result = filter_drg_cases(SAMPLE_CASES, "MDCL", "N20")
    assert [item["case_code"] for item in result] == ["CASE-003"], result


def test_filter_drg_cases_filters_by_risk_and_status() -> None:
    result = filter_drg_cases(SAMPLE_CASES, "", "", "中", "分析中")
    assert [item["case_code"] for item in result] == ["CASE-002"], result


def test_sort_drg_cases_supports_created_and_risk_modes() -> None:
    created_desc = sort_drg_cases(SAMPLE_CASES, "created_desc")
    assert [item["case_code"] for item in created_desc] == ["CASE-003", "CASE-002", "CASE-001"], created_desc
    risk_desc = sort_drg_cases(SAMPLE_CASES, "risk_desc")
    assert [item["case_code"] for item in risk_desc] == ["CASE-001", "CASE-002", "CASE-003"], risk_desc


def test_paginate_items_clamps_page_and_returns_meta() -> None:
    result = paginate_items(SAMPLE_CASES, 5, page_size=2)
    assert result["page"] == 2, result
    assert result["total_pages"] == 2, result
    assert result["start_index"] == 3, result
    assert result["end_index"] == 3, result
    assert [item["case_code"] for item in result["items"]] == ["CASE-003"], result


def test_compute_distribution_uses_fallback_label() -> None:
    result = compute_distribution([
        {"status": "已完成"},
        {"status": ""},
        {},
    ], "status")
    assert result[0] == {"label": "未分类", "count": 2, "percent": 66.7}, result
    assert result[1] == {"label": "已完成", "count": 1, "percent": 33.3}, result


def test_get_distribution_track_class_maps_risk_and_status() -> None:
    assert get_distribution_track_class("risk", "高") == "distribution-track-danger"
    assert get_distribution_track_class("risk", "低") == "distribution-track-success"
    assert get_distribution_track_class("status", "已完成") == "distribution-track-success"
    assert get_distribution_track_class("status", "需复核") == "distribution-track-danger"
    assert get_distribution_track_class("mdc", "MDCE") == ""



def test_get_case_distributions_decorates_track_class() -> None:
    distributions = get_case_distributions(SAMPLE_CASES)
    risk_labels = {item["label"]: item["track_class"] for item in distributions["risk"]}
    status_labels = {item["label"]: item["track_class"] for item in distributions["status"]}
    mdc_labels = {item["label"]: item["track_class"] for item in distributions["mdc"]}
    assert risk_labels["高"] == "distribution-track-danger", risk_labels
    assert risk_labels["中"] == "distribution-track-warning", risk_labels
    assert risk_labels["低"] == "distribution-track-success", risk_labels
    assert status_labels["已完成"] == "distribution-track-success", status_labels
    assert status_labels["分析中"] == "distribution-track-warning", status_labels
    assert status_labels["需复核"] == "distribution-track-danger", status_labels
    assert mdc_labels["MDCE"] == "", mdc_labels


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
    print(f"All {len(ALL_TESTS)} case helper tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
