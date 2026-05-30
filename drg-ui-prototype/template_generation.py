from __future__ import annotations

import os
import json
import re
from typing import Any


MODE_LABELS = {
    "strict": "严谨模式",
    "balanced": "平衡模式",
    "creative": "展示模式",
}

MODE_HINTS = {
    "strict": "模板文案优先保证字段一致、事实准确和复核边界清晰。",
    "balanced": "模板文案兼顾事实链路、阅读顺序和页面可读性。",
    "creative": "模板文案更适合演示讲解，但不改变入组事实。",
}


def normalize_generation_mode(value: str | None) -> str:
    return value if value in MODE_LABELS else "balanced"


def get_default_generation_mode() -> str:
    return normalize_generation_mode(os.environ.get("DRG_TEMPLATE_MODE", "balanced"))


def get_generation_mode_label(mode: str | None) -> str:
    return MODE_LABELS[normalize_generation_mode(mode)]


def get_generation_mode_options() -> list[dict[str, str]]:
    return [{"value": value, "label": label} for value, label in MODE_LABELS.items()]


def get_template_runtime(mode: str | None = None) -> dict[str, Any]:
    active_mode = normalize_generation_mode(mode or get_default_generation_mode())
    return {
        "mode": active_mode,
        "label": get_generation_mode_label(active_mode),
        "hint": MODE_HINTS[active_mode],
        "generator": "template",
    }


def _clip_text(text: str, limit: int) -> str:
    normalized = " ".join((text or "").split())
    return normalized if len(normalized) <= limit else f"{normalized[:limit]}..."


def _join_non_empty(items: list[str], separator: str = "、") -> str:
    return separator.join(item for item in items if item)


def _infer_modules(description: str, target: str, doc_type: str) -> list[str]:
    combined = f"{description} {target} {doc_type}"
    modules = ["需求分析中心", "DRG规则匹配中心"]
    if "移动" in combined:
        modules.append("移动端协同中心")
    if "消息" in combined or "Agent" in combined or "协作" in combined or "智能体" in combined:
        modules.append("多Agent协作中心")
    if "文档" in combined or "提交" in combined:
        modules.append("文档生成中心")
    if "测试" in combined or "用例" in combined:
        modules.append("测试用例中心")
    modules.append("虚拟文档系统")
    return list(dict.fromkeys(modules))[:6]


def generate_drg_reason(
    primary_diagnosis_code: str,
    primary_diagnosis_name: str,
    procedure_code: str,
    procedure_name: str,
    mdc_code: str,
    mdc_name: str,
    adrg_code: str,
    adrg_name: str,
    drg_code: str,
    drg_name: str,
    complication_level: str,
    complication_reason: str,
    risk_level: str,
    status: str,
    raw_record: str,
    mode: str | None = None,
) -> str:
    del risk_level, raw_record, mode
    secondary_line = "次要诊断未命中MCC/CC列表"
    if complication_level in {"MCC", "CC"}:
        match = re.search(r"次诊断\s*([A-Z0-9.+*X-]+)", complication_reason, flags=re.IGNORECASE)
        matched_code = match.group(1) if match else ""
        secondary_line = f"次要诊断 {matched_code or '已提供次诊断'}"

    if complication_level == "MCC":
        complication_lines = [
            "- 该诊断属于MCC（严重合并症或并发症）列表",
            "- 经排除表校验，该并发症不被主诊断所排除",
            f"- 该ADRG支持并发症分层，因此MCC判定成立进入{drg_code}{drg_name}",
        ]
    elif complication_level == "CC":
        complication_lines = [
            "- 该诊断属于CC（一般合并症或并发症）列表",
            "- 经排除表校验，该并发症不被主诊断所排除",
            f"- 该ADRG支持并发症分层，因此CC判定成立进入{drg_code}{drg_name}",
        ]
    else:
        complication_lines = [
            "- 次要诊断未命中有效MCC/CC，或已被排除表排除",
            f"- 该ADRG按无合并症或并发症分层进入{drg_code}{drg_name}",
        ]

    review_line = "" if status == "已完成" else "\n\n当前结果需要人工复核。"
    return "\n\n".join(
        [
            f"主诊断为 {primary_diagnosis_code}（{primary_diagnosis_name or '未填写诊断名称'}）进入{mdc_name}（{mdc_code}）",
            f"主手术 {procedure_code}（{procedure_name or '未填写手术名称'}）命中{adrg_name}（ADRG：{adrg_code}）",
            secondary_line,
            "\n".join(complication_lines) + review_line,
        ]
    )


def generate_analysis_payload(
    project_name: str,
    description: str,
    target: str,
    priority: str,
    doc_type: str,
    mode: str | None = None,
) -> dict[str, list[str]]:
    del mode
    focus_excerpt = _clip_text(f"{description} {target}", 70) or "DRG规则匹配与文档生成闭环"
    modules = _infer_modules(description, target, doc_type)
    return {
        "summary": [
            f"围绕项目“{project_name}”展开分析，当前重点是{focus_excerpt}。",
            f"本轮优先级为{priority}，目标产物定位为{doc_type}。",
            "系统需要串联需求分析、病例入组、文档生成、测试用例生成和虚拟文档提交。",
        ],
        "modules": modules,
        "risks": [
            "病例编码、DRG规则文件或需求描述不完整时，入组结果和生成文档会出现上下文偏差。",
            "MDC、ADRG、MCC/CC和排除表版本不一致时，分组链路需要人工复核。",
            "文档、测试用例和提交记录若未同步刷新，会影响最终演示和验收一致性。",
        ],
        "recommendations": [
            "优先保证主诊断、次诊断和主手术编码字段完整，并保留每一步命中的规则来源。",
            f"围绕{_join_non_empty(modules[:3])}收口主流程，减少与简化入组无关的扩展逻辑。",
            "文档与测试用例应跟随最新病例结果同步生成，形成可追溯的提交批次。",
        ],
    }


def generate_document_contents(
    project_name: str,
    analysis_payload: dict[str, list[str]],
    latest_case: dict[str, Any] | None,
    mode: str | None = None,
) -> dict[str, str]:
    active_mode = normalize_generation_mode(mode or get_default_generation_mode())
    mode_line = f"当前采用{get_generation_mode_label(active_mode)}的模板化文案生成策略。"
    latest_case_lines = []
    if latest_case:
        latest_case_lines = [
            f"五、最新病例：{latest_case['case_code']} / {latest_case['patient_name']}。",
            f"六、入组链路：{latest_case['mdc_code']} -> {latest_case['adrg_code']} -> {latest_case['drg_code']}。",
            f"七、入组说明：{latest_case['group_reason']}",
        ]
    else:
        latest_case_lines = ["五、当前暂无新增病例，文档内容主要基于需求分析上下文生成。"]

    return {
        "需求分析文档": "\n".join(
            [
                f"一、项目名称：{project_name}",
                f"二、总体判断：{'；'.join(analysis_payload['summary'])}",
                f"三、功能模块：{_join_non_empty(analysis_payload['modules'])}。",
                f"四、风险识别：{'；'.join(analysis_payload['risks'])}",
                f"五、生成策略：{mode_line}",
            ]
        ),
        "架构设计文档": "\n".join(
            [
                "一、系统采用 Flask + SQLite 的本地可运行架构。",
                "二、桌面端负责需求分析、DRG入组、Agent、文档、测试与提交，移动端负责上报、消息与文档查看。",
                "三、项目、分析结果、病例、文档、测试用例和提交记录统一写入本地数据库，并同步落到虚拟文档目录。",
                "四、DRG入组模块只读取CHS_DRG_20规则文件，不再使用历史演示规则。",
                *latest_case_lines,
            ]
        ),
        "测试文档": "\n".join(
            [
                f"一、测试范围：覆盖{project_name}的主业务链路与DRG入组闭环。",
                "二、主流程覆盖：需求分析录入、病例入组、文档同步、测试用例刷新和提交中心留痕。",
                "三、重点边界：无CC/MCC分层、排除表命中、编码缺失、规则未命中和文档提交失败。",
                f"四、回归重点：{'；'.join(analysis_payload['recommendations'][:2])}",
                f"五、生成策略：{mode_line}",
            ]
        ),
    }


def generate_test_cases(project_name: str, drg_cases: list[dict[str, Any]], mode: str | None = None) -> list[dict[str, str]]:
    del project_name, drg_cases, mode
    normal_case_json = json.dumps(
        {
            "性别": "男",
            "年龄": 58,
            "主要诊断": {"疾病名称": "支气管胆管瘘", "疾病编码": "J86.000x013"},
            "次要诊断列表": [
                {"疾病名称": "肠粘连", "疾病编码": "K66.002"},
                {"疾病名称": "肝内胆管癌", "疾病编码": "C22.100"},
                {"疾病名称": "肝术后", "疾病编码": "Z98.800x115"},
            ],
            "主要手术": {"手术名称": "膈肌缝合术", "手术编码": "34.8200x002"},
            "其他手术列表": [
                {"手术名称": "内镜逆行胰胆管造影[ERCP]", "手术编码": "51.1000"},
                {"手术名称": "肠粘连松解术", "手术编码": "54.5903"},
                {"手术名称": "胸腔闭式引流术", "手术编码": "34.0401"},
                {"手术名称": "腹腔穿刺引流术", "手术编码": "54.9101"},
            ],
            "result": {
                "mdc": "MDCE",
                "adrg": "EC2",
                "drg": "EC29",
                "complication": "CC",
                "reason": [
                    "主诊断 J86.000x013 匹配到 MDCE（呼吸系统疾病及功能障碍）",
                    "手术 ['34.8200x002'] 匹配到 ADRG EC2",
                    "根据并发症等级选择 DRG EC29（纵隔、气管、胸壁其他手术）",
                ],
            },
        },
        ensure_ascii=False,
        indent=2,
    )
    no_cc_mcc_case_json = json.dumps(
        {
            "性别": "男",
            "年龄": 62,
            "主要诊断": {"疾病名称": "支气管胆管瘘", "疾病编码": "J86.000x013"},
            "次要诊断列表": [],
            "主要手术": {"手术名称": "膈肌缝合术", "手术编码": "34.8200x002"},
            "其他手术列表": [],
            "result": {
                "mdc": "MDCE",
                "adrg": "EC2",
                "drg": "EC29",
                "complication": "无CC/MCC",
                "reason": [
                    "主诊断 J86.000x013 匹配到 MDCE（呼吸系统疾病及功能障碍）",
                    "手术 ['34.8200x002'] 匹配到 ADRG EC2",
                    "未发现有效CC/MCC次诊断，按无合并症或并发症分层进入EC29",
                ],
            },
        },
        ensure_ascii=False,
        indent=2,
    )
    review_case_json = json.dumps(
        {
            "性别": "女",
            "年龄": 70,
            "主要诊断": {"疾病名称": "支气管胆管瘘", "疾病编码": ""},
            "次要诊断列表": [{"疾病名称": "肠粘连", "疾病编码": "K66.002"}],
            "主要手术": {"手术名称": "膈肌缝合术", "手术编码": ""},
            "其他手术列表": [],
            "result": {
                "mdc": "",
                "adrg": "",
                "drg": "",
                "complication": "需人工复核",
                "reason": [
                    "主要诊断编码为空或主要手术编码为空",
                    "系统不应生成确定DRG结果",
                    "该病例需要人工复核后再执行入组",
                ],
            },
        },
        ensure_ascii=False,
        indent=2,
    )
    return [
        {
            "case_code": "DRG-CASE-001",
            "feature": "EC29正常入组样例",
            "precondition_text": normal_case_json,
            "steps_text": "",
            "expected_text": (
                "入组结果为MDC=MDCE，ADRG=EC2，DRG=EC29，并发症层级=CC。"
                "原因应包含：主诊断J86.000x013匹配MDCE；手术34.8200x002匹配ADRG EC2；"
                "根据并发症等级选择DRG EC29（纵隔、气管、胸壁其他手术）。"
            ),
            "priority": "高",
            "case_category": "正常",
        },
        {
            "case_code": "DRG-CASE-002",
            "feature": "无CC/MCC边界场景校验",
            "precondition_text": no_cc_mcc_case_json,
            "steps_text": "",
            "expected_text": (
                "入组结果为MDC=MDCE，ADRG=EC2，DRG=EC25，并发症层级=无CC/MCC。"
                "原因应明确说明未发现有效CC/MCC次诊断，并按无合并症或并发症分层进入EC29。"
            ),
            "priority": "中",
            "case_category": "边界",
        },
        {
            "case_code": "DRG-CASE-003",
            "feature": "编码缺失需人工复核",
            "precondition_text": review_case_json,
            "steps_text": "",
            "expected_text": (
                "系统不应生成确定DRG结果；页面应提示主要诊断编码或主要手术编码不能为空。"
                "该病例需要人工复核，不能写入为已完成入组病例。"
            ),
            "priority": "高",
            "case_category": "异常",
        },
    ]
