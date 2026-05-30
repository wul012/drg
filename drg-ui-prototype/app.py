from __future__ import annotations

import json
import os
from functools import wraps
from pathlib import Path
from typing import Any

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import drg_case_utils as case_utils
from common import get_current_generation_mode, normalize_choice, now_str, validate_password, validate_required_text, validate_username
from data_services import *
from drg_rules import build_case_record, generate_random_groupable_case_input, get_chs_mdc_catalog, resolve_diagnosis_code, resolve_procedure_code
from platform_config import *
from requirement_analysis_generation import RequirementAnalysisGenerator
from storage import sanitize_filename
from template_generation import get_generation_mode_options, get_template_runtime

app = Flask(__name__, instance_path=str(INSTANCE_DIR), instance_relative_config=True)
app.config["SECRET_KEY"] = os.environ.get("DRG_APP_SECRET", "drg-ui-prototype-secret")
app.config["DATABASE"] = str(DATABASE_PATH)
app.teardown_appcontext(close_db)

PENDING_DOCUMENTS: dict[int, list[dict[str, str]]] = {}


def store_pending_documents(project_id: int, documents: list[dict[str, str]]) -> None:
    PENDING_DOCUMENTS[project_id] = [
        {
            **document,
            "id": 0,
            "doc_key": f"pending-{index}",
            "saved": False,
            "content_lines": document["content"].splitlines(),
        }
        for index, document in enumerate(documents)
    ]


def add_pending_document(project_id: int, document: dict[str, str]) -> dict[str, Any]:
    pending_documents = PENDING_DOCUMENTS.setdefault(project_id, [])
    document_key = f"pending-{len(pending_documents)}-{now_str().replace(':', '').replace(' ', '-')}"
    pending_document = {
        **document,
        "id": 0,
        "doc_key": document_key,
        "saved": False,
        "storage_path": "",
        "content_lines": document["content"].splitlines(),
    }
    pending_documents.append(pending_document)
    return pending_document


def get_all_documents(project_id: int) -> list[dict[str, Any]]:
    return [*PENDING_DOCUMENTS.get(project_id, []), *get_documents(project_id)]


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
    active_mode = get_current_generation_mode()
    return {
        "current_user": user,
        "can_manage_cases": bool(user is not None and user["role"] == "管理员"),
        "template_runtime": get_template_runtime(active_mode),
        "generation_mode_options": get_generation_mode_options(),
    }


def parse_json_list(raw_text: str, name_key: str, code_key: str, label: str) -> list[dict[str, str]]:
    if not raw_text.strip():
        return []
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise ValueError(f"{label} JSON格式不正确：{error.msg}") from error
    if not isinstance(payload, list):
        raise ValueError(f"{label}必须是JSON数组。")
    rows: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = str(item.get(name_key, "")).strip()
        code = str(item.get(code_key, "")).strip()
        if name or code:
            rows.append({"name": name, "code": code})
    return rows


def build_record_text(case_json: str, primary_name: str, secondary_items: list[dict[str, str]], procedure_name: str, other_items: list[dict[str, str]]) -> str:
    if case_json.strip():
        return case_json.strip()
    secondary_names = [item["name"] or item["code"] for item in secondary_items]
    other_names = [item["name"] or item["code"] for item in other_items]
    return (
        f"主要诊断：{primary_name}；"
        f"次要诊断列表：{'、'.join(secondary_names) if secondary_names else '无'}；"
        f"主要手术：{procedure_name}；"
        f"其他手术列表：{'、'.join(other_names) if other_names else '无'}。"
    )


def reason_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


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
        user = fetch_one("SELECT * FROM users WHERE username = ?", (username,)) if username else None
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("用户名或密码错误。演示账号：admin / 123456", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            flash("登录成功。", "success")
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
        validation_error = validate_username(username) or validate_password(password)
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
            flash("注册成功，请登录。", "success")
            return redirect(url_for("login"))
    return render_template("register.html", form_data=form_data)


@app.route("/logout")
def logout():
    session.clear()
    flash("已退出登录。", "success")
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
        distributions=case_utils.get_case_distributions(drg_cases),
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
        "system_code": "",
        "design_info": "",
    }
    if request.method == "POST":
        project_name = request.form.get("project_name", project["name"]).strip() or project["name"]
        description = request.form.get("description", project["description"]).strip() or project["description"]
        target = request.form.get("target", project["target"]).strip() or project["target"]
        priority = normalize_choice(request.form.get("priority", project["priority"]), VALID_PRIORITIES, project["priority"])
        system_code = request.form.get("system_code", "").strip()
        design_info = request.form.get("design_info", "").strip()
        form_data = {
            "project_name": project_name,
            "description": description,
            "target": target,
            "priority": priority,
            "system_code": system_code,
            "design_info": design_info,
        }
        validation_error = validate_required_text("项目名称", project_name, MAX_PROJECT_NAME_LENGTH)
        validation_error = validation_error or validate_required_text("业务描述", description, MAX_DESCRIPTION_LENGTH)
        validation_error = validation_error or validate_required_text("目标产物", target, MAX_TARGET_LENGTH)
        if validation_error is not None:
            if request.headers.get("X-Requested-With") == "fetch":
                return jsonify({"ok": False, "message": validation_error}), 400
            flash(validation_error, "warning")
        else:
            generator = RequirementAnalysisGenerator()
            try:
                generation_result = generator.generate(
                    project_name=project_name,
                    description=description,
                    target=target,
                    priority=priority,
                    system_code=system_code,
                    design_info=design_info,
                )
            except Exception as error:
                message = f"DeepSeek生成失败：{error}"
                if request.headers.get("X-Requested-With") == "fetch":
                    return jsonify({"ok": False, "message": message}), 502
                flash(message, "error")
                return redirect(url_for("analysis"))
            database = get_db()
            database.execute(
                """
                UPDATE projects
                SET name = ?, owner_name = ?, priority = ?, phase = ?, target = ?, description = ?, updated_at = ?
                WHERE id = ?
                """,
                (project_name, g.user["username"], priority, "文档生成中", target, description, now_str(), project["id"]),
            )
            drg_cases = get_drg_cases(project["id"])
            pending_documents = build_documents_payload(project_name, drg_cases, generation_result.document_contents)
            store_pending_documents(project["id"], pending_documents)
            replace_agents(project["id"], build_agents_payload(project_name, drg_cases, False))
            replace_messages(project["id"], build_messages_payload(project_name, drg_cases))
            database.commit()
            flash("需求分析已通过DeepSeek生成并同步完成。", "success")
            if request.headers.get("X-Requested-With") == "fetch":
                return jsonify(
                    {
                        "ok": True,
                        "message": "需求分析已通过DeepSeek生成并同步完成。",
                        "document_contents": generation_result.document_contents,
                    }
                )
            return redirect(url_for("analysis"))
    project = get_project()
    return render_template("analysis.html", page_key="analysis", project=project, form_data=form_data)


@app.route("/cases", methods=["GET", "POST"])
@login_required
def cases_page():
    project = get_project()
    form_data = {"case_json": "", "patient_name": "", "primary_diagnosis_code": "", "primary_diagnosis_name": "", "secondary_diagnosis_list": "", "procedure_code": "", "procedure_name": "", "other_procedure_list": ""}
    if request.method == "POST":
        case_json = request.form.get("case_json", "").strip()
        patient_name = request.form.get("patient_name", "").strip()
        primary_name = request.form.get("primary_diagnosis_name", "").strip()
        primary_code = resolve_diagnosis_code(primary_name, request.form.get("primary_diagnosis_code", ""))
        procedure_name = request.form.get("procedure_name", "").strip()
        procedure_code = resolve_procedure_code(procedure_name, request.form.get("procedure_code", ""))
        secondary_raw = request.form.get("secondary_diagnosis_list", "").strip()
        other_raw = request.form.get("other_procedure_list", "").strip()
        form_data = {"case_json": case_json, "patient_name": patient_name, "primary_diagnosis_code": primary_code, "primary_diagnosis_name": primary_name, "secondary_diagnosis_list": secondary_raw, "procedure_code": procedure_code, "procedure_name": procedure_name, "other_procedure_list": other_raw}
        validation_error = validate_required_text("患者姓名", patient_name, MAX_PATIENT_NAME_LENGTH)
        validation_error = validation_error or validate_required_text("主要诊断名称", primary_name, MAX_MEDICAL_NAME_LENGTH)
        validation_error = validation_error or validate_required_text("主要诊断编码", primary_code, MAX_MEDICAL_CODE_LENGTH)
        validation_error = validation_error or validate_required_text("主要手术名称", procedure_name, MAX_MEDICAL_NAME_LENGTH)
        validation_error = validation_error or validate_required_text("主要手术编码", procedure_code, MAX_MEDICAL_CODE_LENGTH)
        secondary_items: list[dict[str, str]] = []
        other_items: list[dict[str, str]] = []
        if validation_error is None:
            try:
                secondary_items = parse_json_list(secondary_raw, "疾病名称", "疾病编码", "次要诊断列表")
                other_items = parse_json_list(other_raw, "手术名称", "手术编码", "其他手术列表")
            except ValueError as error:
                validation_error = str(error)
        record_text = build_record_text(case_json, primary_name, secondary_items, procedure_name, other_items)
        if validation_error is None:
            validation_error = validate_required_text("电子病历摘要", record_text, MAX_RECORD_TEXT_LENGTH)
        if validation_error is not None:
            flash(validation_error, "warning")
        else:
            secondary_codes = [resolve_diagnosis_code(item["name"], item["code"]) for item in secondary_items]
            next_case_number = fetch_one("SELECT COUNT(*) AS count FROM drg_cases WHERE project_id = ?", (project["id"],))["count"] + 1
            case_record = build_case_record(f"CASE-{next_case_number:03d}", patient_name, record_text, primary_code, primary_name, secondary_codes, procedure_code, procedure_name)
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
                (project["id"], case_record["case_code"], case_record["patient_name"], case_record["diagnosis"], case_record["drg_code"], case_record["status"], case_record["risk_level"], case_record["note"], case_record["created_at"], case_record["record_text"], case_record["primary_diagnosis_code"], case_record["primary_diagnosis_name"], case_record["secondary_diagnosis_codes_json"], case_record["procedure_code"], case_record["procedure_name"], case_record["mdc_code"], case_record["mdc_name"], case_record["adrg_code"], case_record["adrg_name"], case_record["drg_name"], case_record["complication_level"], case_record["group_reason"], case_record["updated_at"]),
            )
            database.execute("UPDATE projects SET phase = ?, updated_at = ? WHERE id = ?", ("DRG入组已更新", now_str(), project["id"]))
            sync_generated_content(project["id"], project["name"])
            database.commit()
            flash(f"病例 {case_record['case_code']} 已完成CHS-DRG规则入组。", "success")
            return redirect(url_for("cases_page"))

    drg_cases = get_drg_cases(project["id"])
    mdc_filter = request.args.get("mdc", "").strip().upper()
    risk_filter = request.args.get("risk", "").strip()
    status_filter = request.args.get("status", "").strip()
    keyword = request.args.get("q", "").strip()
    sort_value = request.args.get("sort", "created_desc").strip()
    page = request.args.get("page", type=int) or 1
    mdc_catalog = get_chs_mdc_catalog()
    applied_mdc = case_utils.normalize_case_choice(mdc_filter, {entry["mdc_code"] for entry in mdc_catalog})
    applied_risk = case_utils.normalize_case_choice(risk_filter, {entry["value"] for entry in case_utils.CASE_RISK_OPTIONS})
    applied_status = case_utils.normalize_case_choice(status_filter, {entry["value"] for entry in case_utils.CASE_STATUS_OPTIONS})
    applied_sort = case_utils.normalize_case_sort(sort_value)
    filtered_cases = case_utils.filter_drg_cases(drg_cases, applied_mdc, keyword, applied_risk, applied_status)
    sorted_cases = case_utils.sort_drg_cases(filtered_cases, applied_sort)
    pagination = case_utils.paginate_items(sorted_cases, page)
    has_active_filters = bool(applied_mdc or keyword or applied_risk or applied_status)
    latest_case_source = filtered_cases if has_active_filters else drg_cases
    latest_case = get_latest_case(latest_case_source)
    if latest_case is not None:
        latest_case = {**latest_case, "group_reason_lines": reason_lines(latest_case["group_reason"])}
    base_query_params = {"mdc": applied_mdc, "risk": applied_risk, "status": applied_status, "q": keyword, "sort": applied_sort}
    active_query_params = {key: value for key, value in base_query_params.items() if value and not (key == "sort" and value == "created_desc")}
    pagination_urls = {
        "pages": [{"number": number, "url": url_for("cases_page", **active_query_params, page=number) if number > 1 else url_for("cases_page", **active_query_params), "active": number == pagination["page"]} for number in pagination["page_numbers"]],
        "prev": url_for("cases_page", **active_query_params, page=pagination["prev_page"]) if pagination["has_prev"] and pagination["prev_page"] > 1 else (url_for("cases_page", **active_query_params) if pagination["has_prev"] else ""),
        "next": url_for("cases_page", **active_query_params, page=pagination["next_page"]) if pagination["has_next"] else "",
    }
    return render_template("cases.html", page_key="cases", project=project, drg_cases=pagination["items"], all_case_count=len(drg_cases), filtered_case_count=len(sorted_cases), latest_case=latest_case, form_data=form_data, mdc_catalog=mdc_catalog, risk_options=case_utils.CASE_RISK_OPTIONS, status_options=case_utils.CASE_STATUS_OPTIONS, sort_options=case_utils.CASE_SORT_OPTIONS, pagination=pagination, pagination_urls=pagination_urls, filter_data={"mdc": applied_mdc, "risk": applied_risk, "status": applied_status, "q": keyword, "sort": applied_sort, "active": has_active_filters})


@app.route("/cases/<int:case_id>/delete", methods=["POST"])
@role_required("管理员")
def delete_case(case_id: int):
    project = get_project()
    database = get_db()
    database.execute("DELETE FROM drg_cases WHERE id = ? AND project_id = ?", (case_id, project["id"]))
    database.commit()
    flash("病例已删除。", "success")
    return redirect(url_for("cases_page"))


@app.route("/agents")
@login_required
def agents_page():
    project = get_project()
    return render_template("agents.html", page_key="agents", project=project, agents=get_agents(project["id"]), messages=get_messages(project["id"]))


@app.route("/documents")
@login_required
def documents_page():
    project = get_project()
    documents = get_all_documents(project["id"])
    document_key = request.args.get("document_key", "").strip()
    document_id = request.args.get("document_id", type=int)
    selected = next((item for item in documents if item["doc_key"] == document_key), None)
    if selected is None and document_id is not None:
        selected = next((item for item in documents if item["saved"] and item["id"] == document_id), None)
    if selected is None:
        selected = documents[0] if documents else None
    if selected is not None:
        selected = {**selected, "content_lines": selected["content"].splitlines()}
    return render_template("documents.html", page_key="documents", project=project, documents=documents, selected_document=selected)


@app.route("/documents/<document_key>/save", methods=["POST"])
@login_required
def save_document(document_key: str):
    project = get_project()
    pending_documents = PENDING_DOCUMENTS.get(project["id"], [])
    selected = next((item for item in pending_documents if item["doc_key"] == document_key), None)
    if selected is None:
        flash("未找到待保存文档。", "warning")
        return redirect(url_for("documents_page"))
    database = get_db()
    saved_id = save_document_payload(project["id"], project["name"], selected)
    PENDING_DOCUMENTS[project["id"]] = [item for item in pending_documents if item["doc_key"] != document_key]
    database.commit()
    flash("文档已保存至本地。", "success")
    return redirect(url_for("documents_page", document_id=saved_id))


@app.route("/documents/<int:document_id>/download")
@login_required
def download_document(document_id: int):
    document = fetch_one("SELECT * FROM documents WHERE id = ?", (document_id,))
    if document is None:
        abort(404)
    storage_path = document["storage_path"]
    if not storage_path:
        abort(404)
    path = Path(storage_path)
    if not path.exists():
        abort(404)
    return send_from_directory(path.parent, path.name, as_attachment=True, download_name=f"{sanitize_filename(document['title'])}_{sanitize_filename(document['version'])}.txt")


@app.route("/tests", methods=["GET", "POST"])
@login_required
def tests_page():
    project = get_project()
    if request.method == "POST":
        replace_test_cases(project["id"], build_test_cases_payload(project["name"], get_drg_cases(project["id"])))
        flash("测试用例已重新生成。", "success")
        return redirect(url_for("tests_page"))
    return render_template("tests.html", page_key="tests", project=project, test_cases=get_test_cases(project["id"]))


@app.route("/tests/random-case")
@login_required
def random_test_case():
    try:
        case_input = generate_random_groupable_case_input()
    except ValueError as error:
        return jsonify({"ok": False, "message": str(error)}), 500
    return jsonify({"ok": True, "case_json": json.dumps(case_input, ensure_ascii=False, indent=2)})


@app.route("/tests/random-case/submit", methods=["POST"])
@login_required
def submit_random_test_case():
    project = get_project()
    case_json = request.form.get("case_json", "").strip()
    if not case_json:
        payload = request.get_json(silent=True) or {}
        case_json = str(payload.get("case_json", "")).strip()
    if not case_json:
        return jsonify({"ok": False, "message": "测试用例JSON不能为空。"}), 400
    try:
        json.loads(case_json)
    except json.JSONDecodeError as error:
        return jsonify({"ok": False, "message": f"测试用例JSON格式不正确：{error.msg}"}), 400
    pending_document = add_pending_document(
        project["id"],
        {
            "title": "随机测试用例输入JSON",
            "status": "未保存",
            "version": "V1.0",
            "updated_at": now_str(),
            "source_agent": "测试用例 Agent",
            "content": case_json,
            "received_at": now_str(),
            "storage_path": "",
        },
    )
    return jsonify({"ok": True, "redirect_url": url_for("documents_page", document_key=pending_document["doc_key"])})


@app.route("/submit", methods=["GET", "POST"])
@login_required
def submit_page():
    project = get_project()
    documents = get_documents(project["id"])
    if request.method == "POST":
        selected_ids = [int(value) for value in request.form.getlist("document_ids") if value.isdigit()]
        selected_documents = [item for item in documents if item["id"] in selected_ids]
        if not selected_documents:
            flash("请至少选择一份文档。", "warning")
        else:
            database = get_db()
            database.execute(
                "INSERT INTO submissions (project_id, batch_name, status, docs_count, operator_name, submitted_at, artifact_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (project["id"], f"SUB-{now_str()}", "已提交", len(selected_documents), g.user["username"], now_str(), ""),
            )
            database.commit()
            flash("提交成功。", "success")
            return redirect(url_for("submit_page"))
    return render_template("submit.html", page_key="submit", project=project, documents=documents, submissions=get_submissions(project["id"]))


@app.route("/mobile")
@login_required
def mobile_home():
    project = get_project()
    latest_case = get_latest_case(get_drg_cases(project["id"]))
    highlights = [f"项目阶段：{project['phase']}", f"最新DRG结果：{latest_case['drg_code']}" if latest_case else "暂无DRG入组结果"]
    return render_template("mobile/home.html", page_key="mobile_home", project=project, highlights=highlights, stats=get_stats(project["id"]))


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
        validation_error = validate_required_text("标题", title, MAX_REPORT_TITLE_LENGTH) or validate_required_text("内容", content, MAX_REPORT_CONTENT_LENGTH)
        if validation_error:
            flash(validation_error, "warning")
        else:
            database = get_db()
            database.execute("INSERT INTO mobile_reports (project_id, title, content, priority, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)", (project["id"], title, content, priority, g.user["username"], now_str()))
            database.commit()
            flash("上报成功。", "success")
            return redirect(url_for("mobile_messages"))
    return render_template("mobile/report.html", page_key="mobile_report", project=project, form_data=form_data, priorities=VALID_PRIORITIES)


@app.route("/mobile/messages")
@login_required
def mobile_messages():
    project = get_project()
    return render_template("mobile/messages.html", page_key="mobile_messages", project=project, messages=get_messages(project["id"]), reports=get_mobile_reports(project["id"]))


@app.route("/mobile/documents")
@login_required
def mobile_documents():
    project = get_project()
    return render_template("mobile/documents.html", page_key="mobile_documents", project=project, documents=get_documents(project["id"]))


if __name__ == "__main__":
    with app.app_context():
        init_database()
        seed_demo_data()
    app.run(debug=True)
