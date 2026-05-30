from __future__ import annotations

import sqlite3
from typing import Any

from flask import current_app, g
from werkzeug.security import generate_password_hash

from common import get_current_generation_mode, loads, now_str
from drg_rules import build_case_record
from template_generation import generate_test_cases
from platform_config import INSTANCE_DIR, SUBMISSION_ARTIFACTS_DIR, VIRTUAL_DOCS_DIR
from storage import write_submission_artifact, write_virtual_document

def get_db() -> sqlite3.Connection:
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        g.db = connection
    return g.db


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
    connection.execute("DROP TABLE IF EXISTS analyses")
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

def init_database() -> None:
    ensure_storage_directories()
    connection = sqlite3.connect(current_app.config["DATABASE"])
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


def get_latest_case(drg_cases: list[Any]) -> Any | None:
    return drg_cases[-1] if drg_cases else None


def build_agents_payload(
    project_name: str,
    drg_cases: list[Any],
    has_submissions: bool,
) -> list[dict[str, str]]:
    latest_case = get_latest_case(drg_cases)
    latest_case_label = latest_case["case_code"] if latest_case else "暂无病例"
    return [
        {"name": "需求分析 Agent", "owner": "产品侧", "status": "已完成", "focus": f"完成 {project_name} 的LLM文档生成"},
        {"name": "DRG 分析 Agent", "owner": "业务侧", "status": "已完成" if latest_case else "待处理", "focus": f"最近处理病例：{latest_case_label}"},
        {"name": "文档生成 Agent", "owner": "交付侧", "status": "已完成", "focus": "生成需求分析、架构设计与测试文档"},
        {"name": "测试用例 Agent", "owner": "测试侧", "status": "已完成" if latest_case else "运行中", "focus": "输出正常、边界、异常三类测试用例"},
        {"name": "提交 Agent", "owner": "管理侧", "status": "已完成" if has_submissions else "待处理", "focus": "接收虚拟文档系统文档并生成提交批次"},
    ]


def build_messages_payload(project_name: str, drg_cases: list[Any]) -> list[dict[str, str]]:
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
            "content": f"已完成 {project_name} 的LLM文档生成请求。",
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


def build_documents_payload(
    project_name: str,
    drg_cases: list[Any],
    document_contents: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    timestamp = now_str()
    del drg_cases
    if document_contents is None:
        return []
    generated_contents = document_contents
    payload = [
        {
            "title": "需求分析文档",
            "status": "未保存",
            "version": "V2.0",
            "updated_at": timestamp,
            "source_agent": "需求分析 Agent",
            "content": generated_contents["需求分析文档"],
            "storage_path": "",
        },
        {
            "title": "架构设计文档",
            "status": "未保存",
            "version": "V2.0",
            "updated_at": timestamp,
            "source_agent": "文档生成 Agent",
            "content": generated_contents["架构设计文档"],
            "storage_path": "",
        },
        {
            "title": "测试文档",
            "status": "未保存",
            "version": "V2.0",
            "updated_at": timestamp,
            "source_agent": "测试用例 Agent",
            "content": generated_contents["测试文档"],
            "storage_path": "",
        },
    ]
    for item in payload:
        item["received_at"] = item["updated_at"]
    return payload


def save_document_payload(project_id: int, project_name: str, document: dict[str, str]) -> int:
    saved_at = now_str()
    storage_path = write_virtual_document(project_name, document["title"], document["version"], document["content"], saved_at)
    database = get_db()
    cursor = database.execute(
        """
        INSERT INTO documents (project_id, title, status, version, content, updated_at, source_agent, storage_path, received_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            document["title"],
            "已保存",
            document["version"],
            document["content"],
            saved_at,
            document["source_agent"],
            storage_path,
            document.get("received_at") or saved_at,
        ),
    )
    return int(cursor.lastrowid)


def build_test_cases_payload(project_name: str, drg_cases: list[Any], test_cases: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    timestamp = now_str()
    generated_cases = test_cases or generate_test_cases(project_name, drg_cases, mode=get_current_generation_mode())
    return [{**item, "updated_at": timestamp} for item in generated_cases]


def seed_demo_data() -> None:
    connection = sqlite3.connect(current_app.config["DATABASE"])
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

        generated_agents = build_agents_payload(project_name, drg_cases, False)
        agent_rows = [
            (project_id, item["name"], item["owner"], item["status"], item["focus"], created_at)
            for item in generated_agents
        ]
        cursor.executemany(
            "INSERT INTO agents (project_id, name, owner, status, focus, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            agent_rows,
        )

        generated_messages = build_messages_payload(project_name, drg_cases)
        message_rows = [
            (project_id, item["sender"], item["receiver"], item["content"], item["source"], item["created_at"])
            for item in generated_messages
        ]
        cursor.executemany(
            "INSERT INTO messages (project_id, sender, receiver, content, source, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            message_rows,
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
        cursor.execute(
            "INSERT INTO mobile_reports (project_id, title, content, priority, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, "新增病例录入需求", "移动端需要支持病例摘要快速上报，并同步到PC端工作台。", "高", "王医生", created_at),
        )

    project_row = cursor.execute("SELECT id, name FROM projects ORDER BY id LIMIT 1").fetchone()
    if project_row is not None:
        old_test_case = cursor.execute(
            "SELECT id FROM test_cases WHERE project_id = ? AND case_code = ?",
            (project_row["id"], "TC-201"),
        ).fetchone()
        if old_test_case is not None:
            cursor.execute("DELETE FROM test_cases WHERE project_id = ?", (project_row["id"],))
            generated_test_cases = build_test_cases_payload(project_row["name"], [])
            cursor.executemany(
                """
                INSERT INTO test_cases (project_id, case_code, feature, precondition_text, steps_text, expected_text, priority, case_category, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        project_row["id"],
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
                ],
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


def get_documents(project_id: int) -> list[dict[str, Any]]:
    rows = fetch_all("SELECT * FROM documents WHERE project_id = ? ORDER BY id", (project_id,))
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "status": "已保存",
            "version": row["version"],
            "content": row["content"],
            "content_lines": row["content"].split("\n"),
            "updated_at": row["updated_at"],
            "source_agent": row["source_agent"],
            "storage_path": row["storage_path"],
            "received_at": row["received_at"],
            "saved": True,
            "doc_key": f"saved-{row['id']}",
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


def sync_generated_content(
    project_id: int,
    project_name: str,
    document_contents: dict[str, str] | None = None,
    test_cases: list[dict[str, str]] | None = None,
) -> None:
    del document_contents
    drg_cases = get_drg_cases(project_id)
    submissions = get_submissions(project_id)
    replace_agents(project_id, build_agents_payload(project_name, drg_cases, bool(submissions)))
    replace_messages(project_id, build_messages_payload(project_name, drg_cases))
    replace_test_cases(project_id, build_test_cases_payload(project_name, drg_cases, test_cases))
