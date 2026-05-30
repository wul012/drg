from __future__ import annotations

import re
from typing import Any

from common import dumps, get_current_local_llm_mode, now_str
from local_llm import generate_drg_reason

SIMPLIFIED_MDC_RULES = [
    {
        "mdc_code": "MDCB",
        "mdc_name": "神经系统疾病及功能障碍大类",
        "diagnosis_prefixes": ["G01", "I60", "I61", "I63", "A01.002"],
    },
    {
        "mdc_code": "MDCA",
        "mdc_name": "呼吸系统疾病大类",
        "diagnosis_prefixes": ["J18", "J44", "J96", "J12"],
    },
    {
        "mdc_code": "MDCD",
        "mdc_name": "消化系统疾病大类",
        "diagnosis_prefixes": ["K35", "K36", "K80", "K81"],
    },
    {
        "mdc_code": "MDCG",
        "mdc_name": "消化道疾病及功能障碍",
        "diagnosis_prefixes": ["C16"],
    },
    {
        "mdc_code": "MDCH",
        "mdc_name": "肝、胆、胰疾病及功能障碍",
        "diagnosis_prefixes": ["K83"],
    },
    {
        "mdc_code": "MDCF",
        "mdc_name": "内分泌与代谢系统疾病大类",
        "diagnosis_prefixes": ["E10", "E11", "E14", "L97"],
    },
    {
        "mdc_code": "MDCE",
        "mdc_name": "循环系统疾病大类",
        "diagnosis_prefixes": ["I20", "I21", "I25", "I50"],
    },
    {
        "mdc_code": "MDCL",
        "mdc_name": "泌尿系统疾病大类",
        "diagnosis_prefixes": ["N17", "N18", "N20", "N39"],
    },
]
SIMPLIFIED_ADRG_RULES = {
    "MDCB": [
        {
            "adrg_code": "BB1",
            "adrg_name": "神经系统复杂手术组",
            "procedure_prefixes": ["38.1000", "01.24", "01.59"],
            "supports_complication": True,
        },
        {
            "adrg_code": "BZ1",
            "adrg_name": "神经系统内科治疗组",
            "procedure_prefixes": [],
            "supports_complication": True,
        },
    ],
    "MDCA": [
        {
            "adrg_code": "AB1",
            "adrg_name": "呼吸系统手术组",
            "procedure_prefixes": ["33.22", "32.50"],
            "supports_complication": True,
        },
        {
            "adrg_code": "AZ1",
            "adrg_name": "呼吸系统内科治疗组",
            "procedure_prefixes": [],
            "supports_complication": True,
        },
    ],
    "MDCD": [
        {
            "adrg_code": "GD1",
            "adrg_name": "阑尾切除术组",
            "procedure_prefixes": ["47.0", "47.09", "47.1"],
            "supports_complication": True,
        },
        {
            "adrg_code": "GZ1",
            "adrg_name": "消化系统内科治疗组",
            "procedure_prefixes": [],
            "supports_complication": True,
        },
    ],
    "MDCG": [
        {
            "adrg_code": "GB2",
            "adrg_name": "胃、十二指肠大手术组",
            "procedure_prefixes": ["43.7"],
            "supports_complication": True,
        },
        {
            "adrg_code": "GZ2",
            "adrg_name": "消化道内科治疗组",
            "procedure_prefixes": [],
            "supports_complication": True,
        },
    ],
    "MDCH": [
        {
            "adrg_code": "HC1",
            "adrg_name": "胆总管手术组",
            "procedure_prefixes": ["51.63"],
            "supports_complication": True,
        },
        {
            "adrg_code": "HZ1",
            "adrg_name": "肝胆胰内科治疗组",
            "procedure_prefixes": [],
            "supports_complication": True,
        },
    ],
    "MDCF": [
        {
            "adrg_code": "KD1",
            "adrg_name": "糖尿病足手术组",
            "procedure_prefixes": ["86.2200", "86.22"],
            "supports_complication": True,
        },
        {
            "adrg_code": "KZ1",
            "adrg_name": "代谢系统内科治疗组",
            "procedure_prefixes": [],
            "supports_complication": True,
        },
    ],
    "MDCE": [
        {
            "adrg_code": "EC2",
            "adrg_name": "纵隔、气管、胸壁其他手术组",
            "procedure_prefixes": ["34.82"],
            "supports_complication": True,
        },
        {
            "adrg_code": "FB1",
            "adrg_name": "冠状动脉搭桥手术组",
            "procedure_prefixes": ["36.10", "36.11", "36.12", "36.15"],
            "supports_complication": True,
        },
        {
            "adrg_code": "FZ1",
            "adrg_name": "循环系统内科治疗组",
            "procedure_prefixes": [],
            "supports_complication": True,
        },
    ],
    "MDCL": [
        {
            "adrg_code": "LB1",
            "adrg_name": "肾与尿道手术组",
            "procedure_prefixes": ["55.01", "55.04", "56.0", "56.1"],
            "supports_complication": True,
        },
        {
            "adrg_code": "LZ1",
            "adrg_name": "泌尿系统内科治疗组",
            "procedure_prefixes": [],
            "supports_complication": True,
        },
    ],
}
SIMPLIFIED_MCC_CODES = {"J96", "I50", "N17", "R57", "A41"}
SIMPLIFIED_CC_CODES = {"E87", "D64", "I10", "N39", "J18"}
SIMPLIFIED_CC_EXACT_CODES = {"K66.002"}
SIMPLIFIED_EXCLUDED_CC_MCC = {"Z00", "Z01"}
SPECIAL_MDC_BY_PRIMARY_CODE = {
    "J86.000X013": {
        "mdc_code": "MDCE",
        "mdc_name": "呼吸系统疾病及功能障碍",
    },
}
DIAGNOSIS_NAME_CODE_MAP = {
    "胃窦恶性肿瘤": "C16.301",
    "肠粘连": "K66.002",
    "胃术后": "Z98.800X108",
    "腔隙性脑梗死": "I63.801",
    "肝囊肿": "K76.807",
    "支气管胆管瘘": "J86.000X013",
    "肝内胆管癌": "C22.100",
    "肝术后": "Z98.800X115",
    "胆管狭窄": "K83.105",
    "梗阻性黄疸": "K83.109",
    "胆管扩张": "K83.807",
    "腹腔粘连": "K66.007",
    "更换胆管引流管": "Z43.402",
}
PROCEDURE_NAME_CODE_MAP = {
    "腹腔镜胃大部切除伴胃空肠吻合术": "43.7X03",
    "膈肌缝合术": "34.8200X002",
    "胆总管切除术": "51.6303",
}
DRG_CODE_OVERRIDES = {
    ("GB2", "CC"): "GB29",
    ("EC2", "CC"): "EC29",
    ("HC1", "无CC/MCC"): "HC15",
}


def normalize_medical_code(value: str) -> str:
    return value.strip().upper()


def resolve_diagnosis_code(name: str, code: str | None = None) -> str:
    normalized_code = normalize_medical_code(code or "")
    if normalized_code:
        return normalized_code
    return DIAGNOSIS_NAME_CODE_MAP.get(name.strip(), "")


def resolve_procedure_code(name: str, code: str | None = None) -> str:
    normalized_code = normalize_medical_code(code or "")
    if normalized_code:
        return normalized_code
    return PROCEDURE_NAME_CODE_MAP.get(name.strip(), "")


def parse_code_list(raw_text: str) -> list[str]:
    if not raw_text:
        return []
    codes = []
    for item in re.split(r"[\s,，、;；\n]+", raw_text):
        value = item.strip()
        if value:
            codes.append(normalize_medical_code(DIAGNOSIS_NAME_CODE_MAP.get(value, value)))
    return codes


def tokenize_medical_code(value: str) -> list[str]:
    if not value:
        return []
    return [normalize_medical_code(item) for item in re.split(r"[+＋/、,，\s]+", value) if item.strip()]


def match_mdc(primary_diagnosis_code: str) -> dict[str, str]:
    tokens = tokenize_medical_code(primary_diagnosis_code)
    for token in tokens:
        special_rule = SPECIAL_MDC_BY_PRIMARY_CODE.get(token)
        if special_rule is not None:
            return {
                "mdc_code": special_rule["mdc_code"],
                "mdc_name": special_rule["mdc_name"],
                "matched_code": token,
            }
    for rule in SIMPLIFIED_MDC_RULES:
        for prefix in rule["diagnosis_prefixes"]:
            matched_token = next((token for token in tokens if token.startswith(prefix)), None)
            if matched_token:
                return {
                    "mdc_code": rule["mdc_code"],
                    "mdc_name": rule["mdc_name"],
                    "matched_code": matched_token,
                }
    return {"mdc_code": "MDCQ", "mdc_name": "未细分教学演示大类", "matched_code": normalize_medical_code(primary_diagnosis_code)}


def match_adrg(mdc_code: str, procedure_code: str) -> dict[str, Any]:
    normalized_code = normalize_medical_code(procedure_code)
    fallback_rule = None
    for rule in SIMPLIFIED_ADRG_RULES.get(mdc_code, []):
        prefixes = rule["procedure_prefixes"]
        if not prefixes:
            fallback_rule = rule
            continue
        if any(normalized_code.startswith(prefix) for prefix in prefixes):
            return {**rule, "matched": True, "matched_procedure": normalized_code}
    if fallback_rule is not None:
        return {**fallback_rule, "matched": bool(normalized_code), "matched_procedure": normalized_code or "未提供主手术编码"}
    return {
        "adrg_code": "QZ1",
        "adrg_name": "未细分教学演示组",
        "procedure_prefixes": [],
        "supports_complication": True,
        "matched": False,
        "matched_procedure": normalized_code or "未提供主手术编码",
    }


def detect_complication_level(primary_diagnosis_code: str, secondary_codes: list[str]) -> dict[str, str]:
    primary_tokens = tokenize_medical_code(primary_diagnosis_code)
    cc_result = None
    for raw_code in secondary_codes:
        normalized_code = normalize_medical_code(raw_code)
        if not normalized_code or normalized_code in SIMPLIFIED_EXCLUDED_CC_MCC:
            continue
        if any(normalized_code.startswith(token[:3]) for token in primary_tokens if len(token) >= 3):
            continue
        if any(normalized_code.startswith(prefix) for prefix in SIMPLIFIED_MCC_CODES):
            return {
                "level": "MCC",
                "matched_code": normalized_code,
                "reason": f"次诊断 {normalized_code} 命中教学版 MCC 列表。",
            }
        if cc_result is None and (normalized_code in SIMPLIFIED_CC_EXACT_CODES or any(normalized_code.startswith(prefix) for prefix in SIMPLIFIED_CC_CODES)):
            cc_result = {
                "level": "CC",
                "matched_code": normalized_code,
                "reason": f"次诊断 {normalized_code} 命中教学版 CC 列表。",
            }
    if cc_result is not None:
        return cc_result
    return {"level": "无CC/MCC", "matched_code": "", "reason": "未发现有效的 CC/MCC 次诊断。"}


def build_drg_name(adrg_name: str, complication_level: str) -> str:
    base_name = adrg_name[:-1] if adrg_name.endswith("组") else adrg_name
    suffix = {
        "MCC": "，伴严重合并症或并发症",
        "CC": "，伴一般合并症或并发症",
        "无CC/MCC": "，无合并症或并发症",
    }.get(complication_level, "，需复核")
    return f"{base_name}{suffix}"


def build_drg_code(adrg_code: str, complication_level: str) -> str:
    override = DRG_CODE_OVERRIDES.get((adrg_code, complication_level))
    if override:
        return override
    suffix = {"MCC": "1", "CC": "3", "无CC/MCC": "5"}.get(complication_level, "9")
    return f"{adrg_code}{suffix}"


def group_drg_case(
    primary_diagnosis_code: str,
    primary_diagnosis_name: str,
    procedure_code: str,
    procedure_name: str,
    secondary_codes: list[str],
    raw_record: str,
) -> dict[str, str]:
    mdc_result = match_mdc(primary_diagnosis_code)
    adrg_result = match_adrg(mdc_result["mdc_code"], procedure_code)
    complication_result = detect_complication_level(primary_diagnosis_code, secondary_codes)
    drg_code = build_drg_code(adrg_result["adrg_code"], complication_result["level"])
    drg_name = build_drg_name(adrg_result["adrg_name"], complication_result["level"])
    status = "已完成" if mdc_result["mdc_code"] != "MDCQ" and adrg_result["adrg_code"] != "QZ1" else "需复核"
    risk_level = "高" if complication_result["level"] == "MCC" or status == "需复核" else "中" if complication_result["level"] == "CC" else "低"
    group_reason = generate_drg_reason(
        primary_diagnosis_code,
        primary_diagnosis_name,
        procedure_code,
        procedure_name,
        mdc_result["mdc_code"],
        mdc_result["mdc_name"],
        adrg_result["adrg_code"],
        adrg_result["adrg_name"],
        drg_code,
        drg_name,
        complication_result["level"],
        complication_result["reason"],
        risk_level,
        status,
        raw_record,
        mode=get_current_local_llm_mode(),
    )
    return {
        "mdc_code": mdc_result["mdc_code"],
        "mdc_name": mdc_result["mdc_name"],
        "adrg_code": adrg_result["adrg_code"],
        "adrg_name": adrg_result["adrg_name"],
        "drg_code": drg_code,
        "drg_name": drg_name,
        "complication_level": complication_result["level"],
        "risk_level": risk_level,
        "status": status,
        "group_reason": group_reason,
    }


def build_case_record(
    case_code: str,
    patient_name: str,
    record_text: str,
    primary_diagnosis_code: str,
    primary_diagnosis_name: str,
    secondary_diagnosis_codes: list[str],
    procedure_code: str,
    procedure_name: str,
    created_at: str | None = None,
) -> dict[str, str]:
    timestamp = created_at or now_str()
    grouped_result = group_drg_case(
        primary_diagnosis_code,
        primary_diagnosis_name,
        procedure_code,
        procedure_name,
        secondary_diagnosis_codes,
        record_text,
    )
    return {
        "case_code": case_code,
        "patient_name": patient_name,
        "record_text": record_text,
        "primary_diagnosis_code": primary_diagnosis_code,
        "primary_diagnosis_name": primary_diagnosis_name,
        "secondary_diagnosis_codes_json": dumps(secondary_diagnosis_codes),
        "procedure_code": procedure_code,
        "procedure_name": procedure_name,
        "diagnosis": f"{primary_diagnosis_name}（{primary_diagnosis_code}）",
        "mdc_code": grouped_result["mdc_code"],
        "mdc_name": grouped_result["mdc_name"],
        "adrg_code": grouped_result["adrg_code"],
        "adrg_name": grouped_result["adrg_name"],
        "drg_code": grouped_result["drg_code"],
        "drg_name": grouped_result["drg_name"],
        "complication_level": grouped_result["complication_level"],
        "status": grouped_result["status"],
        "risk_level": grouped_result["risk_level"],
        "note": grouped_result["group_reason"],
        "group_reason": grouped_result["group_reason"],
        "created_at": timestamp,
        "updated_at": timestamp,
    }
