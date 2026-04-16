from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from app import app, get_documents, get_project, init_database, seed_demo_data


def bootstrap_test_database() -> tuple[Path, str, bool]:
    temp_dir = Path(tempfile.mkdtemp(prefix="drg-smoke-"))
    db_path = temp_dir / "smoke.db"
    original_database = app.config["DATABASE"]
    original_testing = app.config.get("TESTING", False)
    app.config.update(TESTING=True, DATABASE=str(db_path))
    with app.app_context():
        init_database()
        seed_demo_data()
    return temp_dir, original_database, original_testing


def get_first_document_id() -> int:
    with app.app_context():
        project = get_project()
        documents = get_documents(project["id"])
        if not documents:
            raise AssertionError("Smoke test expected at least one generated document.")
        return documents[0]["id"]


def assert_contains(response_text: str, expected_text: str) -> None:
    if expected_text not in response_text:
        raise AssertionError(f"Expected to find '{expected_text}' in response body.")


def run_smoke_tests() -> None:
    temp_dir, original_database, original_testing = bootstrap_test_database()
    try:
        with app.test_client() as client:
            home_response = client.get("/")
            assert home_response.status_code == 200
            assert_contains(home_response.get_data(as_text=True), "Flask + SQLite 完整项目")

            redirect_response = client.get("/dashboard")
            assert redirect_response.status_code == 302
            assert "/login" in redirect_response.headers["Location"]

            invalid_register_response = client.post(
                "/register",
                data={
                    "username": "ab",
                    "password": "123456",
                    "confirm_password": "123456",
                    "role": "分析员",
                },
                follow_redirects=True,
            )
            assert_contains(invalid_register_response.get_data(as_text=True), "用户名至少需要")

            register_response = client.post(
                "/register",
                data={
                    "username": "tester01",
                    "password": "123456",
                    "confirm_password": "123456",
                    "role": "医生",
                },
                follow_redirects=True,
            )
            assert register_response.status_code == 200
            assert_contains(register_response.get_data(as_text=True), "注册成功")

            login_response = client.post(
                "/login",
                data={"username": "admin", "password": "123456"},
                follow_redirects=True,
            )
            assert login_response.status_code == 200
            assert_contains(login_response.get_data(as_text=True), "工作台")

            invalid_analysis_response = client.post(
                "/analysis",
                data={
                    "project_name": "X" * 41,
                    "description": "测试业务描述",
                    "target": "测试目标产物",
                    "priority": "高",
                    "doc_type": "完整提交包",
                },
                follow_redirects=True,
            )
            assert_contains(invalid_analysis_response.get_data(as_text=True), "项目名称不能超过40个字符。")

            analysis_response = client.post(
                "/analysis",
                data={
                    "project_name": "医保DRG智能协同平台-最终版",
                    "description": "覆盖需求分析、文档生成、提交流转与移动端协同。",
                    "target": "生成完整提交包并留痕",
                    "priority": "高",
                    "doc_type": "完整提交包",
                },
                follow_redirects=True,
            )
            assert analysis_response.status_code == 200
            assert_contains(analysis_response.get_data(as_text=True), "需求分析已完成")

            invalid_case_response = client.post(
                "/cases",
                data={
                    "patient_name": "张三",
                    "record_text": "病例摘要",
                    "primary_diagnosis_code": "",
                    "primary_diagnosis_name": "伤寒性脑膜炎",
                    "secondary_diagnosis_codes": "J96.0",
                    "procedure_code": "38.1000X002",
                    "procedure_name": "动脉内膜剥脱术",
                },
                follow_redirects=True,
            )
            assert_contains(invalid_case_response.get_data(as_text=True), "主诊断编码不能为空。")

            case_response = client.post(
                "/cases",
                data={
                    "patient_name": "张三",
                    "record_text": "患者主诊断 A01.002+G01，次诊断 J96.0，主要手术 38.1000X002。",
                    "primary_diagnosis_code": "A01.002+G01",
                    "primary_diagnosis_name": "伤寒性脑膜炎",
                    "secondary_diagnosis_codes": "J96.0",
                    "procedure_code": "38.1000X002",
                    "procedure_name": "动脉内膜剥脱术",
                },
                follow_redirects=True,
            )
            assert case_response.status_code == 200
            case_body = case_response.get_data(as_text=True)
            assert_contains(case_body, "已完成本地教学规则入组")
            assert_contains(case_body, "MDC")
            assert_contains(case_body, "DRG")

            first_document_id = get_first_document_id()
            submit_response = client.post(
                "/submit",
                data={"document_ids": [str(first_document_id)]},
                follow_redirects=True,
            )
            assert submit_response.status_code == 200
            assert_contains(submit_response.get_data(as_text=True), "提交成功")

            invalid_mobile_report_response = client.post(
                "/mobile/report",
                data={
                    "title": "",
                    "content": "",
                    "priority": "中",
                },
                follow_redirects=True,
            )
            assert_contains(invalid_mobile_report_response.get_data(as_text=True), "上报标题不能为空。")

            report_title = "移动端补充病例规则"
            mobile_report_response = client.post(
                "/mobile/report",
                data={
                    "title": report_title,
                    "content": "需要补充住院天数、并发症描述和术后观察字段。",
                    "priority": "高",
                },
                follow_redirects=True,
            )
            assert mobile_report_response.status_code == 200
            body = mobile_report_response.get_data(as_text=True)
            assert_contains(body, "上报成功")
            assert_contains(body, report_title)

        print("Smoke tests passed.")
    finally:
        app.config.update(DATABASE=original_database, TESTING=original_testing)
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_smoke_tests()
