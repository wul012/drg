from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from platform_config import BASE_DIR, SUBMISSION_ARTIFACTS_DIR, VIRTUAL_DOCS_DIR


def ensure_storage_directories() -> None:
    VIRTUAL_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    SUBMISSION_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


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

