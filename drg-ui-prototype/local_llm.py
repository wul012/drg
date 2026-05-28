from __future__ import annotations

from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import re
from typing import Any, Sequence


BASE_DIR = Path(__file__).resolve().parent
CORPUS_CONFIG_PATH = BASE_DIR / "local_llm_corpus.json"
_BOS = "<BOS>"
_EOS = "<EOS>"
_PUNCTUATION = {"，", "。", "；", "：", "、", "！", "？"}
_STOPWORDS = {"系统", "项目", "当前", "进行", "需要", "可以", "以及", "和", "与", "的", "端", "中心"}
MODE_LABELS = {
    "strict": "严谨模式",
    "balanced": "平衡模式",
    "creative": "增强模式",
}
MODE_HINTS = {
    "strict": "更强调事实命中、字段一致性与规则边界。",
    "balanced": "兼顾稳定事实、结构约束和页面可读性。",
    "creative": "更强调展示表达、讲解节奏与阅读顺序。",
}
MODE_PROFILES = {
    "strict": {"count_weight": 12, "anchor_boost": 52, "overlap_boost": 6, "repeat_penalty": 28, "punctuation_penalty": 30, "closing_bonus": 9},
    "balanced": {"count_weight": 10, "anchor_boost": 36, "overlap_boost": 4, "repeat_penalty": 18, "punctuation_penalty": 24, "closing_bonus": 6},
    "creative": {"count_weight": 8, "anchor_boost": 28, "overlap_boost": 3, "repeat_penalty": 12, "punctuation_penalty": 18, "closing_bonus": 4},
}
TASK_TOKEN_SETTINGS = {
    "reason": {"strict": (6, 4), "balanced": (8, 4), "creative": (10, 5)},
    "analysis": {"strict": (6, 4), "balanced": (8, 4), "creative": (9, 5)},
    "document": {"strict": (5, 4), "balanced": (7, 4), "creative": (8, 5)},
    "test": {"strict": (6, 4), "balanced": (8, 4), "creative": (9, 5)},
}

_REASON_CORPUS = [
    "结合 病例摘要 与 编码信息 可以看到 本次入组路径 比较清晰 。",
    "系统 先 根据 主诊断 锁定 疾病大类 ， 再 结合 主手术 确认 ADRG 。",
    "如果 次诊断 命中 MCC 或 CC ， 风险等级 会 随之 上调 。",
    "从 教学规则 的 解释链 来看 ， 当前结果 具备 连贯的 依据 。",
    "病例摘要 提供了 补充线索 ， 有助于 理解 当前分组 的 业务含义 。",
    "整体判断 更适合 作为 教学演示 的 本地解释结果 。",
    "若 分组链路 仍有 缺口 ， 建议 交由 人工 进一步复核 。",
    "系统 会 把 主诊断 主手术 次诊断 三类线索 串成 一条 解释路径 。",
    "综合 诊断 手术 与 并发症 信息 ， 可以 形成 相对完整 的 DRG 结论 。",
    "当 关键编码 不完整 时 ， 系统 会 自动 提醒 人工关注 。",
]

_ANALYSIS_CORPUS = [
    "围绕 项目目标 展开 分析 时 ， 应 先 明确 主流程 与 交付边界 。",
    "需求摘要 需要 同时 说明 业务焦点 优先级 与 目标产物 。",
    "模块建议 往往 要 覆盖 桌面端 主流程 数据闭环 与 移动端 协同 。",
    "风险识别 应 重点 关注 编码完整性 状态同步 与 版本一致性 。",
    "推荐动作 更适合 采用 先闭环 再扩展 的 迭代节奏 。",
    "如果 项目描述 聚焦 演示链路 ， 分析结果 应 更强调 可运行 与 可验证 。",
    "当 目标产物 指向 完整提交包 时 ， 需求分析 需要 提前 约束 文档 与 测试 范围 。",
    "高优先级 项目 更适合 收敛 关键页面 与 主业务场景 ， 避免 需求发散 。",
]

_DOCUMENT_CORPUS = [
    "从 交付视角 看 ， 文档正文 应 先 给出 总体判断 ， 再 展开 模块与风险 。",
    "架构说明 需要 把 桌面端 移动端 数据落盘 与 提交流程 串成 一条 主线 。",
    "如果 已经 有 最新病例 ， 文档中 应 记录 入组链路 与 风险说明 。",
    "测试文档 更适合 围绕 主流程 边界场景 和 异常校验 组织 内容 。",
    "本地演示 项目 的 文档 应 强调 可运行 可验证 与 数据留痕 。",
    "当 分析结果 已经 成型 时 ， 文档内容 需要 对应 模块建议 风险识别 与 推荐动作 。",
]

_TEST_CORPUS = [
    "测试步骤 应 围绕 页面录入 规则执行 结果展示 与 数据落盘 展开 。",
    "正常场景 需要 验证 DRG 结果 风险等级 与 说明文本 是否 同步输出 。",
    "边界场景 适合 检查 无 CC MCC 时 的 分层表现 与 页面提示 。",
    "异常场景 必须 关注 必填校验 编码缺失 与 非法输入 被 阻止 的 情况 。",
    "如果 文档与提交链路 也是 主流程 ， 测试描述 应 保留 同步刷新 的 期望结果 。",
    "高优先级 用例 应 直接 覆盖 主业务闭环 与 核心结果展示 。",
]

_DEFAULT_CORPORA = {
    "reason": _REASON_CORPUS,
    "analysis": _ANALYSIS_CORPUS,
    "document": _DOCUMENT_CORPUS,
    "test": _TEST_CORPUS,
}


class MiniLocalLLM:
    def __init__(self, corpus: Sequence[str], order: int = 2) -> None:
        self.order = max(1, order)
        self.transitions: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
        self._fit(corpus)

    def _fit(self, corpus: Sequence[str]) -> None:
        for sample in corpus:
            tokens = self._tokenize(sample)
            if not tokens:
                continue
            sequence = [_BOS] * self.order + tokens + [_EOS]
            for index in range(len(sequence) - self.order):
                state = tuple(sequence[index : index + self.order])
                next_token = sequence[index + self.order]
                self.transitions[state][next_token] += 1

    def _tokenize(self, text: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", (text or "").strip())
        return normalized.split(" ") if normalized else []

    def _resolve_state(self, seed_tokens: list[str]) -> tuple[str, ...]:
        if len(seed_tokens) >= self.order:
            direct_state = tuple(seed_tokens[-self.order :])
            if direct_state in self.transitions:
                return direct_state
        for state in self.transitions:
            if seed_tokens and state[-1] == seed_tokens[-1]:
                return state
        return (_BOS,) * self.order

    def _score_candidate(
        self,
        token: str,
        count: int,
        anchors: Sequence[str],
        generated: list[str],
        min_tokens: int,
        profile: dict[str, int],
    ) -> int:
        score = count * profile["count_weight"]
        if token == _EOS:
            return score if len(generated) >= min_tokens else -10_000
        if token not in _PUNCTUATION:
            score += min(len(token), 6)
        if token in generated[-3:]:
            score -= profile["repeat_penalty"]
        if token in _PUNCTUATION and generated and generated[-1] in _PUNCTUATION:
            score -= profile["punctuation_penalty"]
        if token in {"。", "；"} and len(generated) >= min_tokens:
            score += profile["closing_bonus"]
        for anchor in anchors:
            if not anchor:
                continue
            if token in anchor or anchor in token:
                score += profile["anchor_boost"]
            elif any(char in anchor for char in token if char not in _PUNCTUATION):
                score += profile["overlap_boost"]
        return score

    def generate(
        self,
        seed_tokens: Sequence[str],
        anchors: Sequence[str] = (),
        max_tokens: int = 10,
        min_tokens: int = 4,
        fallback: str = "",
        profile: dict[str, int] | None = None,
    ) -> str:
        active_profile = profile or MODE_PROFILES["balanced"]
        generated = [token for token in seed_tokens if token]
        state = self._resolve_state(generated)
        for _ in range(max_tokens):
            counter = self.transitions.get(state)
            if not counter:
                counter = self.transitions.get((_BOS,) * self.order, Counter())
            token = max(
                counter.items(),
                key=lambda item: (
                    self._score_candidate(item[0], item[1], anchors, generated, min_tokens, active_profile),
                    item[1],
                    item[0],
                ),
            )[0] if counter else _EOS
            if token == _EOS:
                break
            generated.append(token)
            state = tuple((list(state) + [token])[-self.order :])
            if token in {"。", "！", "？"} and len(generated) >= min_tokens:
                break
        rendered = _render_tokens(generated)
        return rendered if _count_meaningful_chars(rendered) >= 4 else fallback


def normalize_generation_mode(value: str) -> str:
    return value if value in MODE_LABELS else "balanced"


def get_default_generation_mode() -> str:
    return normalize_generation_mode(os.environ.get("DRG_LOCAL_LLM_MODE", "balanced"))


def get_generation_mode_label(mode: str) -> str:
    return MODE_LABELS[normalize_generation_mode(mode)]


def get_generation_mode_options() -> list[dict[str, str]]:
    return [{"value": value, "label": label} for value, label in MODE_LABELS.items()]


def _load_external_corpora() -> dict[str, list[str]]:
    payload_map = {task: [] for task in _DEFAULT_CORPORA}
    if not CORPUS_CONFIG_PATH.exists():
        return payload_map
    try:
        raw_payload = json.loads(CORPUS_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return payload_map
    if not isinstance(raw_payload, dict):
        return payload_map
    for task in payload_map:
        values = raw_payload.get(task, [])
        if isinstance(values, list):
            payload_map[task] = [item.strip() for item in values if isinstance(item, str) and item.strip()]
    return payload_map


def _build_corpus_bundle() -> dict[str, list[str]]:
    external_corpora = _load_external_corpora()
    return {
        task: [*_DEFAULT_CORPORA[task], *external_corpora.get(task, [])]
        for task in _DEFAULT_CORPORA
    }


_CORPUS_BUNDLE = _build_corpus_bundle()
_MODEL_CACHE = {task: MiniLocalLLM(samples) for task, samples in _CORPUS_BUNDLE.items()}


def get_local_llm_runtime(mode: str | None = None) -> dict[str, Any]:
    active_mode = normalize_generation_mode(mode or get_default_generation_mode())
    return {
        "mode": active_mode,
        "label": get_generation_mode_label(active_mode),
        "hint": MODE_HINTS[active_mode],
        "corpus_path": CORPUS_CONFIG_PATH.name,
        "external_corpus_loaded": CORPUS_CONFIG_PATH.exists(),
        "corpus_sizes": {task: len(samples) for task, samples in _CORPUS_BUNDLE.items()},
    }


def _render_tokens(tokens: Sequence[str]) -> str:
    return "".join(token for token in tokens if token not in {_BOS, _EOS})


def _strip_tail(text: str) -> str:
    return (text or "").rstrip("，。；：、！？ ")


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\n", " ")).strip()


def _clip_text(text: str, limit: int) -> str:
    normalized = _normalize_text(text)
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}…"


def _count_meaningful_chars(text: str) -> int:
    return len([char for char in text if char not in _PUNCTUATION and not char.isspace()])


def _pick_by_mode(mode: str, strict: str, balanced: str, creative: str) -> str:
    active_mode = normalize_generation_mode(mode)
    if active_mode == "strict":
        return strict
    if active_mode == "creative":
        return creative
    return balanced


def _style(
    task: str,
    seed: Sequence[str],
    anchors: Sequence[str],
    fallback: str,
    mode: str | None = None,
    max_tokens: int | None = None,
    min_tokens: int | None = None,
) -> str:
    active_mode = normalize_generation_mode(mode or get_default_generation_mode())
    default_max, default_min = TASK_TOKEN_SETTINGS.get(task, {}).get(active_mode, (8, 4))
    phrase = _MODEL_CACHE[task].generate(
        seed,
        anchors,
        max_tokens=max_tokens if max_tokens is not None else default_max,
        min_tokens=min_tokens if min_tokens is not None else default_min,
        fallback=fallback,
        profile=MODE_PROFILES[active_mode],
    )
    return _strip_tail(phrase) or fallback


def _unique(items: Sequence[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def _extract_focus_terms(*texts: str) -> list[str]:
    terms: list[str] = []
    for text in texts:
        normalized = _normalize_text(text)
        for token in re.findall(r"[A-Za-z0-9.+/-]{2,}|[\u4e00-\u9fff]{2,8}", normalized):
            if token not in _STOPWORDS and token not in terms:
                terms.append(token)
    return terms[:8]


def _infer_modules(description: str, target: str, doc_type: str) -> list[str]:
    combined = f"{description} {target} {doc_type}"
    modules = ["需求分析中心", "DRG规则匹配中心"]
    if "移动" in combined:
        modules.append("移动端协同中心")
    if "消息" in combined or "Agent" in combined or "协作" in combined:
        modules.append("多Agent协作中心")
    if "文档" in combined or "提交" in combined or "完整提交包" in combined:
        modules.append("文档生成中心")
    if "测试" in combined or "提交" in combined:
        modules.append("测试与提交中心")
    modules.append("工作台总览中心")
    return _unique(modules)[:6]


def generate_drg_reason(
    primary_diagnosis_code: str,
    primary_diagnosis_name: str,
    procedure_code: str,
    procedure_name: str,
    mdc_code: str,
    mdc_name: str,
    adrg_code: str,
    adrg_name: str,
    drg_code: str,
    drg_name: str,
    complication_level: str,
    complication_reason: str,
    risk_level: str,
    status: str,
    raw_record: str,
    mode: str | None = None,
) -> str:
    active_mode = normalize_generation_mode(mode or get_default_generation_mode())
    anchors = [mdc_code, adrg_code, drg_code, complication_level, risk_level, status]
    intro = _style("reason", ["结合"], anchors, "结合病例摘要与编码信息可以看到", mode=active_mode)
    closing = _style("reason", ["整体判断"], anchors, "整体判断与当前教学规则保持一致", mode=active_mode)
    procedure_display = f"{procedure_code or '未填写'}（{procedure_name or '未填写'}）"
    mode_tail = _pick_by_mode(
        active_mode,
        "整段说明更强调规则命中、事实一致性与复核边界。",
        "整段说明兼顾事实链路、阅读顺序与页面可读性。",
        "整段说明更突出展示表达、讲解节奏与链路完整性。",
    )
    parts = [
        f"{intro}。",
        f"主诊断 {primary_diagnosis_code}（{primary_diagnosis_name}）命中 {mdc_code} {mdc_name}。",
        f"系统随后根据主手术 {procedure_display}归入 {adrg_code} {adrg_name}，{complication_reason.rstrip('。')}。",
        "系统会把主诊断、主手术和次诊断线索串成一条解释路径。",
        f"综合分层结果与教学规则，最终得到 {drg_code} {drg_name}，当前状态为 {status}，风险等级为 {risk_level}。",
    ]
    if raw_record:
        record_hint = _pick_by_mode(
            active_mode,
            "病例摘要被作为补充证据纳入解释链路。",
            "病例摘要也提供了辅助线索。",
            "病例摘要进一步补足了这条本地解释链路。",
        ).rstrip("。")
        parts.append(f"{record_hint}，其中“{_clip_text(raw_record, 28)}”被纳入本地微型LLM解释链路。")
    if status != "已完成":
        review_hint = _style("reason", ["若"], anchors, "若分组链路仍有缺口", mode=active_mode)
        parts.append(f"{review_hint}，建议人工复核。")
    else:
        parts.append(f"{closing}，{mode_tail} 可作为当前教学场景下的本地分组说明。")
    return "".join(parts)


def generate_analysis_payload(project_name: str, description: str, target: str, priority: str, doc_type: str, mode: str | None = None) -> dict[str, list[str]]:
    active_mode = normalize_generation_mode(mode or get_default_generation_mode())
    focus_excerpt = _clip_text(f"{description} {target}", 34) or "DRG规则匹配与文档生成闭环"
    focus_terms = _extract_focus_terms(project_name, description, target, doc_type)
    intro = _style("analysis", ["围绕"], [project_name, priority, doc_type], "围绕项目目标展开分析时", mode=active_mode)
    close = _style("analysis", ["推荐动作"], [priority, doc_type], "推荐动作更适合采用先闭环再扩展的节奏", mode=active_mode)
    modules = _infer_modules(description, target, doc_type)
    strategy_line = _pick_by_mode(
        active_mode,
        "建议优先锁定字段约束、状态同步和版本一致性，再推进展示层扩展。",
        "建议先收口可运行、可验证的主业务闭环，再扩展展示层与讲解层。",
        "建议把可运行闭环、展示亮点和答辩讲解节奏一起纳入本轮方案。",
    )
    recommendation_tail = _pick_by_mode(
        active_mode,
        "将模式保持在严谨表达，优先保证事实链与表述链一致。",
        "将模式保持在平衡表达，兼顾结构稳定和自然表述。",
        "将模式切到增强表达，更适合现场展示与流程讲解。",
    )
    summary = [
        f"{intro}，项目“{project_name}”当前聚焦 {focus_excerpt}。",
        f"从交付约束看，本轮优先级为{priority}，目标产物定位为{doc_type}。",
        f"结合 {('、'.join(focus_terms[:3]) if focus_terms else '桌面端主流程')} 等重点信息，{strategy_line}",
    ]
    risks = [
        f"如果病例编码、需求描述或目标产物表达不完整，后续 DRG、文档与测试生成会出现上下文偏差。",
        "当桌面端状态、Agent消息和移动端上报不同步时，协作链路容易出现展示与数据不一致。",
        "如果文档版本、测试用例与提交批次没有同步刷新，最终演示效果和答辩稳定性都会受到影响。",
    ]
    recommendations = [
        f"{close}，先把需求分析、病例入组、文档生成和提交中心串成一条主线。",
        f"围绕 {('、'.join(modules[:3]))} 做展示收口，把高频入口集中到工作台与病例页。",
        f"把移动端保持在上报、消息、文档查看三个高频场景，避免演示路径过长；{recommendation_tail}",
    ]
    return {
        "summary": summary,
        "modules": modules,
        "risks": risks,
        "recommendations": recommendations,
    }


def generate_document_contents(
    project_name: str,
    analysis_payload: dict[str, list[str]],
    latest_case: dict[str, Any] | None,
    mode: str | None = None,
) -> dict[str, str]:
    active_mode = normalize_generation_mode(mode or get_default_generation_mode())
    focus_intro = _style("document", ["从"], [project_name], "从交付视角看", mode=active_mode)
    architecture_intro = _style("document", ["架构说明"], [project_name], "架构说明需要把关键页面与数据落盘串成主线", mode=active_mode)
    test_intro = _style("document", ["测试文档"], [project_name], "测试文档更适合围绕主流程与异常校验组织内容", mode=active_mode)
    mode_line = f"当前采用 {get_generation_mode_label(active_mode)} 的本地微型LLM 文风，并结合 {CORPUS_CONFIG_PATH.name} 中的扩展语料。"
    architecture_tail = _pick_by_mode(
        active_mode,
        "结构说明优先强调模块关系、数据落盘与边界控制。",
        "结构说明兼顾页面层级、数据链路与演示完整性。",
        "结构说明更强调展示叙事、亮点归纳与讲解顺序。",
    )
    test_tail = _pick_by_mode(
        active_mode,
        "测试文案优先压实校验条件和回归边界。",
        "测试文案兼顾稳定事实和阅读友好度。",
        "测试文案更强调展示效果和链路表达。",
    )
    latest_case_lines = []
    if latest_case:
        latest_case_lines = [
            f"五、最新病例：{latest_case['case_code']} / {latest_case['patient_name']}。",
            f"六、入组链路：{latest_case['mdc_code']} -> {latest_case['adrg_code']} -> {latest_case['drg_code']}。",
            f"七、入组说明：{latest_case['group_reason']}",
        ]
    else:
        latest_case_lines = ["五、当前暂无新增病例，文档内容主要基于需求分析上下文生成。"]
    return {
        "需求分析文档": "\n".join(
            [
                f"一、项目名称：{project_name}",
                f"二、总体判断：{focus_intro}，当前项目已经形成“{'；'.join(analysis_payload['summary'])}”这一分析基线。",
                f"三、建议模块：{'、'.join(analysis_payload['modules'])}。",
                f"四、风险与动作：{'；'.join(analysis_payload['risks'])}；建议 {'；'.join(analysis_payload['recommendations'])}",
                f"五、生成策略：{mode_line}",
            ]
        ),
        "架构设计文档": "\n".join(
            [
                "一、系统采用 Flask + SQLite 的本地可运行架构。",
                f"二、总体结构：{architecture_intro}，桌面端负责需求分析、DRG入组、Agent、文档、测试与提交，移动端负责上报、消息与文档查看。",
                "三、数据策略：项目、分析结果、病例、文档、测试用例和提交记录统一写入本地数据库，并同步落到虚拟文档目录。",
                f"四、结构表达：{architecture_tail}",
                *latest_case_lines,
            ]
        ),
        "测试文档": "\n".join(
            [
                f"一、测试范围：{test_intro}，重点覆盖 {project_name} 的主业务链路与 DRG 入组闭环。",
                "二、主流程覆盖：需求分析录入、病例入组、文档同步、测试用例刷新和提交中心留痕。",
                "三、重点边界：无 CC/MCC 分层、关键词筛选为空、分页与排序切换、文档下载与无效提交拦截。",
                f"四、回归重点：{'；'.join(analysis_payload['recommendations'][:2])}",
                f"五、模式说明：{test_tail}",
            ]
        ),
    }


def generate_test_cases(project_name: str, drg_cases: list[dict[str, Any]], mode: str | None = None) -> list[dict[str, str]]:
    active_mode = normalize_generation_mode(mode or get_default_generation_mode())
    latest_case = drg_cases[-1] if drg_cases else None
    latest_case_code = latest_case["case_code"] if latest_case else "CASE-DEMO"
    latest_case_drg = latest_case["drg_code"] if latest_case else "GD15"
    normal_intro = _style("test", ["正常场景"], [latest_case_code, latest_case_drg], "正常场景需要验证主流程结果是否完整", mode=active_mode)
    edge_intro = _style("test", ["边界场景"], [project_name], "边界场景适合检查分层与说明文本", mode=active_mode)
    exception_intro = _style("test", ["异常场景"], [project_name], "异常场景必须关注字段校验与非法输入拦截", mode=active_mode)
    timestamp_hint = _style("test", ["测试步骤"], [latest_case_code], "测试步骤应围绕页面录入规则执行与结果展示展开", mode=active_mode)
    delivery_intro = _style("test", ["测试步骤"], [project_name, "提交"], "如果文档与提交链路也是主流程，测试描述应保留同步刷新预期", mode=active_mode)
    mode_assertion = _pick_by_mode(
        active_mode,
        "当前模式更强调校验边界、字段一致性与结果可追溯性。",
        "当前模式兼顾结果稳定性与页面可读性。",
        "当前模式更强调展示表达、讲解顺序与链路完整性。",
    )
    return [
        {
            "case_code": "TC-201",
            "feature": "DRG入组主链路校验",
            "precondition_text": f"{normal_intro}，已准备包含主诊断、次诊断和主手术编码的完整病例数据。",
            "steps_text": f"进入 {project_name} 的病例录入页，提交病例 {latest_case_code} 并执行本地教学规则入组；{timestamp_hint}。",
            "expected_text": f"页面成功输出 MDC / ADRG / DRG，最新病例结果展示为 {latest_case_drg}，并同时生成一段更自然的本地微型LLM原因说明；{mode_assertion}",
            "priority": "高",
            "case_category": "正常",
        },
        {
            "case_code": "TC-202",
            "feature": "无CC/MCC边界场景校验",
            "precondition_text": f"{edge_intro}，次诊断为空或未命中 CC/MCC 列表。",
            "steps_text": "提交仅包含主诊断与主手术的病例，观察分层结果、风险等级与说明文本是否同步刷新。",
            "expected_text": "系统输出无CC/MCC分层结果，风险等级保持在可解释范围内，并给出完整且可阅读的入组原因说明。",
            "priority": "中",
            "case_category": "边界",
        },
        {
            "case_code": "TC-203",
            "feature": "编码缺失异常场景校验",
            "precondition_text": f"{exception_intro}，主诊断编码或主手术编码为空。",
            "steps_text": f"在 {project_name} 的病例录入页提交不完整编码数据，检查页面校验、数据库写入与测试文档是否被错误刷新。",
            "expected_text": "页面阻止提交并给出字段校验提示，不写入错误病例，也不会产生误导性的 DRG 结果。",
            "priority": "高",
            "case_category": "异常",
        },
        {
            "case_code": "TC-204",
            "feature": "文档提交与留痕校验",
            "precondition_text": f"{delivery_intro}，系统已生成最新需求、架构与测试文档。",
            "steps_text": "进入提交中心勾选文档并确认提交，检查提交批次、提交清单和消息流是否同步刷新。",
            "expected_text": "系统生成新的提交批次，落地本地提交清单文件，并把项目阶段更新为已提交待审核。",
            "priority": "中",
            "case_category": "正常",
        },
    ]
