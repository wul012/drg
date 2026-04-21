from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

from flask import Flask, abort, flash, g, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
DATABASE_PATH = INSTANCE_DIR / "drg_platform.db"

app = Flask(__name__, instance_path=str(INSTANCE_DIR), instance_relative_config=True)
app.config["SECRET_KEY"] = os.environ.get("DRG_APP_SECRET", "drg-ui-prototype-secret")
app.config["DATABASE"] = str(DATABASE_PATH)

VALID_PRIORITIES = {"高", "中", "低"}
VALID_DOC_TYPES = {"需求分析文档", "架构设计文档", "测试用例文档", "完整提交包"}
VALID_ROLES = {"分析员", "医生", "管理员"}
MAX_PROJECT_NAME_LENGTH = 40
MAX_DESCRIPTION_LENGTH = 300
MAX_TARGET_LENGTH = 200
MAX_REPORT_TITLE_LENGTH = 50
MAX_REPORT_CONTENT_LENGTH = 500
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 20
MIN_PASSWORD_LENGTH = 6
VIRTUAL_DOCS_DIR = INSTANCE_DIR / "virtual_docs"
SUBMISSION_ARTIFACTS_DIR = INSTANCE_DIR / "submissions"
MAX_PATIENT_NAME_LENGTH = 30
MAX_RECORD_TEXT_LENGTH = 800
MAX_MEDICAL_NAME_LENGTH = 60
MAX_MEDICAL_CODE_LENGTH = 40
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
SIMPLIFIED_EXCLUDED_CC_MCC = {"Z00", "Z01"}


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads(value: str | None) -> list[str]:
    if not value:
        return []
    return json.loads(value)


def normalize_choice(value: str, allowed_values: set[str], default: str) -> str:
    return value if value in allowed_values else default


def validate_required_text(field_name: str, value: str, max_length: int) -> str | None:
    if not value:
        return f"{field_name}不能为空。"
    if len(value) > max_length:
        return f"{field_name}不能超过{max_length}个字符。"
    return None


def validate_username(username: str) -> str | None:
    if not username:
        return "用户名不能为空。"
    if len(username) < MIN_USERNAME_LENGTH:
        return f"用户名至少需要 {MIN_USERNAME_LENGTH} 个字符。"
    if len(username) > MAX_USERNAME_LENGTH:
        return f"用户名不能超过 {MAX_USERNAME_LENGTH} 个字符。"
    return None


def validate_password(password: str) -> str | None:
    if not password:
        return "密码不能为空。"
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"密码至少需要 {MIN_PASSWORD_LENGTH} 个字符。"
    return None


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        connection = sqlite3.connect(app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        g.db = connection
    return g.db


@app.teardown_appcontext
def close_db(_: Any) -> None:
    database = g.pop("db", None)
    if database is not None:
        database.close()


def ensure_storage_directories() -> None:
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    VIRTUAL_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    SUBMISSION_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def get_table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()}


def ensure_column_exists(connection: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
    if column_name not in get_table_columns(connection, table_name):
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def run_schema_migrations(connection: sqlite3.Connection) -> None:
    ensure_column_exists(connection, "drg_cases", "record_text", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "drg_cases", "primary_diagnosis_code", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "drg_cases", "primary_diagnosis_name", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "drg_cases", "secondary_diagnosis_codes_json", "TEXT NOT NULL DEFAULT '[]'")
    ensure_column_exists(connection, "drg_cases", "procedure_code", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "drg_cases", "procedure_name", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "drg_cases", "mdc_code", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "drg_cases", "mdc_name", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "drg_cases", "adrg_code", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "drg_cases", "adrg_name", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "drg_cases", "drg_name", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "drg_cases", "complication_level", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "drg_cases", "group_reason", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "drg_cases", "updated_at", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "documents", "source_agent", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "documents", "storage_path", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "documents", "received_at", "TEXT NOT NULL DEFAULT ''")
    ensure_column_exists(connection, "test_cases", "case_category", "TEXT NOT NULL DEFAULT '正常'")
    ensure_column_exists(connection, "submissions", "artifact_path", "TEXT NOT NULL DEFAULT ''")


def normalize_medical_code(value: str) -> str:
    return value.strip().upper()


def parse_code_list(raw_text: str) -> list[str]:
    if not raw_text:
        return []
    return [normalize_medical_code(item) for item in re.split(r"[\s,，、;；\n]+", raw_text) if item.strip()]


def tokenize_medical_code(value: str) -> list[str]:
    if not value:
        return []
    return [normalize_medical_code(item) for item in re.split(r"[+＋/、,，\s]+", value) if item.strip()]


def match_mdc(primary_diagnosis_code: str) -> dict[str, str]:
    tokens = tokenize_medical_code(primary_diagnosis_code)
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
        if cc_result is None and any(normalized_code.startswith(prefix) for prefix in SIMPLIFIED_CC_CODES):
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
    suffix = {"MCC": "1", "CC": "3", "无CC/MCC": "5"}.get(complication_result["level"], "9")
    drg_code = f"{adrg_result['adrg_code']}{suffix}"
    status = "已完成" if mdc_result["mdc_code"] != "MDCQ" and adrg_result["adrg_code"] != "QZ1" else "需复核"
    risk_level = "高" if complication_result["level"] == "MCC" or status == "需复核" else "中" if complication_result["level"] == "CC" else "低"
    reason_parts = [
        f"主诊断 {primary_diagnosis_code}（{primary_diagnosis_name}）命中 {mdc_result['mdc_code']} {mdc_result['mdc_name']}。",
        f"主手术 {procedure_code or '未填写'}（{procedure_name or '未填写'}）归入 {adrg_result['adrg_code']} {adrg_result['adrg_name']}。",
        complication_result["reason"],
    ]
    if raw_record:
        reason_parts.append("电子病历摘要已纳入本地教学规则匹配。")
    if status != "已完成":
        reason_parts.append("当前结果未命中完整教学规则，建议人工复核。")
    return {
        "mdc_code": mdc_result["mdc_code"],
        "mdc_name": mdc_result["mdc_name"],
        "adrg_code": adrg_result["adrg_code"],
        "adrg_name": adrg_result["adrg_name"],
        "drg_code": drg_code,
        "drg_name": build_drg_name(adrg_result["adrg_name"], complication_result["level"]),
        "complication_level": complication_result["level"],
        "risk_level": risk_level,
        "status": status,
        "group_reason": "；".join(reason_parts),
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


def sanitize_filename(value: str) -> str:
    sanitized = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", value).strip("._")
    return sanitized or "artifact"


def to_relative_storage_path(path: Path) -> str:
    try:
        return str(path.relative_to(BASE_DIR))
    except ValueError:
        return str(path)


def write_virtual_document(project_name: str, title: str, version: str, content: str, received_at: str) -> str:
    ensure_storage_directories()
    file_name = f"{sanitize_filename(project_name)}_{sanitize_filename(title)}_{sanitize_filename(version)}_{received_at.replace(':', '').replace(' ', '-')}.txt"
    file_path = VIRTUAL_DOCS_DIR / file_name
    file_path.write_text(content, encoding="utf-8")
    return to_relative_storage_path(file_path)


def write_submission_artifact(batch_name: str, operator_name: str, selected_documents: list[dict[str, Any]], submitted_at: str) -> str:
    ensure_storage_directories()
    file_name = f"{sanitize_filename(batch_name)}_{submitted_at.replace(':', '').replace(' ', '-')}.txt"
    file_path = SUBMISSION_ARTIFACTS_DIR / file_name
    content_lines = [
        f"批次名称：{batch_name}",
        f"操作人：{operator_name}",
        f"提交时间：{submitted_at}",
        "文档清单：",
    ]
    content_lines.extend([f"- {item['title']} | {item['version']} | {item['status']}" for item in selected_documents])
    file_path.write_text("\n".join(content_lines), encoding="utf-8")
    return to_relative_storage_path(file_path)


def init_database() -> None:
    ensure_storage_directories()
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            priority TEXT NOT NULL,
            phase TEXT NOT NULL,
            target TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL UNIQUE,
            summary_json TEXT NOT NULL,
            modules_json TEXT NOT NULL,
            risks_json TEXT NOT NULL,
            recommendations_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );

        CREATE TABLE IF NOT EXISTS drg_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            case_code TEXT NOT NULL,
            patient_name TEXT NOT NULL,
            diagnosis TEXT NOT NULL,
            drg_code TEXT NOT NULL,
            status TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            note TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );

        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            owner TEXT NOT NULL,
            status TEXT NOT NULL,
            focus TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            version TEXT NOT NULL,
            content TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );

        CREATE TABLE IF NOT EXISTS test_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            case_code TEXT NOT NULL,
            feature TEXT NOT NULL,
            precondition_text TEXT NOT NULL,
            steps_text TEXT NOT NULL,
            expected_text TEXT NOT NULL,
            priority TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );

        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            batch_name TEXT NOT NULL,
            status TEXT NOT NULL,
            docs_count INTEGER NOT NULL,
            operator_name TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );

        CREATE TABLE IF NOT EXISTS mobile_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            priority TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );
        """
    )
    run_schema_migrations(connection)
    connection.commit()
    connection.close()


def build_analysis_payload(project_name: str, description: str, target: str, priority: str, doc_type: str) -> dict[str, list[str]]:
    focus = f"{description} {target}".strip().replace("\n", " ")
    short_focus = focus[:40] if focus else "DRG规则匹配与文档生成"
    return {
        "summary": [
            f"围绕“{project_name}”，当前优先处理 {short_focus}。",
            f"项目优先级为{priority}，当前目标文档类型为{doc_type}。",
            "建议采用PC端主导分析、移动端承载快速上报与查看的协同模式。",
        ],
        "modules": [
            "需求分析中心",
            "DRG规则匹配中心",
            "多Agent协作中心",
            "文档生成中心",
            "测试与提交中心",
        ],
        "risks": [
            "病例编码和病案摘要不完整会影响DRG分组准确性。",
            "Agent状态同步不清晰会造成任务链路中断。",
            "提交前如果文档版本不一致，会影响最终演示效果。",
        ],
        "recommendations": [
            "优先保证需求分析 -> 文档生成 -> 提交中心这一主流程闭环。",
            "将移动端收敛为上报、消息、文档查看三个高频场景。",
            "把当前阶段、最新文档和最近提交记录集中展示在工作台首页。",
        ],
    }


def get_latest_case(drg_cases: list[Any]) -> Any | None:
    return drg_cases[-1] if drg_cases else None


def build_agents_payload(
    project_name: str,
    analysis_payload: dict[str, list[str]],
    drg_cases: list[Any],
    has_submissions: bool,
) -> list[dict[str, str]]:
    latest_case = get_latest_case(drg_cases)
    latest_case_label = latest_case["case_code"] if latest_case else "暂无病例"
    return [
        {"name": "需求分析 Agent", "owner": "产品侧", "status": "已完成", "focus": f"完成 {project_name} 的需求摘要、模块建议与风险识别"},
        {"name": "DRG 分析 Agent", "owner": "业务侧", "status": "已完成" if latest_case else "待处理", "focus": f"最近处理病例：{latest_case_label}"},
        {"name": "文档生成 Agent", "owner": "交付侧", "status": "已完成", "focus": f"基于 {len(analysis_payload['modules'])} 个核心模块生成文档"},
        {"name": "测试用例 Agent", "owner": "测试侧", "status": "已完成" if latest_case else "运行中", "focus": "输出正常、边界、异常三类测试用例"},
        {"name": "提交 Agent", "owner": "管理侧", "status": "已完成" if has_submissions else "待处理", "focus": "接收虚拟文档系统文档并生成提交批次"},
    ]


def build_messages_payload(project_name: str, analysis_payload: dict[str, list[str]], drg_cases: list[Any]) -> list[dict[str, str]]:
    timestamp = now_str()
    latest_case = get_latest_case(drg_cases)
    latest_case_message = (
        f"最新病例 {latest_case['case_code']} 已完成入组，结果为 {latest_case['drg_code']}。"
        if latest_case
        else "当前尚无已录入病例，等待 DRG 规则匹配输入。"
    )
    return [
        {
            "sender": "需求分析 Agent",
            "receiver": "DRG 分析 Agent",
            "content": f"已解析 {project_name} 的需求上下文，共识别 {len(analysis_payload['modules'])} 个核心模块。",
            "source": "desktop",
            "created_at": timestamp,
        },
        {
            "sender": "DRG 分析 Agent",
            "receiver": "文档生成 Agent",
            "content": latest_case_message,
            "source": "desktop",
            "created_at": timestamp,
        },
        {
            "sender": "文档生成 Agent",
            "receiver": "测试用例 Agent",
            "content": "虚拟文档系统已接收最新需求、架构与测试文档，请同步刷新测试覆盖清单。",
            "source": "desktop",
            "created_at": timestamp,
        },
    ]


def build_documents_payload(project_name: str, analysis_payload: dict[str, list[str]], drg_cases: list[Any]) -> list[dict[str, str]]:
    timestamp = now_str()
    latest_case = get_latest_case(drg_cases)
    latest_case_lines = [
        f"最新病例：{latest_case['case_code']} / {latest_case['patient_name']}",
        f"入组结果：{latest_case['mdc_code']} -> {latest_case['adrg_code']} -> {latest_case['drg_code']}",
        f"入组说明：{latest_case['group_reason']}",
    ] if latest_case else ["当前暂无病例入组结果，文档基于需求分析上下文生成。"]
    payload = [
        {
            "title": "需求分析文档",
            "status": "已生成",
            "version": "V2.0",
            "updated_at": timestamp,
            "source_agent": "需求分析 Agent",
            "content": "\n".join(
                [
                    f"一、项目名称：{project_name}",
                    f"二、需求摘要：{'；'.join(analysis_payload['summary'])}",
                    f"三、建议模块：{'、'.join(analysis_payload['modules'])}",
                    f"四、风险识别：{'；'.join(analysis_payload['risks'])}",
                ]
            ),
        },
        {
            "title": "架构设计文档",
            "status": "已生成",
            "version": "V2.0",
            "updated_at": timestamp,
            "source_agent": "文档生成 Agent",
            "content": "\n".join(
                [
                    "一、系统采用 Flask + SQLite 的本地可运行架构。",
                    "二、PC端包括工作台、需求分析、DRG入组、Agent、文档、测试和提交中心。",
                    "三、移动端包括上报、消息和文档查看，并与桌面端消息流联动。",
                    *latest_case_lines,
                ]
            ),
        },
        {
            "title": "测试文档",
            "status": "已生成",
            "version": "V2.0",
            "updated_at": timestamp,
            "source_agent": "测试用例 Agent",
            "content": "\n".join(
                [
                    f"一、重点覆盖 {project_name} 的主业务链路与 DRG 入组闭环。",
                    "二、覆盖正常入组、无 CC/MCC 边界场景以及编码缺失异常场景。",
                    "三、覆盖虚拟文档系统接收、提交中心留痕和移动端上报同步。",
                ]
            ),
        },
    ]
    for item in payload:
        item["received_at"] = item["updated_at"]
        item["storage_path"] = write_virtual_document(project_name, item["title"], item["version"], item["content"], item["received_at"])
    return payload


def build_test_cases_payload(project_name: str, drg_cases: list[Any]) -> list[dict[str, str]]:
    timestamp = now_str()
    latest_case = get_latest_case(drg_cases)
    latest_case_code = latest_case["case_code"] if latest_case else "CASE-DEMO"
    latest_case_drg = latest_case["drg_code"] if latest_case else "GD15"
    return [
        {
            "case_code": "TC-201",
            "feature": "DRG入组正常场景",
            "precondition_text": "已录入完整电子病历、主诊断、次诊断和主手术编码",
            "steps_text": f"提交病例 {latest_case_code} 并执行本地教学规则入组",
            "expected_text": f"成功输出 MDC / ADRG / DRG，且最新病例结果展示为 {latest_case_drg}",
            "priority": "高",
            "case_category": "正常",
            "updated_at": timestamp,
        },
        {
            "case_code": "TC-202",
            "feature": "无CC/MCC边界场景",
            "precondition_text": "次诊断编码为空或未命中 CC/MCC 列表",
            "steps_text": "提交仅包含主诊断与主手术的病例并执行入组",
            "expected_text": "系统输出无CC/MCC分层结果，并给出明确入组原因说明",
            "priority": "中",
            "case_category": "边界",
            "updated_at": timestamp,
        },
        {
            "case_code": "TC-203",
            "feature": "编码缺失异常场景",
            "precondition_text": "主诊断编码或主手术编码为空",
            "steps_text": f"在 {project_name} 的病例录入页提交不完整编码数据",
            "expected_text": "页面阻止提交并给出字段校验提示，不写入错误病例",
            "priority": "高",
            "case_category": "异常",
            "updated_at": timestamp,
        },
        {
            "case_code": "TC-204",
            "feature": "虚拟文档接收与提交",
            "precondition_text": "系统已生成最新需求、架构与测试文档",
            "steps_text": "在提交中心勾选文档并确认提交",
            "expected_text": "生成提交批次、落地本地提交清单，并把项目阶段更新为已提交待审核",
            "priority": "中",
            "case_category": "正常",
            "updated_at": timestamp,
        },
    ]


def seed_demo_data() -> None:
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    has_user = cursor.execute("SELECT id FROM users LIMIT 1").fetchone()
    if not has_user:
        created_at = now_str()
        users = [
            ("admin", generate_password_hash("123456"), "管理员", created_at),
            ("doctor", generate_password_hash("123456"), "医生", created_at),
            ("analyst", generate_password_hash("123456"), "分析员", created_at),
        ]
        cursor.executemany(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            users,
        )

    has_project = cursor.execute("SELECT id FROM projects LIMIT 1").fetchone()
    if not has_project:
        created_at = now_str()
        project_name = "医保DRG智能协同平台"
        cursor.execute(
            """
            INSERT INTO projects (name, owner_name, priority, phase, target, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_name,
                "王医生",
                "高",
                "需求分析中",
                "生成需求分析、测试用例与提交包",
                "围绕住院病例DRG入组、文档生成与智能协作的课程完整项目。",
                created_at,
                created_at,
            ),
        )
        project_id = cursor.lastrowid

        analysis_payload = build_analysis_payload(
            project_name,
            "围绕住院病例信息、DRG规则匹配、多Agent协作与文档生成展开。",
            "输出需求分析、架构设计、测试用例和提交记录。",
            "高",
            "完整提交包",
        )
        cursor.execute(
            """
            INSERT INTO analyses (project_id, summary_json, modules_json, risks_json, recommendations_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                dumps(analysis_payload["summary"]),
                dumps(analysis_payload["modules"]),
                dumps(analysis_payload["risks"]),
                dumps(analysis_payload["recommendations"]),
                created_at,
            ),
        )

        drg_cases = [
            build_case_record(
                "CASE-001",
                "张某某",
                "患者主诊断为 A01.002+G01，次诊断 J96.0，主要手术 38.1000X002。",
                "A01.002+G01",
                "伤寒性脑膜炎",
                ["J96.0"],
                "38.1000X002",
                "动脉内膜剥脱术",
                created_at,
            ),
            build_case_record(
                "CASE-002",
                "李某某",
                "患者主诊断 J18.9，次诊断 E87.1，无主手术编码，按内科治疗流程入组。",
                "J18.9",
                "肺部感染",
                ["E87.1"],
                "",
                "内科治疗",
                created_at,
            ),
            build_case_record(
                "CASE-003",
                "赵某某",
                "患者主诊断 E11.621，主要手术 86.2200，暂无有效并发症编码。",
                "E11.621",
                "糖尿病足感染",
                [],
                "86.2200",
                "清创术",
                created_at,
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO drg_cases (
                project_id,
                case_code,
                patient_name,
                diagnosis,
                drg_code,
                status,
                risk_level,
                note,
                created_at,
                record_text,
                primary_diagnosis_code,
                primary_diagnosis_name,
                secondary_diagnosis_codes_json,
                procedure_code,
                procedure_name,
                mdc_code,
                mdc_name,
                adrg_code,
                adrg_name,
                drg_name,
                complication_level,
                group_reason,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    project_id,
                    item["case_code"],
                    item["patient_name"],
                    item["diagnosis"],
                    item["drg_code"],
                    item["status"],
                    item["risk_level"],
                    item["note"],
                    item["created_at"],
                    item["record_text"],
                    item["primary_diagnosis_code"],
                    item["primary_diagnosis_name"],
                    item["secondary_diagnosis_codes_json"],
                    item["procedure_code"],
                    item["procedure_name"],
                    item["mdc_code"],
                    item["mdc_name"],
                    item["adrg_code"],
                    item["adrg_name"],
                    item["drg_name"],
                    item["complication_level"],
                    item["group_reason"],
                    item["updated_at"],
                )
                for item in drg_cases
            ],
        )

        generated_agents = build_agents_payload(project_name, analysis_payload, drg_cases, False)
        agent_rows = [
            (project_id, item["name"], item["owner"], item["status"], item["focus"], created_at)
            for item in generated_agents
        ]
        cursor.executemany(
            "INSERT INTO agents (project_id, name, owner, status, focus, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            agent_rows,
        )

        generated_messages = build_messages_payload(project_name, analysis_payload, drg_cases)
        message_rows = [
            (project_id, item["sender"], item["receiver"], item["content"], item["source"], item["created_at"])
            for item in generated_messages
        ]
        cursor.executemany(
            "INSERT INTO messages (project_id, sender, receiver, content, source, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            message_rows,
        )

        generated_documents = build_documents_payload(project_name, analysis_payload, drg_cases)
        document_rows = [
            (
                project_id,
                item["title"],
                item["status"],
                item["version"],
                item["content"],
                item["updated_at"],
                item["source_agent"],
                item["storage_path"],
                item["received_at"],
            )
            for item in generated_documents
        ]
        cursor.executemany(
            "INSERT INTO documents (project_id, title, status, version, content, updated_at, source_agent, storage_path, received_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            document_rows,
        )

        generated_test_cases = build_test_cases_payload(project_name, drg_cases)
        test_rows = [
            (
                project_id,
                item["case_code"],
                item["feature"],
                item["precondition_text"],
                item["steps_text"],
                item["expected_text"],
                item["priority"],
                item["case_category"],
                item["updated_at"],
            )
            for item in generated_test_cases
        ]
        cursor.executemany(
            """
            INSERT INTO test_cases (project_id, case_code, feature, precondition_text, steps_text, expected_text, priority, case_category, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            test_rows,
        )

        submission_batch_name = "实验二初始提交批次"
        submission_artifact_path = write_submission_artifact(submission_batch_name, "王医生", generated_documents[:2], created_at)
        cursor.execute(
            "INSERT INTO submissions (project_id, batch_name, status, docs_count, operator_name, submitted_at, artifact_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project_id, submission_batch_name, "待审核", 2, "王医生", created_at, submission_artifact_path),
        )
        cursor.execute(
            "INSERT INTO mobile_reports (project_id, title, content, priority, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, "新增病例录入需求", "移动端需要支持病例摘要快速上报，并同步到PC端工作台。", "高", "王医生", created_at),
        )

    connection.commit()
    connection.close()


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    return get_db().execute(query, params).fetchone()


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    return get_db().execute(query, params).fetchall()


def get_project() -> sqlite3.Row:
    project = fetch_one("SELECT * FROM projects ORDER BY id LIMIT 1")
    if project is None:
        raise RuntimeError("Project seed data not found.")
    return project


def get_analysis(project_id: int) -> dict[str, Any]:
    row = fetch_one("SELECT * FROM analyses WHERE project_id = ?", (project_id,))
    if row is None:
        return {"summary": [], "modules": [], "risks": [], "recommendations": [], "updated_at": now_str()}
    return {
        "summary": loads(row["summary_json"]),
        "modules": loads(row["modules_json"]),
        "risks": loads(row["risks_json"]),
        "recommendations": loads(row["recommendations_json"]),
        "updated_at": row["updated_at"],
    }


def get_documents(project_id: int) -> list[dict[str, Any]]:
    rows = fetch_all("SELECT * FROM documents WHERE project_id = ? ORDER BY id", (project_id,))
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "status": row["status"],
            "version": row["version"],
            "content": row["content"],
            "content_lines": row["content"].split("\n"),
            "updated_at": row["updated_at"],
            "source_agent": row["source_agent"],
            "storage_path": row["storage_path"],
            "received_at": row["received_at"],
        }
        for row in rows
    ]


def get_drg_cases(project_id: int) -> list[dict[str, Any]]:
    rows = fetch_all("SELECT * FROM drg_cases WHERE project_id = ? ORDER BY id", (project_id,))
    return [
        {
            "id": row["id"],
            "case_code": row["case_code"],
            "patient_name": row["patient_name"],
            "diagnosis": row["diagnosis"],
            "drg_code": row["drg_code"],
            "drg_name": row["drg_name"],
            "status": row["status"],
            "risk_level": row["risk_level"],
            "note": row["note"],
            "record_text": row["record_text"],
            "primary_diagnosis_code": row["primary_diagnosis_code"],
            "primary_diagnosis_name": row["primary_diagnosis_name"],
            "secondary_diagnosis_codes": loads(row["secondary_diagnosis_codes_json"]),
            "procedure_code": row["procedure_code"],
            "procedure_name": row["procedure_name"],
            "mdc_code": row["mdc_code"],
            "mdc_name": row["mdc_name"],
            "adrg_code": row["adrg_code"],
            "adrg_name": row["adrg_name"],
            "complication_level": row["complication_level"],
            "group_reason": row["group_reason"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def get_agents(project_id: int) -> list[sqlite3.Row]:
    return fetch_all("SELECT * FROM agents WHERE project_id = ? ORDER BY id", (project_id,))


def get_messages(project_id: int) -> list[sqlite3.Row]:
    return fetch_all("SELECT * FROM messages WHERE project_id = ? ORDER BY id DESC", (project_id,))


def get_test_cases(project_id: int) -> list[sqlite3.Row]:
    return fetch_all("SELECT * FROM test_cases WHERE project_id = ? ORDER BY id", (project_id,))


def get_submissions(project_id: int) -> list[sqlite3.Row]:
    return fetch_all("SELECT * FROM submissions WHERE project_id = ? ORDER BY id DESC", (project_id,))


def get_mobile_reports(project_id: int) -> list[sqlite3.Row]:
    return fetch_all("SELECT * FROM mobile_reports WHERE project_id = ? ORDER BY id DESC", (project_id,))


def get_stats(project_id: int) -> dict[str, int]:
    pending_agents = fetch_one(
        "SELECT COUNT(*) AS count FROM agents WHERE project_id = ? AND status != ?",
        (project_id, "已完成"),
    )["count"]
    document_count = fetch_one("SELECT COUNT(*) AS count FROM documents WHERE project_id = ?", (project_id,))["count"]
    submission_count = fetch_one("SELECT COUNT(*) AS count FROM submissions WHERE project_id = ?", (project_id,))["count"]
    report_count = fetch_one("SELECT COUNT(*) AS count FROM mobile_reports WHERE project_id = ?", (project_id,))["count"]
    return {
        "pending_agents": pending_agents,
        "documents": document_count,
        "submissions": submission_count,
        "mobile_reports": report_count,
    }


def get_mdc_catalog() -> list[dict[str, str]]:
    return [{"mdc_code": rule["mdc_code"], "mdc_name": rule["mdc_name"]} for rule in SIMPLIFIED_MDC_RULES]


def filter_drg_cases(cases: list[dict[str, Any]], mdc_code: str, keyword: str) -> list[dict[str, Any]]:
    filtered = cases
    if mdc_code:
        filtered = [item for item in filtered if item["mdc_code"] == mdc_code]
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


def replace_agents(project_id: int, payload: list[dict[str, str]]) -> None:
    database = get_db()
    database.execute("DELETE FROM agents WHERE project_id = ?", (project_id,))
    database.executemany(
        "INSERT INTO agents (project_id, name, owner, status, focus, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        [(project_id, item["name"], item["owner"], item["status"], item["focus"], now_str()) for item in payload],
    )


def replace_messages(project_id: int, payload: list[dict[str, str]]) -> None:
    database = get_db()
    database.execute("DELETE FROM messages WHERE project_id = ? AND source = ?", (project_id, "desktop"))
    database.executemany(
        "INSERT INTO messages (project_id, sender, receiver, content, source, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (project_id, item["sender"], item["receiver"], item["content"], item["source"], item["created_at"])
            for item in payload
        ],
    )


def replace_documents(project_id: int, payload: list[dict[str, str]]) -> None:
    database = get_db()
    database.execute("DELETE FROM documents WHERE project_id = ?", (project_id,))
    database.executemany(
        "INSERT INTO documents (project_id, title, status, version, content, updated_at, source_agent, storage_path, received_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                project_id,
                item["title"],
                item["status"],
                item["version"],
                item["content"],
                item["updated_at"],
                item["source_agent"],
                item["storage_path"],
                item["received_at"],
            )
            for item in payload
        ],
    )


def replace_test_cases(project_id: int, payload: list[dict[str, str]]) -> None:
    database = get_db()
    database.execute("DELETE FROM test_cases WHERE project_id = ?", (project_id,))
    database.executemany(
        """
        INSERT INTO test_cases (project_id, case_code, feature, precondition_text, steps_text, expected_text, priority, case_category, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                project_id,
                item["case_code"],
                item["feature"],
                item["precondition_text"],
                item["steps_text"],
                item["expected_text"],
                item["priority"],
                item["case_category"],
                item["updated_at"],
            )
            for item in payload
        ],
    )


def sync_generated_content(project_id: int, project_name: str, analysis_payload: dict[str, list[str]]) -> None:
    drg_cases = get_drg_cases(project_id)
    submissions = get_submissions(project_id)
    replace_agents(project_id, build_agents_payload(project_name, analysis_payload, drg_cases, bool(submissions)))
    replace_messages(project_id, build_messages_payload(project_name, analysis_payload, drg_cases))
    replace_documents(project_id, build_documents_payload(project_name, analysis_payload, drg_cases))
    replace_test_cases(project_id, build_test_cases_payload(project_name, drg_cases))


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


def role_required(*allowed_roles: str):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                return redirect(url_for("login"))
            if g.user["role"] not in allowed_roles:
                flash("当前账号没有执行该操作的权限。", "warning")
                return redirect(request.referrer or url_for("dashboard"))
            return view(**kwargs)

        return wrapped_view

    return decorator


@app.before_request
def load_logged_in_user() -> None:
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
        return
    user = fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    if user is None:
        session.clear()
    g.user = user


@app.context_processor
def inject_globals() -> dict[str, Any]:
    user = g.get("user")
    return {
        "current_user": user,
        "can_manage_cases": bool(user is not None and user["role"] == "管理员"),
    }


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(BASE_DIR / "static", "favicon.ico", mimetype="image/vnd.microsoft.icon")


@app.route("/")
def index():
    project = get_project()
    stats = get_stats(project["id"])
    return render_template(
        "index.html",
        project=project,
        doc_count=stats["documents"],
        submission_count=stats["submissions"],
        report_count=stats["mobile_reports"],
        case_count=len(get_drg_cases(project["id"])),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("dashboard"))

    form_data = {"username": "admin"}
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        form_data["username"] = username
        if not username or not password:
            flash("请先输入用户名和密码。", "warning")
        else:
            user = fetch_one("SELECT * FROM users WHERE username = ?", (username,))
            if user is None or not check_password_hash(user["password_hash"], password):
                flash("用户名或密码错误。演示账号：admin / 123456", "error")
            else:
                session.clear()
                session["user_id"] = user["id"]
                flash("登录成功，欢迎进入完整项目。", "success")
                return redirect(url_for("dashboard"))

    return render_template("login.html", form_data=form_data)


@app.route("/register", methods=["GET", "POST"])
def register():
    form_data = {"username": "", "role": "分析员"}
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = normalize_choice(request.form.get("role", "分析员"), VALID_ROLES, "分析员")
        form_data = {"username": username, "role": role}
        validation_error = validate_username(username)
        if validation_error is None:
            validation_error = validate_password(password)
        if validation_error is None and password != confirm_password:
            validation_error = "两次输入的密码不一致。"
        if validation_error is not None:
            flash(validation_error, "warning")
        elif fetch_one("SELECT id FROM users WHERE username = ?", (username,)) is not None:
            flash("该用户名已存在。", "error")
        else:
            database = get_db()
            database.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (username, generate_password_hash(password), role, now_str()),
            )
            database.commit()
            flash("注册成功，请使用新账号登录。", "success")
            return redirect(url_for("login"))

    return render_template("register.html", form_data=form_data)


@app.route("/logout")
def logout():
    session.clear()
    flash("你已退出登录。", "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    project = get_project()
    stats = get_stats(project["id"])
    messages = get_messages(project["id"])
    submissions = get_submissions(project["id"])
    documents = get_documents(project["id"])
    drg_cases = get_drg_cases(project["id"])
    distributions = get_case_distributions(drg_cases)
    timeline = [
        f"当前项目阶段：{project['phase']}",
        f"最近文档版本：{documents[0]['version']}" if documents else "暂无文档",
        f"最近提交状态：{submissions[0]['status']}" if submissions else "暂无提交记录",
        f"最新消息来源：{messages[0]['sender']}" if messages else "暂无消息",
    ]
    return render_template(
        "dashboard.html",
        page_key="dashboard",
        project=project,
        stats=stats,
        timeline=timeline,
        recent_messages=messages[:4],
        case_count=len(drg_cases),
        distributions=distributions,
    )


@app.route("/analysis", methods=["GET", "POST"])
@login_required
def analysis():
    project = get_project()
    form_data = {
        "project_name": project["name"],
        "description": project["description"],
        "target": project["target"],
        "priority": project["priority"],
        "doc_type": "完整提交包",
    }
    if request.method == "POST":
        project_name = request.form.get("project_name", project["name"]).strip() or project["name"]
        description = request.form.get("description", project["description"]).strip() or project["description"]
        target = request.form.get("target", project["target"]).strip() or project["target"]
        priority = normalize_choice(request.form.get("priority", project["priority"]), VALID_PRIORITIES, project["priority"])
        doc_type = normalize_choice(request.form.get("doc_type", "完整提交包"), VALID_DOC_TYPES, "完整提交包")
        form_data = {
            "project_name": project_name,
            "description": description,
            "target": target,
            "priority": priority,
            "doc_type": doc_type,
        }
        validation_error = validate_required_text("项目名称", project_name, MAX_PROJECT_NAME_LENGTH)
        if validation_error is None:
            validation_error = validate_required_text("业务描述", description, MAX_DESCRIPTION_LENGTH)
        if validation_error is None:
            validation_error = validate_required_text("目标产物", target, MAX_TARGET_LENGTH)
        if validation_error is not None:
            flash(validation_error, "warning")
        else:
            analysis_payload = build_analysis_payload(project_name, description, target, priority, doc_type)
            database = get_db()
            database.execute(
                """
                UPDATE projects
                SET name = ?, owner_name = ?, priority = ?, phase = ?, target = ?, description = ?, updated_at = ?
                WHERE id = ?
                """,
                (project_name, g.user["username"], priority, "文档生成中", target, description, now_str(), project["id"]),
            )
            existing = fetch_one("SELECT id FROM analyses WHERE project_id = ?", (project["id"],))
            if existing is None:
                database.execute(
                    """
                    INSERT INTO analyses (project_id, summary_json, modules_json, risks_json, recommendations_json, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project["id"],
                        dumps(analysis_payload["summary"]),
                        dumps(analysis_payload["modules"]),
                        dumps(analysis_payload["risks"]),
                        dumps(analysis_payload["recommendations"]),
                        now_str(),
                    ),
                )
            else:
                database.execute(
                    """
                    UPDATE analyses
                    SET summary_json = ?, modules_json = ?, risks_json = ?, recommendations_json = ?, updated_at = ?
                    WHERE project_id = ?
                    """,
                    (
                        dumps(analysis_payload["summary"]),
                        dumps(analysis_payload["modules"]),
                        dumps(analysis_payload["risks"]),
                        dumps(analysis_payload["recommendations"]),
                        now_str(),
                        project["id"],
                    ),
                )
            sync_generated_content(project["id"], project_name, analysis_payload)
            database.commit()
            flash("需求分析已完成，文档、Agent 和测试用例已同步刷新。", "success")
            return redirect(url_for("analysis"))

    project = get_project()
    return render_template(
        "analysis.html",
        page_key="analysis",
        project=project,
        analysis=get_analysis(project["id"]),
        form_data=form_data,
    )


@app.route("/cases", methods=["GET", "POST"])
@login_required
def cases_page():
    project = get_project()
    form_data = {
        "patient_name": "",
        "record_text": "",
        "primary_diagnosis_code": "",
        "primary_diagnosis_name": "",
        "secondary_diagnosis_codes": "",
        "procedure_code": "",
        "procedure_name": "",
    }
    if request.method == "POST":
        patient_name = request.form.get("patient_name", "").strip()
        record_text = request.form.get("record_text", "").strip()
        primary_diagnosis_code = normalize_medical_code(request.form.get("primary_diagnosis_code", ""))
        primary_diagnosis_name = request.form.get("primary_diagnosis_name", "").strip()
        secondary_diagnosis_raw = request.form.get("secondary_diagnosis_codes", "").strip()
        procedure_code = normalize_medical_code(request.form.get("procedure_code", ""))
        procedure_name = request.form.get("procedure_name", "").strip()
        form_data = {
            "patient_name": patient_name,
            "record_text": record_text,
            "primary_diagnosis_code": primary_diagnosis_code,
            "primary_diagnosis_name": primary_diagnosis_name,
            "secondary_diagnosis_codes": secondary_diagnosis_raw,
            "procedure_code": procedure_code,
            "procedure_name": procedure_name,
        }
        validation_error = validate_required_text("患者姓名", patient_name, MAX_PATIENT_NAME_LENGTH)
        if validation_error is None:
            validation_error = validate_required_text("电子病历摘要", record_text, MAX_RECORD_TEXT_LENGTH)
        if validation_error is None:
            validation_error = validate_required_text("主诊断编码", primary_diagnosis_code, MAX_MEDICAL_CODE_LENGTH)
        if validation_error is None:
            validation_error = validate_required_text("主诊断名称", primary_diagnosis_name, MAX_MEDICAL_NAME_LENGTH)
        if validation_error is None:
            validation_error = validate_required_text("主手术编码", procedure_code, MAX_MEDICAL_CODE_LENGTH)
        if validation_error is None:
            validation_error = validate_required_text("主手术名称", procedure_name, MAX_MEDICAL_NAME_LENGTH)
        if validation_error is not None:
            flash(validation_error, "warning")
        else:
            secondary_codes = parse_code_list(secondary_diagnosis_raw)
            next_case_number = fetch_one("SELECT COUNT(*) AS count FROM drg_cases WHERE project_id = ?", (project["id"],))["count"] + 1
            case_record = build_case_record(
                f"CASE-{next_case_number:03d}",
                patient_name,
                record_text,
                primary_diagnosis_code,
                primary_diagnosis_name,
                secondary_codes,
                procedure_code,
                procedure_name,
            )
            database = get_db()
            database.execute(
                """
                INSERT INTO drg_cases (
                    project_id, case_code, patient_name, diagnosis, drg_code, status, risk_level, note, created_at,
                    record_text, primary_diagnosis_code, primary_diagnosis_name, secondary_diagnosis_codes_json,
                    procedure_code, procedure_name, mdc_code, mdc_name, adrg_code, adrg_name, drg_name,
                    complication_level, group_reason, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project["id"],
                    case_record["case_code"],
                    case_record["patient_name"],
                    case_record["diagnosis"],
                    case_record["drg_code"],
                    case_record["status"],
                    case_record["risk_level"],
                    case_record["note"],
                    case_record["created_at"],
                    case_record["record_text"],
                    case_record["primary_diagnosis_code"],
                    case_record["primary_diagnosis_name"],
                    case_record["secondary_diagnosis_codes_json"],
                    case_record["procedure_code"],
                    case_record["procedure_name"],
                    case_record["mdc_code"],
                    case_record["mdc_name"],
                    case_record["adrg_code"],
                    case_record["adrg_name"],
                    case_record["drg_name"],
                    case_record["complication_level"],
                    case_record["group_reason"],
                    case_record["updated_at"],
                ),
            )
            database.execute(
                "UPDATE projects SET phase = ?, updated_at = ? WHERE id = ?",
                ("DRG入组已更新", now_str(), project["id"]),
            )
            sync_generated_content(project["id"], project["name"], get_analysis(project["id"]))
            database.commit()
            flash(f"病例 {case_record['case_code']} 已完成本地教学规则入组。", "success")
            return redirect(url_for("cases_page"))

    drg_cases = get_drg_cases(project["id"])
    mdc_filter = request.args.get("mdc", "").strip().upper()
    keyword = request.args.get("q", "").strip()
    mdc_catalog = get_mdc_catalog()
    valid_mdc_codes = {entry["mdc_code"] for entry in mdc_catalog}
    applied_mdc = mdc_filter if mdc_filter in valid_mdc_codes else ""
    filtered_cases = filter_drg_cases(drg_cases, applied_mdc, keyword)
    has_active_filters = bool(applied_mdc or keyword)
    latest_case_source = filtered_cases if has_active_filters else drg_cases
    return render_template(
        "cases.html",
        page_key="cases",
        project=project,
        drg_cases=filtered_cases,
        all_case_count=len(drg_cases),
        latest_case=get_latest_case(latest_case_source),
        form_data=form_data,
        mdc_catalog=mdc_catalog,
        filter_data={"mdc": applied_mdc, "q": keyword, "active": has_active_filters},
    )


@app.route("/cases/<int:case_id>/delete", methods=["POST"])
@role_required("管理员")
def delete_case(case_id: int):
    project = get_project()
    case_row = fetch_one(
        "SELECT case_code FROM drg_cases WHERE id = ? AND project_id = ?",
        (case_id, project["id"]),
    )
    if case_row is None:
        flash("未找到对应病例，可能已被删除。", "warning")
        return redirect(url_for("cases_page"))
    database = get_db()
    database.execute("DELETE FROM drg_cases WHERE id = ? AND project_id = ?", (case_id, project["id"]))
    database.execute(
        "INSERT INTO messages (project_id, sender, receiver, content, source, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (
            project["id"],
            "DRG 分析 Agent",
            "需求分析 Agent",
            f"管理员 {g.user['username']} 已撤销病例 {case_row['case_code']}，请刷新下游数据。",
            "desktop",
            now_str(),
        ),
    )
    database.execute(
        "UPDATE projects SET phase = ?, updated_at = ? WHERE id = ?",
        ("DRG入组已更新", now_str(), project["id"]),
    )
    sync_generated_content(project["id"], project["name"], get_analysis(project["id"]))
    database.commit()
    flash(f"病例 {case_row['case_code']} 已成功删除。", "success")
    return redirect(url_for("cases_page"))


@app.route("/agents")
@login_required
def agents_page():
    project = get_project()
    return render_template(
        "agents.html",
        page_key="agents",
        project=project,
        agents=get_agents(project["id"]),
        messages=get_messages(project["id"]),
    )


@app.route("/documents/<int:document_id>/download")
@login_required
def download_document(document_id: int):
    project = get_project()
    document = fetch_one(
        "SELECT title, version, storage_path FROM documents WHERE id = ? AND project_id = ?",
        (document_id, project["id"]),
    )
    if document is None or not document["storage_path"]:
        abort(404)
    storage_path = Path(document["storage_path"])
    if not storage_path.is_absolute():
        storage_path = BASE_DIR / storage_path
    try:
        storage_path.resolve().relative_to(VIRTUAL_DOCS_DIR.resolve())
    except ValueError:
        abort(404)
    if not storage_path.is_file():
        abort(404)
    download_name = f"{sanitize_filename(document['title'])}_{sanitize_filename(document['version'])}.txt"
    return send_from_directory(
        VIRTUAL_DOCS_DIR,
        storage_path.name,
        as_attachment=True,
        download_name=download_name,
    )


@app.route("/documents")
@login_required
def documents_page():
    project = get_project()
    documents = get_documents(project["id"])
    selected_id = request.args.get("document_id", type=int)
    selected_document = None
    if documents:
        selected_document = next((item for item in documents if item["id"] == selected_id), documents[0])
    return render_template(
        "documents.html",
        page_key="documents",
        project=project,
        documents=documents,
        selected_document=selected_document,
    )


@app.route("/tests", methods=["GET", "POST"])
@login_required
def tests_page():
    project = get_project()
    if request.method == "POST":
        payload = build_test_cases_payload(project["name"], get_drg_cases(project["id"]))
        replace_test_cases(project["id"], payload)
        get_db().commit()
        flash("测试用例已按当前项目上下文重新生成。", "success")
        return redirect(url_for("tests_page"))

    return render_template(
        "tests.html",
        page_key="tests",
        project=project,
        test_cases=get_test_cases(project["id"]),
    )


@app.route("/submit", methods=["GET", "POST"])
@login_required
def submit_page():
    project = get_project()
    documents = get_documents(project["id"])
    if request.method == "POST":
        if not documents:
            flash("当前没有可提交文档，请先完成需求分析。", "warning")
            return redirect(url_for("submit_page"))
        selected_ids = [int(item) for item in request.form.getlist("document_ids") if item.isdigit()]
        if not selected_ids:
            flash("请至少选择一份文档后再提交。", "warning")
            return redirect(url_for("submit_page"))
        selected_id_set = set(selected_ids)
        valid_selected_ids = [item["id"] for item in documents if item["id"] in selected_id_set]
        if not valid_selected_ids:
            flash("请选择当前项目中的有效文档后再提交。", "warning")
            return redirect(url_for("submit_page"))
        selected_documents = [item for item in documents if item["id"] in selected_id_set]
        submitted_at = now_str()
        batch_name = f"{project['name']} 提交批次 {datetime.now().strftime('%m%d-%H%M')}"
        artifact_path = write_submission_artifact(batch_name, g.user["username"], selected_documents, submitted_at)
        database = get_db()
        placeholders = ",".join("?" for _ in valid_selected_ids)
        database.execute(
            f"UPDATE documents SET status = ?, updated_at = ? WHERE id IN ({placeholders})",
            tuple(["已提交", submitted_at, *valid_selected_ids]),
        )
        database.execute(
            "UPDATE projects SET phase = ?, updated_at = ? WHERE id = ?",
            ("已提交待审核", submitted_at, project["id"]),
        )
        database.execute(
            "INSERT INTO submissions (project_id, batch_name, status, docs_count, operator_name, submitted_at, artifact_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                project["id"],
                batch_name,
                "已提交",
                len(valid_selected_ids),
                g.user["username"],
                submitted_at,
                artifact_path,
            ),
        )
        analysis_payload = get_analysis(project["id"])
        drg_cases = get_drg_cases(project["id"])
        replace_agents(project["id"], build_agents_payload(project["name"], analysis_payload, drg_cases, True))
        replace_messages(project["id"], build_messages_payload(project["name"], analysis_payload, drg_cases))
        database.execute(
            "INSERT INTO messages (project_id, sender, receiver, content, source, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (project["id"], "提交 Agent", "虚拟文档系统", f"批次 {batch_name} 已提交，提交清单已写入 {artifact_path}。", "desktop", submitted_at),
        )
        database.commit()
        flash("提交成功，已生成新的提交记录。", "success")
        return redirect(url_for("submit_page"))

    return render_template(
        "submit.html",
        page_key="submit",
        project=project,
        documents=documents,
        submissions=get_submissions(project["id"]),
    )


@app.route("/mobile/home")
@login_required
def mobile_home():
    project = get_project()
    stats = get_stats(project["id"])
    documents = get_documents(project["id"])
    submissions = get_submissions(project["id"])
    messages = get_messages(project["id"])
    drg_cases = get_drg_cases(project["id"])
    latest_case = get_latest_case(drg_cases)
    tasks = [
        f"最新DRG结果：{latest_case['drg_code']}" if latest_case else "暂无DRG入组结果",
        f"查看最新文档版本：{documents[0]['version']}" if documents else "暂无文档",
        f"当前处理阶段：{project['phase']}",
        f"最近消息来源：{messages[0]['sender']}" if messages else "暂无消息",
        f"最近提交状态：{submissions[0]['status']}" if submissions else "暂无提交",
    ]
    return render_template(
        "mobile_home.html",
        page_key="mobile_home",
        project=project,
        stats=stats,
        tasks=tasks,
    )


@app.route("/mobile/report", methods=["GET", "POST"])
@login_required
def mobile_report():
    project = get_project()
    form_data = {"title": "", "content": "", "priority": "中"}
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        priority = normalize_choice(request.form.get("priority", "中"), VALID_PRIORITIES, "中")
        form_data = {"title": title, "content": content, "priority": priority}
        validation_error = validate_required_text("上报标题", title, MAX_REPORT_TITLE_LENGTH)
        if validation_error is None:
            validation_error = validate_required_text("上报内容", content, MAX_REPORT_CONTENT_LENGTH)
        if validation_error is not None:
            flash(validation_error, "warning")
        else:
            database = get_db()
            database.execute(
                "INSERT INTO mobile_reports (project_id, title, content, priority, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (project["id"], title, content, priority, g.user["username"], now_str()),
            )
            database.execute(
                "INSERT INTO messages (project_id, sender, receiver, content, source, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (project["id"], "移动端上报", "需求分析 Agent", f"{title}：{content}", "mobile", now_str()),
            )
            database.execute(
                "UPDATE projects SET phase = ?, updated_at = ? WHERE id = ?",
                ("收到移动端上报", now_str(), project["id"]),
            )
            database.commit()
            flash("上报成功，PC端消息流已同步新增记录。", "success")
            return redirect(url_for("mobile_messages"))

    return render_template("mobile_report.html", page_key="mobile_report", project=project, form_data=form_data)


@app.route("/mobile/messages")
@login_required
def mobile_messages():
    project = get_project()
    return render_template(
        "mobile_messages.html",
        page_key="mobile_messages",
        project=project,
        messages=get_messages(project["id"]),
    )


@app.route("/mobile/documents")
@login_required
def mobile_documents():
    project = get_project()
    return render_template(
        "mobile_documents.html",
        page_key="mobile_documents",
        project=project,
        documents=get_documents(project["id"]),
        submissions=get_submissions(project["id"]),
        reports=get_mobile_reports(project["id"]),
    )


with app.app_context():
    init_database()
    seed_demo_data()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
