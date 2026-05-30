from __future__ import annotations

import re
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

from common import dumps, get_current_generation_mode, now_str
from template_generation import generate_drg_reason
from platform_config import BASE_DIR

CHS_DRG_RULES_DIR = BASE_DIR / "CHS_DRG_20"
NO_CC_MCC_LEVEL = "无CC/MCC"
DRG_SUFFIX_BY_LEVEL = {"MCC": "1", "CC": "3", NO_CC_MCC_LEVEL: "5"}

# These maps only help demo JSON files that omit codes. DRG grouping itself is
# driven exclusively by CHS_DRG_20 rule files below.
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


def canonical_medical_code(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").strip().upper())


def medical_code_variants(value: str) -> list[str]:
    code = canonical_medical_code(value)
    if not code:
        return []
    variants = [code]
    if code.endswith("*"):
        variants.append(code[:-1])
    elif "+" in code:
        variants.append(f"{code}*")
    if re.fullmatch(r"[A-Z]\d{2}\.\d", code):
        variants.append(f"{code}00")
    if re.fullmatch(r"[A-Z]\d{2}\.\d{2}", code):
        variants.append(f"{code}0")
    if re.fullmatch(r"[A-Z]\d{2}\.\d{3}", code) and code.endswith("0"):
        variants.append(code[:-1])
    return list(dict.fromkeys(variants))


def parse_rule_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or " " not in stripped:
        return None
    code, name = stripped.split(maxsplit=1)
    if not re.match(r"^[A-Z0-9]", code, re.IGNORECASE):
        return None
    return canonical_medical_code(code), name.strip()


def read_rule_lines(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        return []
    rows: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_rule_line(line)
        if parsed is not None:
            rows.append(parsed)
    return rows


@lru_cache(maxsize=1)
def load_chs_rules() -> dict[str, Any]:
    if not CHS_DRG_RULES_DIR.exists():
        return {"available": False}

    mdc_names = dict(read_rule_lines(CHS_DRG_RULES_DIR / "MDC.dat"))
    adrg_names = dict(read_rule_lines(CHS_DRG_RULES_DIR / "ADRG.dat"))
    drg_names = dict(read_rule_lines(CHS_DRG_RULES_DIR / "DRG.dat"))
    mcc_groups = dict(read_rule_lines(CHS_DRG_RULES_DIR / "MCC.dat"))
    cc_groups = dict(read_rule_lines(CHS_DRG_RULES_DIR / "CC.dat"))
    cce_groups = dict(read_rule_lines(CHS_DRG_RULES_DIR / "CCE.dat"))

    mdc_diagnoses: dict[str, dict[str, str]] = {}
    for path in (CHS_DRG_RULES_DIR / "MDC").glob("*.dat"):
        mdc_code = canonical_medical_code(path.name.split("_", 1)[0])
        for diagnosis_code, diagnosis_name in read_rule_lines(path):
            mdc_diagnoses[diagnosis_code] = {
                "mdc_code": mdc_code,
                "mdc_name": mdc_names.get(mdc_code, path.stem.split("_", 1)[-1]),
                "matched_code": diagnosis_code,
                "diagnosis_name": diagnosis_name,
            }

    adrg_procedures: dict[str, list[dict[str, str]]] = {}
    for path in (CHS_DRG_RULES_DIR / "ADRG").glob("*.dat"):
        adrg_code = canonical_medical_code(path.name.split("_", 1)[0])
        adrg_name = adrg_names.get(adrg_code, path.stem.split("_", 1)[-1])
        for procedure_code, procedure_name in read_rule_lines(path):
            adrg_procedures.setdefault(procedure_code, []).append(
                {
                    "adrg_code": adrg_code,
                    "adrg_name": adrg_name,
                    "procedure_code": procedure_code,
                    "procedure_name": procedure_name,
                }
            )

    return {
        "available": True,
        "mdc_names": mdc_names,
        "adrg_names": adrg_names,
        "drg_names": drg_names,
        "mcc_groups": mcc_groups,
        "cc_groups": cc_groups,
        "cce_groups": cce_groups,
        "mdc_diagnoses": mdc_diagnoses,
        "adrg_procedures": adrg_procedures,
    }


def get_chs_mdc_catalog() -> list[dict[str, str]]:
    rules = load_chs_rules()
    return [
        {"mdc_code": code, "mdc_name": name}
        for code, name in sorted(rules.get("mdc_names", {}).items())
    ]


def lookup_code(mapping: dict[str, Any], code: str) -> Any | None:
    for variant in medical_code_variants(code):
        if variant in mapping:
            return mapping[variant]
    return None


def lookup_code_with_prefix(mapping: dict[str, Any], code: str) -> Any | None:
    result = lookup_code(mapping, code)
    if result is not None:
        return result
    variants = medical_code_variants(code)
    for variant in variants:
        for indexed_code, indexed_value in mapping.items():
            if indexed_code.startswith(variant):
                return indexed_value
    return None


def normalize_medical_code(value: str) -> str:
    return canonical_medical_code(value)


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
    return [normalize_medical_code(item) for item in re.split(r"[+，、;\s]+", value) if item.strip()]


def match_mdc(primary_diagnosis_code: str) -> dict[str, str]:
    rules = load_chs_rules()
    diagnosis_map = rules.get("mdc_diagnoses", {})
    for candidate in [primary_diagnosis_code, *tokenize_medical_code(primary_diagnosis_code)]:
        result = lookup_code_with_prefix(diagnosis_map, candidate)
        if result is not None:
            return result
    return {
        "mdc_code": "MDCQ",
        "mdc_name": "未命中CHS-DRG主要诊断大类",
        "matched_code": normalize_medical_code(primary_diagnosis_code),
    }


def match_adrg(mdc_code: str, procedure_code: str) -> dict[str, Any]:
    normalized_code = normalize_medical_code(procedure_code)
    rules = load_chs_rules()
    procedure_map = rules.get("adrg_procedures", {})
    expected_prefix = mdc_code.replace("MDC", "")[:1]
    for variant in medical_code_variants(normalized_code):
        candidates = procedure_map.get(variant, [])
        if not candidates:
            candidates = [
                rule
                for indexed_code, rules_for_code in procedure_map.items()
                if indexed_code.startswith(variant)
                for rule in rules_for_code
            ]
        for rule in candidates:
            if not expected_prefix or rule["adrg_code"].startswith(expected_prefix):
                return {
                    "adrg_code": rule["adrg_code"],
                    "adrg_name": rule["adrg_name"],
                    "procedure_prefixes": [rule["procedure_code"]],
                    "supports_complication": True,
                    "matched": True,
                    "matched_procedure": rule["procedure_code"],
                }
    return {
        "adrg_code": "QZ1",
        "adrg_name": "未命中CHS-DRG核心分组",
        "procedure_prefixes": [],
        "supports_complication": False,
        "matched": False,
        "matched_procedure": normalized_code or "未提供主手术编码",
    }


def is_chs_complication_excluded(primary_diagnosis_code: str, secondary_code: str, cce_groups: dict[str, str]) -> bool:
    secondary_group = lookup_code(cce_groups, secondary_code)
    if not secondary_group:
        return False
    for primary_candidate in [primary_diagnosis_code, *tokenize_medical_code(primary_diagnosis_code)]:
        primary_group = lookup_code(cce_groups, primary_candidate)
        if primary_group and primary_group == secondary_group:
            return True
    return False


def detect_complication_level(primary_diagnosis_code: str, secondary_codes: list[str]) -> dict[str, str]:
    rules = load_chs_rules()
    cc_result = None
    for raw_code in secondary_codes:
        normalized_code = normalize_medical_code(raw_code)
        if not normalized_code:
            continue
        if is_chs_complication_excluded(primary_diagnosis_code, normalized_code, rules.get("cce_groups", {})):
            continue
        if lookup_code(rules.get("mcc_groups", {}), normalized_code):
            return {
                "level": "MCC",
                "matched_code": normalized_code,
                "reason": f"次诊断 {normalized_code} 命中 CHS-DRG MCC 列表，排除表校验未排除。",
            }
        if cc_result is None and lookup_code(rules.get("cc_groups", {}), normalized_code):
            cc_result = {
                "level": "CC",
                "matched_code": normalized_code,
                "reason": f"次诊断 {normalized_code} 命中 CHS-DRG CC 列表，排除表校验未排除。",
            }
    if cc_result is not None:
        return cc_result
    return {"level": NO_CC_MCC_LEVEL, "matched_code": "", "reason": "未发现有效的 CC/MCC 次诊断，或已被排除表排除。"}


def build_drg_name(adrg_name: str, complication_level: str) -> str:
    suffix = {
        "MCC": "，伴严重合并症或并发症",
        "CC": "，伴一般合并症或并发症",
        NO_CC_MCC_LEVEL: "，无合并症或并发症",
    }.get(complication_level, "，需复核")
    return f"{adrg_name}{suffix}"


def build_drg_code(adrg_code: str, complication_level: str) -> str:
    rules = load_chs_rules()
    drg_names = rules.get("drg_names", {})
    preferred_suffix = DRG_SUFFIX_BY_LEVEL.get(complication_level, "9")
    for suffix in [preferred_suffix, "9", "5", "3", "1"]:
        candidate = f"{adrg_code}{suffix}"
        if candidate in drg_names:
            return candidate
    return f"{adrg_code}{preferred_suffix}"


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
    rules = load_chs_rules()
    drg_name = rules.get("drg_names", {}).get(drg_code, build_drg_name(adrg_result["adrg_name"], complication_result["level"]))
    status = "已完成" if mdc_result["mdc_code"] != "MDCQ" and adrg_result["adrg_code"] != "QZ1" and drg_code in rules.get("drg_names", {}) else "需复核"
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
        mode=get_current_generation_mode(),
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


def generate_random_groupable_case_input() -> dict[str, Any]:
    rules = load_chs_rules()
    diagnosis_rows = list(rules.get("mdc_diagnoses", {}).values())
    procedure_rows = [
        rule
        for rules_for_code in rules.get("adrg_procedures", {}).values()
        for rule in rules_for_code
    ]
    if not diagnosis_rows or not procedure_rows:
        raise ValueError("CHS-DRG规则文件不完整，无法随机生成可入组用例。")

    complication_sources = [
        ("MCC", list(rules.get("mcc_groups", {}).items())),
        ("CC", list(rules.get("cc_groups", {}).items())),
        (NO_CC_MCC_LEVEL, []),
    ]
    random.shuffle(complication_sources)

    for _ in range(300):
        diagnosis = random.choice(diagnosis_rows)
        expected_prefix = diagnosis["mdc_code"].replace("MDC", "")[:1]
        matched_procedures = [item for item in procedure_rows if item["adrg_code"].startswith(expected_prefix)]
        if not matched_procedures:
            continue
        procedure = random.choice(matched_procedures)
        secondary_items: list[dict[str, str]] = []

        for _, candidates in complication_sources:
            secondary_items = []
            if candidates:
                random.shuffle(candidates)
                for secondary_code, secondary_name in candidates[:80]:
                    if not is_chs_complication_excluded(diagnosis["matched_code"], secondary_code, rules.get("cce_groups", {})):
                        secondary_items = [{"疾病名称": secondary_name, "疾病编码": secondary_code}]
                        break
            grouped = group_drg_case(
                diagnosis["matched_code"],
                diagnosis.get("diagnosis_name", ""),
                procedure["procedure_code"],
                procedure["procedure_name"],
                [item["疾病编码"] for item in secondary_items],
                "",
            )
            if grouped["status"] == "已完成":
                return {
                    "性别": random.choice(["男", "女"]),
                    "年龄": random.randint(18, 88),
                    "主要诊断": {
                        "疾病名称": diagnosis.get("diagnosis_name", ""),
                        "疾病编码": diagnosis["matched_code"],
                    },
                    "次要诊断列表": secondary_items,
                    "主要手术": {
                        "手术名称": procedure["procedure_name"],
                        "手术编码": procedure["procedure_code"],
                    },
                    "其他手术列表": [],
                }

    raise ValueError("未能在当前规则集中随机生成可正常入组的输入用例。")


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
