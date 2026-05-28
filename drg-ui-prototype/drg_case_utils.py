from __future__ import annotations

from math import ceil
from typing import Any


CASE_PAGE_SIZE = 4
CASE_RISK_OPTIONS = [
    {"value": "高", "label": "高风险"},
    {"value": "中", "label": "中风险"},
    {"value": "低", "label": "低风险"},
]
CASE_STATUS_OPTIONS = [
    {"value": "已完成", "label": "已完成"},
    {"value": "分析中", "label": "分析中"},
    {"value": "需复核", "label": "需复核"},
]
CASE_SORT_OPTIONS = [
    {"value": "created_desc", "label": "最新录入优先"},
    {"value": "created_asc", "label": "最早录入优先"},
    {"value": "risk_desc", "label": "风险等级优先"},
    {"value": "case_code_asc", "label": "病例编号升序"},
]


def get_mdc_catalog(mdc_rules: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{"mdc_code": rule["mdc_code"], "mdc_name": rule["mdc_name"]} for rule in mdc_rules]



def normalize_case_choice(value: str, allowed_values: set[str]) -> str:
    return value if value in allowed_values else ""



def normalize_case_sort(sort_value: str) -> str:
    valid_values = {option["value"] for option in CASE_SORT_OPTIONS}
    return sort_value if sort_value in valid_values else "created_desc"



def filter_drg_cases(
    cases: list[dict[str, Any]],
    mdc_code: str,
    keyword: str,
    risk_level: str = "",
    status: str = "",
) -> list[dict[str, Any]]:
    filtered = cases
    if mdc_code:
        filtered = [item for item in filtered if item["mdc_code"] == mdc_code]
    if risk_level:
        filtered = [item for item in filtered if item.get("risk_level") == risk_level]
    if status:
        filtered = [item for item in filtered if item.get("status") == status]
    if keyword:
        lowered = keyword.lower()
        filtered = [
            item
            for item in filtered
            if lowered in (item.get("case_code") or "").lower()
            or lowered in (item.get("patient_name") or "").lower()
            or lowered in (item.get("diagnosis") or "").lower()
            or lowered in (item.get("primary_diagnosis_code") or "").lower()
            or lowered in (item.get("primary_diagnosis_name") or "").lower()
            or lowered in (item.get("procedure_code") or "").lower()
            or lowered in (item.get("procedure_name") or "").lower()
        ]
    return filtered



def sort_drg_cases(cases: list[dict[str, Any]], sort_value: str) -> list[dict[str, Any]]:
    if sort_value == "created_asc":
        return sorted(cases, key=lambda item: (item.get("created_at") or "", item.get("id") or 0))
    if sort_value == "risk_desc":
        risk_order = {"高": 0, "中": 1, "低": 2}
        return sorted(cases, key=lambda item: (risk_order.get(item.get("risk_level"), 9), -(item.get("id") or 0)))
    if sort_value == "case_code_asc":
        return sorted(cases, key=lambda item: (item.get("case_code") or "", item.get("id") or 0))
    return sorted(cases, key=lambda item: (item.get("created_at") or "", item.get("id") or 0), reverse=True)



def paginate_items(items: list[dict[str, Any]], page: int, page_size: int = CASE_PAGE_SIZE) -> dict[str, Any]:
    total_items = len(items)
    total_pages = max(1, ceil(total_items / page_size)) if total_items else 1
    current_page = min(max(page, 1), total_pages)
    start = (current_page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "page": current_page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_prev": current_page > 1,
        "has_next": current_page < total_pages,
        "prev_page": current_page - 1,
        "next_page": current_page + 1,
        "page_numbers": list(range(1, total_pages + 1)),
        "start_index": start + 1 if total_items else 0,
        "end_index": min(end, total_items),
    }



def compute_distribution(items: list[dict[str, Any]], key: str, fallback_label: str = "未分类") -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        value = (item.get(key) or fallback_label) or fallback_label
        counts[value] = counts.get(value, 0) + 1
    total = sum(counts.values()) or 1
    return [
        {
            "label": label,
            "count": count,
            "percent": round(count * 100 / total, 1),
        }
        for label, count in sorted(counts.items(), key=lambda entry: entry[1], reverse=True)
    ]



def get_distribution_track_class(distribution_type: str, label: str) -> str:
    if distribution_type == "risk":
        return {
            "高": "distribution-track-danger",
            "中": "distribution-track-warning",
            "低": "distribution-track-success",
        }.get(label, "")
    if distribution_type == "status":
        return {
            "已完成": "distribution-track-success",
            "分析中": "distribution-track-warning",
        }.get(label, "distribution-track-danger")
    return ""



def decorate_distribution_entries(entries: list[dict[str, Any]], distribution_type: str) -> list[dict[str, Any]]:
    return [
        {
            **entry,
            "track_class": get_distribution_track_class(distribution_type, entry["label"]),
        }
        for entry in entries
    ]



def get_case_distributions(cases: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "mdc": decorate_distribution_entries(compute_distribution(cases, "mdc_code"), "mdc"),
        "risk": decorate_distribution_entries(compute_distribution(cases, "risk_level"), "risk"),
        "status": decorate_distribution_entries(compute_distribution(cases, "status"), "status"),
    }
