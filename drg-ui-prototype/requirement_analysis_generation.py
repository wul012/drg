from __future__ import annotations

import importlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"


@dataclass(frozen=True)
class RequirementAnalysisResult:
    document_contents: dict[str, str]


class RequirementAnalysisGenerator:
    """Generate requirement-stage deliverables from project context."""

    def __init__(self, config_module: str = "deepseek_config") -> None:
        self.config_module = config_module
        self.api_key = ""
        self.base_url = DEFAULT_DEEPSEEK_BASE_URL
        self.model = DEFAULT_DEEPSEEK_MODEL
        self.timeout_seconds = 60
        self._load_config()

    def generate(
        self,
        project_name: str,
        description: str,
        target: str,
        priority: str,
        system_code: str = "",
        design_info: str = "",
    ) -> RequirementAnalysisResult:
        if not self.api_key:
            raise ValueError("未配置DeepSeek API Key。")

        prompt = self._build_prompt(project_name, description, target, priority, system_code, design_info)
        parsed = self._request_json(prompt)
        normalized = self._normalize_model_payload(parsed)
        return RequirementAnalysisResult(
            document_contents=normalized["document_contents"],
        )

    def _load_config(self) -> None:
        try:
            config = importlib.import_module(self.config_module)
        except ModuleNotFoundError:
            return
        self.api_key = str(getattr(config, "DEEPSEEK_API_KEY", "")).strip()
        self.base_url = str(getattr(config, "DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL)).rstrip("/")
        self.model = str(getattr(config, "DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL)).strip() or DEFAULT_DEEPSEEK_MODEL
        self.timeout_seconds = int(getattr(config, "DEEPSEEK_TIMEOUT_SECONDS", self.timeout_seconds))

    def _build_prompt(
        self,
        project_name: str,
        description: str,
        target: str,
        priority: str,
        system_code: str,
        design_info: str,
    ) -> str:
        return f"""
你是软件工程课程项目的需求分析与文档生成专家。请基于输入的系统需求、系统代码和设计信息，生成规范、可提交、可测试的项目文档。

必须只输出一个JSON对象，不要输出Markdown围栏。JSON结构如下：
{{
  "document_contents": {{
    "需求分析文档": "含系统功能需求、非功能需求、角色、核心用例、业务流程、验收标准",
    "架构设计文档": "含整体结构、模块关系、数据流、接口协作、部署与扩展说明",
    "测试文档": "含测试策略、测试范围、测试方案、关键测试用例与验收口径"
  }}
}}

生成要求：
1. 文档内容使用中文，面向课程大作业完整提交包。
2. 需求分析文档必须包含系统功能需求和用例。
3. 架构设计文档必须包含整体结构和模块关系。
4. 测试文档必须包含测试策略和测试方案。
5. 测试文档可以描述测试范围与方案，但不要输出独立的test_cases数组。
6. 不要编造外部法规版本号；若信息不足，请写明假设和待确认项。

项目名称：{project_name}
业务/系统需求：{description}
目标产物：{target}
优先级：{priority}
系统代码摘要：{system_code or "暂未提供，基于当前项目描述和已有原型能力分析。"}
设计信息：{design_info or "暂未提供，需在文档中标注架构假设。"}
""".strip()

    def _request_json(self, prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你只输出合法JSON对象。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json; charset=utf-8",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        content = response_payload["choices"][0]["message"]["content"]
        return self._parse_json_content(content)

    def _parse_json_content(self, content: str) -> dict[str, Any]:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
        return json.loads(cleaned)

    def _normalize_model_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        document_contents = payload.get("document_contents")

        if not isinstance(document_contents, dict):
            raise ValueError("DeepSeek返回结果缺少document_contents对象。")

        normalized_documents = {
            "需求分析文档": str(document_contents.get("需求分析文档") or "").strip(),
            "架构设计文档": str(document_contents.get("架构设计文档") or "").strip(),
            "测试文档": str(document_contents.get("测试文档") or "").strip(),
        }
        if not all(normalized_documents.values()):
            raise ValueError("DeepSeek返回结果缺少必需文档内容。")
        return {
            "document_contents": normalized_documents,
        }
