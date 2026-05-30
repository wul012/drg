from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from flask import has_request_context, session

from template_generation import get_default_generation_mode, normalize_generation_mode
from platform_config import (
    MAX_PROJECT_NAME_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH,
)

def get_current_generation_mode() -> str:
    if has_request_context():
        return normalize_generation_mode(session.get("generation_mode", get_default_generation_mode()))
    return get_default_generation_mode()


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

