from __future__ import annotations

import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from local_llm import (
    generate_analysis_payload,
    generate_document_contents,
    generate_drg_reason,
    generate_test_cases,
    get_generation_mode_label,
    get_local_llm_runtime,
    normalize_generation_mode,
)


def test_generate_drg_reason_keeps_core_facts() -> None:
    result = generate_drg_reason(
        "I21.0",
        "急性心肌梗死",
        "36.10",
        "冠状动脉搭桥术",
        "MDCE",
        "循环系统疾病大类",
        "FB1",
        "冠状动脉搭桥手术组",
        "FB13",
        "冠状动脉搭桥手术，伴一般合并症或并发症",
        "CC",
        "次诊断 I10 命中教学版 CC 列表。",
        "中",
        "已完成",
        "患者主诊断 I21.0，次诊断 I10，执行冠状动脉搭桥术。",
    )
    assert "MDCE" in result, result
    assert "FB1" in result, result
    assert "FB13" in result, result
    assert "本地微型LLM" in result, result


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
        "mdc_code": "MDCE",
        "adrg_code": "FB1",
        "drg_code": "FB13",
        "group_reason": "本地微型LLM生成的解释说明",
    }
    result = generate_document_contents("医保DRG智能协同平台", analysis_payload, latest_case)
    assert "需求分析文档" in result, result
    assert "架构设计文档" in result, result
    assert "测试文档" in result, result
    assert "CASE-005" in result["架构设计文档"], result
    assert "本地微型LLM生成的解释说明" in result["架构设计文档"], result


def test_generate_test_cases_returns_four_cases() -> None:
    result = generate_test_cases(
        "医保DRG智能协同平台",
        [{"case_code": "CASE-005", "drg_code": "FB13"}],
    )
    assert len(result) == 4, result
    assert result[0]["case_code"] == "TC-201", result
    assert "本地微型LLM" in result[0]["expected_text"], result
    assert result[-1]["case_code"] == "TC-204", result


def test_generation_mode_runtime_metadata() -> None:
    assert normalize_generation_mode("strict") == "strict"
    assert normalize_generation_mode("invalid-mode") == "balanced"
    assert get_generation_mode_label("creative") == "增强模式"
    runtime = get_local_llm_runtime("creative")
    assert runtime["mode"] == "creative", runtime
    assert runtime["external_corpus_loaded"] is True, runtime
    assert runtime["corpus_path"] == "local_llm_corpus.json", runtime


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
    print(f"All {len(ALL_TESTS)} local LLM tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
