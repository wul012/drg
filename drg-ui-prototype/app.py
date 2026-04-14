from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

from flask import Flask, flash, g, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
DATABASE_PATH = INSTANCE_DIR / "drg_platform.db"

app = Flask(__name__, instance_path=str(INSTANCE_DIR), instance_relative_config=True)
app.config["SECRET_KEY"] = os.environ.get("DRG_APP_SECRET", "drg-ui-prototype-secret")
app.config["DATABASE"] = str(DATABASE_PATH)


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads(value: str | None) -> list[str]:
    if not value:
        return []
    return json.loads(value)


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


def init_database() -> None:
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
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


def build_agents_payload() -> list[dict[str, str]]:
    return [
        {"name": "需求分析 Agent", "owner": "产品侧", "status": "已完成", "focus": "解析需求输入并提炼关键模块"},
        {"name": "DRG 分析 Agent", "owner": "业务侧", "status": "已完成", "focus": "输出病例与DRG规则匹配结果"},
        {"name": "文档生成 Agent", "owner": "交付侧", "status": "运行中", "focus": "生成需求、架构和测试文档"},
        {"name": "测试用例 Agent", "owner": "测试侧", "status": "待处理", "focus": "整理测试步骤与预期结果"},
        {"name": "提交 Agent", "owner": "管理侧", "status": "待处理", "focus": "打包文档并提交到虚拟系统"},
    ]


def build_messages_payload(project_name: str) -> list[dict[str, str]]:
    timestamp = now_str()
    return [
        {
            "sender": "需求分析 Agent",
            "receiver": "DRG 分析 Agent",
            "content": f"已解析 {project_name} 的需求上下文，请开始进行规则匹配与风险识别。",
            "source": "desktop",
            "created_at": timestamp,
        },
        {
            "sender": "DRG 分析 Agent",
            "receiver": "文档生成 Agent",
            "content": "规则匹配已完成，请基于结果生成需求分析文档和风险说明。",
            "source": "desktop",
            "created_at": timestamp,
        },
        {
            "sender": "文档生成 Agent",
            "receiver": "测试用例 Agent",
            "content": "需求与设计文档已就绪，请同步形成测试覆盖清单。",
            "source": "desktop",
            "created_at": timestamp,
        },
    ]


def build_documents_payload(project_name: str, analysis_payload: dict[str, list[str]]) -> list[dict[str, str]]:
    timestamp = now_str()
    return [
        {
            "title": "需求分析文档",
            "status": "已生成",
            "version": "V1.1",
            "updated_at": timestamp,
            "content": "\n".join(
                [
                    f"一、项目名称：{project_name}",
                    f"二、需求摘要：{'；'.join(analysis_payload['summary'])}",
                    f"三、建议模块：{'、'.join(analysis_payload['modules'])}",
                ]
            ),
        },
        {
            "title": "架构设计文档",
            "status": "待更新",
            "version": "V1.0",
            "updated_at": timestamp,
            "content": "\n".join(
                [
                    "一、系统采用 Flask + SQLite 的前后端一体化方案。",
                    "二、PC端包含工作台、分析、DRG、Agent、文档、测试与提交中心。",
                    "三、移动端包含上报、消息和文档查看，采用响应式布局而非原型手机壳。",
                ]
            ),
        },
        {
            "title": "测试用例文档",
            "status": "已生成",
            "version": "V1.0",
            "updated_at": timestamp,
            "content": "\n".join(
                [
                    f"一、重点覆盖 {project_name} 的主业务链路。",
                    "二、覆盖登录、需求分析、消息联动、文档查看和提交流程。",
                    "三、覆盖移动端上报与结果查看。",
                ]
            ),
        },
    ]


def build_test_cases_payload(project_name: str) -> list[dict[str, str]]:
    timestamp = now_str()
    return [
        {
            "case_code": "TC-101",
            "feature": "需求分析自动生成",
            "precondition_text": "用户已登录并进入需求分析页",
            "steps_text": f"填写 {project_name} 的需求描述并点击开始分析",
            "expected_text": "生成摘要、模块建议与风险识别结果",
            "priority": "高",
            "updated_at": timestamp,
        },
        {
            "case_code": "TC-102",
            "feature": "Agent协作流转",
            "precondition_text": "分析结果已生成",
            "steps_text": "进入 Agent 协作页查看状态和消息流",
            "expected_text": "看到需求分析 -> DRG -> 文档生成的消息链路",
            "priority": "高",
            "updated_at": timestamp,
        },
        {
            "case_code": "TC-103",
            "feature": "文档提交",
            "precondition_text": "文档列表已准备完成",
            "steps_text": "在提交中心勾选文档并点击确认提交",
            "expected_text": "生成新的提交记录并更新项目阶段",
            "priority": "中",
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
        cursor.execute(
            """
            INSERT INTO projects (name, owner_name, priority, phase, target, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "医保DRG智能协同平台",
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
            "医保DRG智能协同平台",
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
            (project_id, "CASE-001", "张某某", "急性阑尾炎", "GB15", "已完成", "低", "主要诊断明确，手术路径清晰。", created_at),
            (project_id, "CASE-002", "李某某", "肺部感染伴并发症", "EB23", "分析中", "中", "需补充合并症编码和住院天数。", created_at),
            (project_id, "CASE-003", "赵某某", "糖尿病足感染", "KT11", "待复核", "高", "治疗路径复杂，建议复核手术与并发症信息。", created_at),
        ]
        cursor.executemany(
            """
            INSERT INTO drg_cases (project_id, case_code, patient_name, diagnosis, drg_code, status, risk_level, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            drg_cases,
        )

        agent_rows = [
            (project_id, item["name"], item["owner"], item["status"], item["focus"], created_at)
            for item in build_agents_payload()
        ]
        cursor.executemany(
            "INSERT INTO agents (project_id, name, owner, status, focus, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            agent_rows,
        )

        message_rows = [
            (project_id, item["sender"], item["receiver"], item["content"], item["source"], item["created_at"])
            for item in build_messages_payload("医保DRG智能协同平台")
        ]
        cursor.executemany(
            "INSERT INTO messages (project_id, sender, receiver, content, source, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            message_rows,
        )

        document_rows = [
            (project_id, item["title"], item["status"], item["version"], item["content"], item["updated_at"])
            for item in build_documents_payload("医保DRG智能协同平台", analysis_payload)
        ]
        cursor.executemany(
            "INSERT INTO documents (project_id, title, status, version, content, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            document_rows,
        )

        test_rows = [
            (project_id, item["case_code"], item["feature"], item["precondition_text"], item["steps_text"], item["expected_text"], item["priority"], item["updated_at"])
            for item in build_test_cases_payload("医保DRG智能协同平台")
        ]
        cursor.executemany(
            """
            INSERT INTO test_cases (project_id, case_code, feature, precondition_text, steps_text, expected_text, priority, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            test_rows,
        )

        cursor.execute(
            "INSERT INTO submissions (project_id, batch_name, status, docs_count, operator_name, submitted_at) VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, "实验二初始提交批次", "待审核", 2, "王医生", created_at),
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
            "content_lines": row["content"].split("\n"),
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def get_drg_cases(project_id: int) -> list[sqlite3.Row]:
    return fetch_all("SELECT * FROM drg_cases WHERE project_id = ? ORDER BY id", (project_id,))


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
        "INSERT INTO documents (project_id, title, status, version, content, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        [(project_id, item["title"], item["status"], item["version"], item["content"], item["updated_at"]) for item in payload],
    )


def replace_test_cases(project_id: int, payload: list[dict[str, str]]) -> None:
    database = get_db()
    database.execute("DELETE FROM test_cases WHERE project_id = ?", (project_id,))
    database.executemany(
        """
        INSERT INTO test_cases (project_id, case_code, feature, precondition_text, steps_text, expected_text, priority, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                item["updated_at"],
            )
            for item in payload
        ],
    )


def sync_generated_content(project_id: int, project_name: str, analysis_payload: dict[str, list[str]]) -> None:
    replace_agents(project_id, build_agents_payload())
    replace_messages(project_id, build_messages_payload(project_name))
    replace_documents(project_id, build_documents_payload(project_name, analysis_payload))
    replace_test_cases(project_id, build_test_cases_payload(project_name))


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


@app.before_request
def load_logged_in_user() -> None:
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
        return
    g.user = fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))


@app.context_processor
def inject_globals() -> dict[str, Any]:
    return {"current_user": g.get("user")}


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

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = fetch_one("SELECT * FROM users WHERE username = ?", (username,))
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("用户名或密码错误。演示账号：admin / 123456", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            flash("登录成功，欢迎进入完整项目。", "success")
            return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "分析员")
        if not username or not password:
            flash("请完整填写用户名和密码。", "warning")
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

    return render_template("register.html")


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
    )


@app.route("/analysis", methods=["GET", "POST"])
@login_required
def analysis():
    project = get_project()
    if request.method == "POST":
        project_name = request.form.get("project_name", project["name"]).strip() or project["name"]
        description = request.form.get("description", project["description"]).strip() or project["description"]
        target = request.form.get("target", project["target"]).strip() or project["target"]
        priority = request.form.get("priority", project["priority"])
        doc_type = request.form.get("doc_type", "完整提交包")
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
    )


@app.route("/cases")
@login_required
def cases_page():
    project = get_project()
    return render_template(
        "cases.html",
        page_key="cases",
        project=project,
        drg_cases=get_drg_cases(project["id"]),
    )


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
        payload = build_test_cases_payload(project["name"])
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
        selected_ids = [int(item) for item in request.form.getlist("document_ids") if item.isdigit()]
        if not selected_ids:
            flash("请至少选择一份文档后再提交。", "warning")
            return redirect(url_for("submit_page"))
        database = get_db()
        placeholders = ",".join("?" for _ in selected_ids)
        database.execute(
            f"UPDATE documents SET status = ?, updated_at = ? WHERE id IN ({placeholders})",
            tuple(["已提交", now_str(), *selected_ids]),
        )
        database.execute(
            "UPDATE projects SET phase = ?, updated_at = ? WHERE id = ?",
            ("已提交待审核", now_str(), project["id"]),
        )
        database.execute(
            "INSERT INTO submissions (project_id, batch_name, status, docs_count, operator_name, submitted_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                project["id"],
                f"{project['name']} 提交批次 {datetime.now().strftime('%m%d-%H%M')}",
                "已提交",
                len(selected_ids),
                g.user["username"],
                now_str(),
            ),
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
    tasks = [
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
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        priority = request.form.get("priority", "中")
        if not title or not content:
            flash("请完整填写上报标题和内容。", "warning")
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

    return render_template("mobile_report.html", page_key="mobile_report", project=project)


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
