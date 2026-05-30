from __future__ import annotations

import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from template_generation import (
    generate_analysis_payload,
    generate_document_contents,
    generate_drg_reason,
    generate_test_cases,
    get_generation_mode_label,
    get_template_runtime,
    normalize_generation_mode,
)


def test_generate_drg_reason_uses_path_template() -> None:
    result = generate_drg_reason(
        "A01.002+G01*",
        "伤寒性脑膜炎",
        "38.1000x002",
        "动脉内膜剥脱术",
        "MDCB",
        "神经系统疾病及功能障碍",
        "BB1",
        "神经系统复合手术组",
        "BB11",
        "神经系统复合手术，伴严重合并症或并发症",
        "MCC",
        "次诊断 J96.0 命中 CHS-DRG MCC 列表，排除表校验未排除。",
        "高",
        "已完成",
        "患者主诊断 A01.002+G01*，次诊断 J96.0，主要手术 38.1000x002。",
    )
    assert "主诊断为 A01.002+G01*（伤寒性脑膜炎）进入神经系统疾病及功能障碍（MDCB）" in result
    assert "主手术 38.1000x002（动脉内膜剥脱术）命中神经系统复合手术组（ADRG：BB1）" in result
    assert "该诊断属于MCC" in result
    assert "进入BB11" in result
    assert "LLM" not in result


def test_generate_analysis_payload_returns_four_sections() -> None:
    result = generate_analysis_payload(
        "医保DRG智能协同平台",
        "围绕住院病例信息、DRG规则匹配、多Agent协作与文档生成展开。",
        "输出需求分析、架构设计、测试用例和提交记录。",
        "高",
        "完整提交包",
    )
    assert len(result["summary"]) == 3, result
    assert "DRG规则匹配中心" in result["modules"], result
    assert len(result["risks"]) == 3, result
    assert len(result["recommendations"]) == 3, result


def test_generate_document_contents_uses_latest_case_context() -> None:
    analysis_payload = generate_analysis_payload(
        "医保DRG智能协同平台",
        "围绕住院病例信息、DRG规则匹配、多Agent协作与文档生成展开。",
        "输出需求分析、架构设计、测试用例和提交记录。",
        "高",
        "完整提交包",
    )
    latest_case = {
        "case_code": "CASE-005",
        "patient_name": "演示病例",
        "mdc_code": "MDCB",
        "adrg_code": "BB1",
        "drg_code": "BB11",
        "group_reason": "模板化入组路径说明",
    }
    result = generate_document_contents("医保DRG智能协同平台", analysis_payload, latest_case)
    assert "需求分析文档" in result, result
    assert "架构设计文档" in result, result
    assert "测试文档" in result, result
    assert "CASE-005" in result["架构设计文档"], result
    assert "模板化入组路径说明" in result["架构设计文档"], result


def test_generate_test_cases_returns_drg_grouping_cases() -> None:
    result = generate_test_cases(
        "医保DRG智能协同平台",
        [{"case_code": "CASE-005", "drg_code": "BB11"}],
    )
    assert len(result) == 3, result
    assert result[0]["case_code"] == "DRG-CASE-001", result
    assert "DRG=EC29" in result[0]["expected_text"], result
    assert result[1]["case_category"] == "边界", result
    assert "无CC/MCC" in result[1]["expected_text"], result
    assert result[2]["case_category"] == "异常", result
    assert "人工复核" in result[2]["expected_text"], result


def test_generation_mode_runtime_metadata() -> None:
    assert normalize_generation_mode("strict") == "strict"
    assert normalize_generation_mode("invalid-mode") == "balanced"
    assert get_generation_mode_label("creative") == "展示模式"
    runtime = get_template_runtime("creative")
    assert runtime["mode"] == "creative", runtime
    assert runtime["generator"] == "template", runtime


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
    print(f"All {len(ALL_TESTS)} template generation tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
