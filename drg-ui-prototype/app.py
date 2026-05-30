from __future__ import annotations

import os
from datetime import datetime
from functools import wraps

from flask import Flask, abort, flash, g, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import drg_case_utils as case_utils
from common import get_current_local_llm_mode, normalize_choice, validate_password, validate_required_text, validate_username
from data_services import *
from drg_rules import *
from local_llm import get_generation_mode_options, get_local_llm_runtime, normalize_generation_mode
from platform_config import *
from storage import sanitize_filename

app = Flask(__name__, instance_path=str(INSTANCE_DIR), instance_relative_config=True)
app.config["SECRET_KEY"] = os.environ.get("DRG_APP_SECRET", "drg-ui-prototype-secret")
app.config["DATABASE"] = str(DATABASE_PATH)
app.teardown_appcontext(close_db)

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
    active_mode = get_current_local_llm_mode()
    return {
        "current_user": user,
        "can_manage_cases": bool(user is not None and user["role"] == "管理员"),
        "local_llm_runtime": get_local_llm_runtime(active_mode),
        "local_llm_mode_options": get_generation_mode_options(),
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
    distributions = case_utils.get_case_distributions(drg_cases)
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
        "llm_mode": get_current_local_llm_mode(),
    }
    if request.method == "POST":
        project_name = request.form.get("project_name", project["name"]).strip() or project["name"]
        description = request.form.get("description", project["description"]).strip() or project["description"]
        target = request.form.get("target", project["target"]).strip() or project["target"]
        priority = normalize_choice(request.form.get("priority", project["priority"]), VALID_PRIORITIES, project["priority"])
        doc_type = normalize_choice(request.form.get("doc_type", "完整提交包"), VALID_DOC_TYPES, "完整提交包")
        llm_mode = normalize_generation_mode(request.form.get("llm_mode", get_current_local_llm_mode()))
        form_data = {
            "project_name": project_name,
            "description": description,
            "target": target,
            "priority": priority,
            "doc_type": doc_type,
            "llm_mode": llm_mode,
        }
        validation_error = validate_required_text("项目名称", project_name, MAX_PROJECT_NAME_LENGTH)
        if validation_error is None:
            validation_error = validate_required_text("业务描述", description, MAX_DESCRIPTION_LENGTH)
        if validation_error is None:
            validation_error = validate_required_text("目标产物", target, MAX_TARGET_LENGTH)
        if validation_error is not None:
            flash(validation_error, "warning")
        else:
            session["local_llm_mode"] = llm_mode
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
        primary_diagnosis_code_raw = request.form.get("primary_diagnosis_code", "")
        primary_diagnosis_name = request.form.get("primary_diagnosis_name", "").strip()
        secondary_diagnosis_raw = request.form.get("secondary_diagnosis_codes", "").strip()
        procedure_code_raw = request.form.get("procedure_code", "")
        procedure_name = request.form.get("procedure_name", "").strip()
        primary_diagnosis_code = resolve_diagnosis_code(primary_diagnosis_name, primary_diagnosis_code_raw)
        procedure_code = resolve_procedure_code(procedure_name, procedure_code_raw)
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
            validation_error = validate_required_text("主诊断名称", primary_diagnosis_name, MAX_MEDICAL_NAME_LENGTH)
        if validation_error is None:
            validation_error = validate_required_text("主手术名称", procedure_name, MAX_MEDICAL_NAME_LENGTH)
        if validation_error is None:
            validation_error = validate_required_text("主诊断编码", primary_diagnosis_code, MAX_MEDICAL_CODE_LENGTH)
        if validation_error is None:
            validation_error = validate_required_text("主手术编码", procedure_code, MAX_MEDICAL_CODE_LENGTH)
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
    risk_filter = request.args.get("risk", "").strip()
    status_filter = request.args.get("status", "").strip()
    keyword = request.args.get("q", "").strip()
    sort_value = request.args.get("sort", "created_desc").strip()
    page = request.args.get("page", type=int) or 1
    mdc_catalog = case_utils.get_mdc_catalog(SIMPLIFIED_MDC_RULES)
    valid_mdc_codes = {entry["mdc_code"] for entry in mdc_catalog}
    risk_values = {entry["value"] for entry in case_utils.CASE_RISK_OPTIONS}
    status_values = {entry["value"] for entry in case_utils.CASE_STATUS_OPTIONS}
    applied_mdc = case_utils.normalize_case_choice(mdc_filter, valid_mdc_codes)
    applied_risk = case_utils.normalize_case_choice(risk_filter, risk_values)
    applied_status = case_utils.normalize_case_choice(status_filter, status_values)
    applied_sort = case_utils.normalize_case_sort(sort_value)
    filtered_cases = case_utils.filter_drg_cases(
        drg_cases,
        applied_mdc,
        keyword,
        applied_risk,
        applied_status,
    )
    sorted_cases = case_utils.sort_drg_cases(filtered_cases, applied_sort)
    pagination = case_utils.paginate_items(sorted_cases, page)
    page_cases = pagination["items"]
    has_active_filters = bool(applied_mdc or keyword or applied_risk or applied_status)
    latest_case_source = filtered_cases if has_active_filters else drg_cases
    base_query_params = {
        "mdc": applied_mdc,
        "risk": applied_risk,
        "status": applied_status,
        "q": keyword,
        "sort": applied_sort,
    }
    active_query_params = {key: value for key, value in base_query_params.items() if value and not (key == "sort" and value == "created_desc")}
    pagination_urls = {
        "pages": [
            {
                "number": number,
                "url": url_for("cases_page", **active_query_params, page=number) if number > 1 else url_for("cases_page", **active_query_params),
                "active": number == pagination["page"],
            }
            for number in pagination["page_numbers"]
        ],
        "prev": url_for("cases_page", **active_query_params, page=pagination["prev_page"]) if pagination["has_prev"] and pagination["prev_page"] > 1 else (url_for("cases_page", **active_query_params) if pagination["has_prev"] else ""),
        "next": url_for("cases_page", **active_query_params, page=pagination["next_page"]) if pagination["has_next"] else "",
    }
    return render_template(
        "cases.html",
        page_key="cases",
        project=project,
        drg_cases=page_cases,
        all_case_count=len(drg_cases),
        filtered_case_count=len(sorted_cases),
        latest_case=get_latest_case(latest_case_source),
        form_data=form_data,
        mdc_catalog=mdc_catalog,
        risk_options=case_utils.CASE_RISK_OPTIONS,
        status_options=case_utils.CASE_STATUS_OPTIONS,
        sort_options=case_utils.CASE_SORT_OPTIONS,
        pagination=pagination,
        pagination_urls=pagination_urls,
        filter_data={
            "mdc": applied_mdc,
            "risk": applied_risk,
            "status": applied_status,
            "q": keyword,
            "sort": applied_sort,
            "active": has_active_filters,
        },
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
