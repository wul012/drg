const STORAGE_KEY = "drgPrototypeStateV1";
const SESSION_KEY = "drgPrototypeSessionV1";

const routes = {
    index: "/index.html",
    login: "/pages/login.html",
    dashboard: "/pages/dashboard.html",
    analysis: "/pages/analysis.html",
    drg: "/pages/drg.html",
    agents: "/pages/agents.html",
    documents: "/pages/documents.html",
    tests: "/pages/tests.html",
    submit: "/pages/submit.html",
    mobileLogin: "/pages/mobile-login.html",
    mobileHome: "/pages/mobile-home.html",
    mobileReport: "/pages/mobile-report.html",
    mobileMessages: "/pages/mobile-messages.html",
    mobileDocs: "/pages/mobile-docs.html"
};

const defaultState = {
    project: {
        name: "医保DRG智能协同平台",
        owner: "王医生",
        role: "分析员",
        priority: "高",
        phase: "需求分析中",
        target: "生成需求分析、测试用例与提交包",
        description: "围绕住院病例DRG入组、文档生成与智能协作的课程实验原型。"
    },
    analysis: {
        summary: [
            "系统需要支持病例信息录入、DRG规则匹配和智能需求摘要生成。",
            "需要通过多Agent协作把需求分析、文档生成、测试用例和提交流程串联起来。",
            "移动端承担快速上报与结果查看，PC端承担分析、编排和提交。"
        ],
        modules: [
            "需求分析中心",
            "DRG规则匹配引擎",
            "多Agent协作总线",
            "文档生成中心",
            "测试与提交中心"
        ],
        risks: [
            "病例数据格式不统一可能导致规则匹配偏差。",
            "多Agent任务衔接需要清晰的状态同步。",
            "提交前需要统一校验文档版本与测试覆盖率。"
        ],
        recommendations: [
            "优先保证主流程闭环：需求 -> 分析 -> 文档 -> 提交。",
            "文档生成和测试用例生成使用统一项目上下文。",
            "移动端只承载轻量输入与结果查看，避免流程复杂化。"
        ]
    },
    drgCases: [
        {
            id: "CASE-001",
            patient: "张某某",
            diagnosis: "急性阑尾炎",
            drg: "GB15",
            status: "已完成",
            risk: "低",
            note: "主要诊断明确，手术路径清晰。"
        },
        {
            id: "CASE-002",
            patient: "李某某",
            diagnosis: "肺部感染伴并发症",
            drg: "EB23",
            status: "分析中",
            risk: "中",
            note: "需补充合并症编码和住院天数。"
        },
        {
            id: "CASE-003",
            patient: "赵某某",
            diagnosis: "糖尿病足感染",
            drg: "KT11",
            status: "待复核",
            risk: "高",
            note: "治疗路径复杂，建议复核手术与并发症信息。"
        }
    ],
    agents: [
        {
            name: "需求分析 Agent",
            status: "已完成",
            owner: "产品侧",
            focus: "提炼需求目标与功能边界"
        },
        {
            name: "DRG 分析 Agent",
            status: "运行中",
            owner: "业务侧",
            focus: "匹配病例与DRG分组规则"
        },
        {
            name: "文档生成 Agent",
            status: "待处理",
            owner: "交付侧",
            focus: "输出需求、设计与测试文档"
        },
        {
            name: "测试用例 Agent",
            status: "待处理",
            owner: "测试侧",
            focus: "形成测试步骤与预期结果"
        },
        {
            name: "提交 Agent",
            status: "待处理",
            owner: "管理侧",
            focus: "打包并提交虚拟文档系统"
        }
    ],
    messages: [
        {
            from: "需求分析 Agent",
            to: "DRG 分析 Agent",
            content: "已提取项目核心目标，请开始DRG规则匹配与风险识别。",
            time: "09:30"
        },
        {
            from: "DRG 分析 Agent",
            to: "文档生成 Agent",
            content: "两条病例规则已完成，建议先生成需求分析文档初稿。",
            time: "09:42"
        }
    ],
    documents: [
        {
            id: "DOC-REQ",
            title: "需求分析文档",
            status: "已生成",
            version: "V1.0",
            updatedAt: "2026-04-14 21:00",
            content: [
                "一、项目目标：构建医保DRG智能协同平台，用于病例规则分析、文档输出与课程实验展示。",
                "二、核心功能：登录、需求分析、DRG规则匹配、多Agent协作、文档生成、测试用例生成、提交中心。",
                "三、端侧分工：PC端负责分析与编排，移动端负责快速上报与结果查看。"
            ]
        },
        {
            id: "DOC-ARC",
            title: "架构设计文档",
            status: "待更新",
            version: "V0.9",
            updatedAt: "2026-04-14 21:05",
            content: [
                "一、系统采用前端原型方式模拟业务闭环。",
                "二、模块包括工作台、需求分析、Agent协作、文档中心、测试中心、提交流程与移动端。",
                "三、数据由浏览器本地存储维护，用于演示状态流转。"
            ]
        },
        {
            id: "DOC-TEST",
            title: "测试用例文档",
            status: "待生成",
            version: "V0.3",
            updatedAt: "2026-04-14 21:08",
            content: [
                "一、覆盖登录、需求录入、分析生成、文档预览与提交流程。",
                "二、覆盖移动端上报与查看。",
                "三、覆盖异常状态展示。"
            ]
        }
    ],
    testCases: [
        {
            id: "TC-001",
            feature: "登录",
            precondition: "用户已注册演示账号",
            steps: "输入用户名、密码并点击登录",
            expected: "进入工作台首页并显示用户信息",
            priority: "高"
        },
        {
            id: "TC-002",
            feature: "需求分析",
            precondition: "进入需求分析页",
            steps: "填写项目名称、需求描述、目标并点击开始分析",
            expected: "生成摘要、模块建议和风险识别结果",
            priority: "高"
        },
        {
            id: "TC-003",
            feature: "文档提交",
            precondition: "文档已生成",
            steps: "在提交中心勾选文档并点击确认提交",
            expected: "新增一次提交记录并返回工作台",
            priority: "中"
        }
    ],
    submissions: [
        {
            id: "SUB-001",
            batch: "实验二演示批次",
            status: "待审核",
            submittedAt: "2026-04-14 21:12",
            docs: 2,
            operator: "王医生"
        }
    ],
    mobileReports: [
        {
            title: "新增住院病例录入需求",
            content: "移动端需要支持病例摘要快速上报，并同步到PC端工作台。",
            priority: "高",
            createdAt: "2026-04-14 21:10"
        }
    ]
};

function clone(value) {
    return JSON.parse(JSON.stringify(value));
}

function mergeState(saved) {
    if (!saved) {
        return clone(defaultState);
    }
    const state = clone(defaultState);
    return {
        ...state,
        ...saved,
        project: { ...state.project, ...(saved.project || {}) },
        analysis: { ...state.analysis, ...(saved.analysis || {}) }
    };
}

function getState() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
        const state = clone(defaultState);
        saveState(state);
        return state;
    }
    try {
        return mergeState(JSON.parse(raw));
    } catch (error) {
        const state = clone(defaultState);
        saveState(state);
        return state;
    }
}

function saveState(state) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function getSession() {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) {
        return null;
    }
    try {
        return JSON.parse(raw);
    } catch (error) {
        localStorage.removeItem(SESSION_KEY);
        return null;
    }
}

function setSession(payload) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(payload));
}

function clearSession() {
    localStorage.removeItem(SESSION_KEY);
}

function $(selector) {
    return document.querySelector(selector);
}

function $$(selector) {
    return Array.from(document.querySelectorAll(selector));
}

function setText(selector, value) {
    const element = $(selector);
    if (element) {
        element.textContent = value;
    }
}

function goTo(route) {
    window.location.href = route;
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function statusClass(status) {
    if (status.includes("完成") || status.includes("通过") || status.includes("已生成") || status.includes("已提交")) {
        return "success";
    }
    if (status.includes("运行") || status.includes("审核") || status.includes("分析中") || status.includes("待更新")) {
        return "warning";
    }
    if (status.includes("高") || status.includes("异常") || status.includes("退回")) {
        return "danger";
    }
    return "";
}

function formatNow() {
    const now = new Date();
    const pad = (value) => String(value).padStart(2, "0");
    return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
}

function requireAuth(page) {
    if (["index", "login", "mobile-login"].includes(page)) {
        return;
    }
    const session = getSession();
    if (!session) {
        if (page.startsWith("mobile")) {
            goTo(routes.mobileLogin);
            return;
        }
        goTo(routes.login);
    }
}

function bindGlobalActions() {
    $$('[data-action="logout"]').forEach((button) => {
        button.addEventListener("click", () => {
            clearSession();
            goTo(routes.index);
        });
    });

    $$('[data-action="reset-demo"]').forEach((button) => {
        button.addEventListener("click", () => {
            saveState(clone(defaultState));
            if (!window.location.pathname.endsWith("index.html")) {
                window.location.reload();
            }
        });
    });

    const session = getSession();
    if (!session) {
        return;
    }

    $$('[data-user-name]').forEach((element) => {
        element.textContent = session.username;
    });
    $$('[data-user-role]').forEach((element) => {
        element.textContent = session.role;
    });
    $$('[data-user-avatar]').forEach((element) => {
        element.textContent = session.username.slice(0, 1);
    });
}

function buildAnalysisPayload(formData) {
    const text = `${formData.description} ${formData.target}`.replace(/\s+/g, " ").trim();
    const focus = text.slice(0, 36) || "DRG规则匹配与文档生成";
    return {
        summary: [
            `围绕“${formData.projectName}”，系统需要优先处理 ${focus}。`,
            `当前需求优先级为${formData.priority}，目标文档类型为${formData.docType}。`,
            `建议采用PC端主导分析、移动端承载快速上报的双端协同模式。`
        ],
        modules: [
            "病例数据接入模块",
            "DRG规则匹配模块",
            "多Agent任务编排模块",
            "文档自动生成模块",
            "提交与追踪模块"
        ],
        risks: [
            "编码缺失会影响DRG分组准确性。",
            "Agent间状态同步若不明确会导致流程中断。",
            "提交前未锁定版本可能造成文档与测试数据不一致。"
        ],
        recommendations: [
            "先形成需求分析与DRG规则说明，再生成设计和测试文档。",
            "把核心状态集中展示在工作台和Agent协作页。",
            "移动端只保留上报、消息和文档查看三个高频场景。"
        ]
    };
}

function buildDocuments(projectName, analysis) {
    const time = formatNow();
    return [
        {
            id: "DOC-REQ",
            title: "需求分析文档",
            status: "已生成",
            version: "V1.1",
            updatedAt: time,
            content: [
                `一、项目名称：${projectName}`,
                `二、需求摘要：${analysis.summary.join("；")}`,
                `三、建议模块：${analysis.modules.join("、")}`
            ]
        },
        {
            id: "DOC-ARC",
            title: "架构设计文档",
            status: "待更新",
            version: "V1.0",
            updatedAt: time,
            content: [
                "一、采用前端原型模拟多角色协作场景。",
                "二、PC端包含工作台、分析、Agent协作、测试与提交中心。",
                "三、移动端包含登录、上报、消息与文档查看。"
            ]
        },
        {
            id: "DOC-TEST",
            title: "测试用例文档",
            status: "已生成",
            version: "V1.0",
            updatedAt: time,
            content: [
                `一、重点覆盖${projectName}的主业务链路。`,
                "二、覆盖登录、分析、消息联动、文档预览和提交。",
                "三、覆盖移动端上报和结果查看。"
            ]
        }
    ];
}

function buildTestCases(projectName) {
    return [
        {
            id: "TC-101",
            feature: "需求分析自动生成",
            precondition: "用户进入需求分析页",
            steps: `填写${projectName}业务描述并点击开始分析`,
            expected: "生成摘要、模块建议与风险识别",
            priority: "高"
        },
        {
            id: "TC-102",
            feature: "Agent协作流转",
            precondition: "分析结果已生成",
            steps: "进入Agent协作页查看消息流和当前任务",
            expected: "看到从需求分析到文档生成的消息链路",
            priority: "高"
        },
        {
            id: "TC-103",
            feature: "提交中心",
            precondition: "文档列表已准备完成",
            steps: "确认提交批次并点击提交",
            expected: "写入新的提交记录并更新状态",
            priority: "中"
        }
    ];
}

function buildMessages(projectName) {
    return [
        {
            from: "需求分析 Agent",
            to: "DRG 分析 Agent",
            content: `已解析 ${projectName} 的需求上下文，请补充规则匹配结果。`,
            time: formatNow().slice(11)
        },
        {
            from: "DRG 分析 Agent",
            to: "文档生成 Agent",
            content: "规则匹配完成，请输出需求分析文档与风险提示。",
            time: formatNow().slice(11)
        },
        {
            from: "文档生成 Agent",
            to: "测试用例 Agent",
            content: "已生成初版文档，请同步形成测试覆盖清单。",
            time: formatNow().slice(11)
        }
    ];
}

function buildAgents() {
    return [
        {
            name: "需求分析 Agent",
            status: "已完成",
            owner: "产品侧",
            focus: "解析输入需求并提炼关键模块"
        },
        {
            name: "DRG 分析 Agent",
            status: "已完成",
            owner: "业务侧",
            focus: "输出DRG规则匹配与风险说明"
        },
        {
            name: "文档生成 Agent",
            status: "运行中",
            owner: "交付侧",
            focus: "生成需求与设计文档"
        },
        {
            name: "测试用例 Agent",
            status: "待处理",
            owner: "测试侧",
            focus: "整理测试步骤和预期结果"
        },
        {
            name: "提交 Agent",
            status: "待处理",
            owner: "管理侧",
            focus: "打包提交并写入记录"
        }
    ];
}

function initLandingPage() {
    const state = getState();
    setText("#landingProjectName", state.project.name);
    setText("#landingProjectDesc", state.project.description);
    setText("#landingDocCount", String(state.documents.length));
    setText("#landingCaseCount", String(state.drgCases.length));
    setText("#landingSubmissionCount", String(state.submissions.length));

    const session = getSession();
    const hint = $("#landingSessionHint");
    const continueButton = $("#continueButton");
    if (session && hint && continueButton) {
        hint.textContent = `当前登录：${session.username} / ${session.role}`;
        continueButton.classList.remove("hidden");
        continueButton.addEventListener("click", () => {
            if (session.entry === "mobile") {
                goTo(routes.mobileHome);
                return;
            }
            goTo(routes.dashboard);
        });
    }
}

function initLoginPage(isMobile) {
    const session = getSession();
    if (session) {
        goTo(isMobile ? routes.mobileHome : routes.dashboard);
        return;
    }

    const form = $("#loginForm");
    if (!form) {
        return;
    }

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const username = $("#username").value.trim() || "演示用户";
        const password = $("#password").value.trim();
        const role = $("#role").value;
        if (!password) {
            alert("请输入密码后再登录。");
            return;
        }
        setSession({
            username,
            role,
            entry: isMobile ? "mobile" : "desktop"
        });
        const state = getState();
        state.project.owner = username;
        state.project.role = role;
        saveState(state);
        goTo(isMobile ? routes.mobileHome : routes.dashboard);
    });
}

function renderDashboard() {
    const state = getState();
    const stats = {
        projects: 1,
        pending: state.agents.filter((agent) => !agent.status.includes("完成")).length,
        docs: state.documents.length,
        submissions: state.submissions.length
    };
    setText("#statProjects", String(stats.projects));
    setText("#statPending", String(stats.pending));
    setText("#statDocs", String(stats.docs));
    setText("#statSubmissions", String(stats.submissions));

    setText("#projectName", state.project.name);
    setText("#projectPriority", state.project.priority);
    setText("#projectPhase", state.project.phase);
    setText("#projectTarget", state.project.target);

    const timeline = $("#recentTimeline");
    if (timeline) {
        timeline.innerHTML = [
            `已载入项目：${state.project.name}`,
            `当前阶段：${state.project.phase}`,
            `最新文档版本：${state.documents[0].version}`,
            `最近提交状态：${state.submissions[0].status}`
        ]
            .map(
                (item) => `
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <div class="timeline-content">${escapeHtml(item)}</div>
                </div>`
            )
            .join("");
    }
}

function renderAnalysis() {
    const state = getState();
    const summary = $("#analysisSummary");
    const modules = $("#analysisModules");
    const risks = $("#analysisRisks");
    const recommendations = $("#analysisRecommendations");

    if (summary) {
        summary.innerHTML = state.analysis.summary.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    }
    if (modules) {
        modules.innerHTML = state.analysis.modules.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    }
    if (risks) {
        risks.innerHTML = state.analysis.risks.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    }
    if (recommendations) {
        recommendations.innerHTML = state.analysis.recommendations.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    }

    setText("#analysisProjectName", state.project.name);
    setText("#analysisCurrentTarget", state.project.target);
}

function initAnalysisPage() {
    const state = getState();
    $("#projectNameInput").value = state.project.name;
    $("#descriptionInput").value = state.project.description;
    $("#targetInput").value = state.project.target;
    $("#priorityInput").value = state.project.priority;
    renderAnalysis();

    const form = $("#analysisForm");
    if (!form) {
        return;
    }

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const payload = {
            projectName: $("#projectNameInput").value.trim() || state.project.name,
            description: $("#descriptionInput").value.trim(),
            target: $("#targetInput").value.trim(),
            priority: $("#priorityInput").value,
            docType: $("#docTypeInput").value
        };

        const analysis = buildAnalysisPayload(payload);
        const nextState = getState();
        nextState.project = {
            ...nextState.project,
            name: payload.projectName,
            description: payload.description,
            target: payload.target,
            priority: payload.priority,
            phase: "文档生成中"
        };
        nextState.analysis = analysis;
        nextState.documents = buildDocuments(payload.projectName, analysis);
        nextState.testCases = buildTestCases(payload.projectName);
        nextState.messages = buildMessages(payload.projectName);
        nextState.agents = buildAgents();
        saveState(nextState);
        renderAnalysis();
        setText("#analysisFeedback", "分析完成，已更新文档中心、Agent协作和测试用例数据。");
    });

    const nextButton = $("#analysisNextButton");
    if (nextButton) {
        nextButton.addEventListener("click", () => goTo(routes.agents));
    }
}

function initDrgPage() {
    const state = getState();
    const container = $("#drgCaseList");
    if (!container) {
        return;
    }
    container.innerHTML = state.drgCases
        .map(
            (item) => `
            <div class="doc-item">
                <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:8px;">
                    <div>
                        <h4>${escapeHtml(item.id)} · ${escapeHtml(item.patient)}</h4>
                        <p>${escapeHtml(item.diagnosis)}</p>
                    </div>
                    <span class="tag ${statusClass(item.status)}">${escapeHtml(item.status)}</span>
                </div>
                <div class="kv-list">
                    <div class="kv-item"><strong>DRG分组</strong><span>${escapeHtml(item.drg)}</span></div>
                    <div class="kv-item"><strong>风险等级</strong><span>${escapeHtml(item.risk)}</span></div>
                    <div class="kv-item"><strong>说明</strong><span>${escapeHtml(item.note)}</span></div>
                </div>
            </div>`
        )
        .join("");
    setText("#drgCaseCount", String(state.drgCases.length));
}

function initAgentsPage() {
    const state = getState();
    const agentList = $("#agentList");
    const messageList = $("#messageList");
    const detailList = $("#agentDetailList");

    if (agentList) {
        agentList.innerHTML = state.agents
            .map(
                (item) => `
                <div class="agent-item">
                    <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:10px;">
                        <div>
                            <h4>${escapeHtml(item.name)}</h4>
                            <p>${escapeHtml(item.owner)}</p>
                        </div>
                        <span class="agent-status ${statusClass(item.status)}">${escapeHtml(item.status)}</span>
                    </div>
                    <p>${escapeHtml(item.focus)}</p>
                </div>`
            )
            .join("");
    }

    if (messageList) {
        messageList.innerHTML = state.messages
            .map(
                (item) => `
                <div class="message-item">
                    <div style="display:flex;justify-content:space-between;gap:12px;margin-bottom:8px;">
                        <h4>${escapeHtml(item.from)} → ${escapeHtml(item.to)}</h4>
                        <span class="tag">${escapeHtml(item.time)}</span>
                    </div>
                    <p>${escapeHtml(item.content)}</p>
                </div>`
            )
            .join("");
    }

    if (detailList) {
        detailList.innerHTML = `
            <div class="doc-item">
                <h4>当前项目</h4>
                <p>${escapeHtml(state.project.name)}</p>
            </div>
            <div class="doc-item">
                <h4>当前阶段</h4>
                <p>${escapeHtml(state.project.phase)}</p>
            </div>
            <div class="doc-item">
                <h4>目标产物</h4>
                <p>${escapeHtml(state.project.target)}</p>
              </div>`;
    }

    const docButton = $("#goDocumentsButton");
    if (docButton) {
        docButton.addEventListener("click", () => goTo(routes.documents));
    }
    const docButtonBottom = $("#goDocumentsButtonBottom");
    if (docButtonBottom) {
        docButtonBottom.addEventListener("click", () => goTo(routes.documents));
    }
}

function renderDocumentPreview(docId) {
    const state = getState();
    const docs = state.documents;
    const current = docs.find((item) => item.id === docId) || docs[0];
    const title = $("#docPreviewTitle");
    const meta = $("#docPreviewMeta");
    const content = $("#docPreviewContent");
    if (title) {
        title.textContent = current.title;
    }
    if (meta) {
        meta.textContent = `${current.version} · ${current.updatedAt} · ${current.status}`;
    }
    if (content) {
        content.innerHTML = current.content.map((line) => `<div class="timeline-content">${escapeHtml(line)}</div>`).join("");
    }
    $$(".tab-button").forEach((button) => {
        button.classList.toggle("active", button.dataset.docId === current.id);
    });
}

function initDocumentsPage() {
    const state = getState();
    const docList = $("#docList");
    if (docList) {
        docList.innerHTML = state.documents
            .map(
                (item) => `
                <div class="doc-item">
                    <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:8px;">
                        <div>
                            <h4>${escapeHtml(item.title)}</h4>
                            <p>${escapeHtml(item.version)} · ${escapeHtml(item.updatedAt)}</p>
                        </div>
                        <span class="tag ${statusClass(item.status)}">${escapeHtml(item.status)}</span>
                    </div>
                    <div class="tab-row">
                        <button class="tab-button" type="button" data-doc-id="${escapeHtml(item.id)}">预览</button>
                    </div>
                </div>`
            )
            .join("");
        $$(".tab-button").forEach((button) => {
            button.addEventListener("click", () => renderDocumentPreview(button.dataset.docId));
        });
        renderDocumentPreview(state.documents[0].id);
    }

    const testsButton = $("#goTestsButton");
    if (testsButton) {
        testsButton.addEventListener("click", () => goTo(routes.tests));
    }
}

function initTestsPage() {
    const state = getState();
    const body = $("#testTableBody");
    if (!body) {
        return;
    }
    body.innerHTML = state.testCases
        .map(
            (item) => `
            <tr>
                <td>${escapeHtml(item.id)}</td>
                <td>${escapeHtml(item.feature)}</td>
                <td>${escapeHtml(item.precondition)}</td>
                <td>${escapeHtml(item.steps)}</td>
                <td>${escapeHtml(item.expected)}</td>
                <td><span class="tag ${statusClass(item.priority)}">${escapeHtml(item.priority)}</span></td>
            </tr>`
        )
        .join("");

    const regenerateButton = $("#regenerateTestsButton");
    if (regenerateButton) {
        regenerateButton.onclick = () => {
            const nextState = getState();
            nextState.testCases = buildTestCases(nextState.project.name);
            saveState(nextState);
            initTestsPage();
        };
    }

    const submitButton = $("#goSubmitButton");
    if (submitButton) {
        submitButton.addEventListener("click", () => goTo(routes.submit));
    }
}

function initSubmitPage() {
    const state = getState();
    const docChecklist = $("#submitChecklist");
    const history = $("#submitHistory");

    if (docChecklist) {
        docChecklist.innerHTML = state.documents
            .map(
                (item) => `
                <label class="submit-item" style="display:flex;justify-content:space-between;gap:12px;align-items:center;">
                    <span>
                        <strong>${escapeHtml(item.title)}</strong>
                        <span style="display:block;color:var(--text-soft);margin-top:6px;">${escapeHtml(item.version)} · ${escapeHtml(item.status)}</span>
                    </span>
                    <input type="checkbox" checked />
                </label>`
            )
            .join("");
    }

    if (history) {
        history.innerHTML = state.submissions
            .map(
                (item) => `
                <div class="submit-item">
                    <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:8px;">
                        <div>
                            <h4>${escapeHtml(item.batch)}</h4>
                            <p>${escapeHtml(item.submittedAt)} · ${escapeHtml(item.operator)}</p>
                        </div>
                        <span class="tag ${statusClass(item.status)}">${escapeHtml(item.status)}</span>
                    </div>
                    <p>文档数：${escapeHtml(item.docs)}，批次编号：${escapeHtml(item.id)}</p>
                </div>`
            )
            .join("");
    }

    const submitButton = $("#submitButton");
    if (submitButton) {
        submitButton.onclick = () => {
            const nextState = getState();
            nextState.submissions.unshift({
                id: `SUB-${String(nextState.submissions.length + 1).padStart(3, "0")}`,
                batch: `${nextState.project.name} 提交批次`,
                status: "已提交",
                submittedAt: formatNow(),
                docs: nextState.documents.length,
                operator: getSession()?.username || nextState.project.owner
            });
            nextState.project.phase = "已提交待审核";
            nextState.documents = nextState.documents.map((item) => ({ ...item, status: "已提交" }));
            saveState(nextState);
            initSubmitPage();
            setText("#submitFeedback", "提交成功，工作台与移动端状态已同步更新。");
        };
    }
}

function initMobileHomePage() {
    const state = getState();
    setText("#mobileOwner", state.project.owner);
    setText("#mobileProjectName", state.project.name);
    setText("#mobilePhase", state.project.phase);
    setText("#mobileDocCount", String(state.documents.length));
    setText("#mobileMessageCount", String(state.messages.length));
    setText("#mobileSubmissionCount", String(state.submissions.length));

    const taskList = $("#mobileTaskList");
    if (taskList) {
        taskList.innerHTML = [
            `查看最新文档版本：${state.documents[0].version}`,
            `当前处理阶段：${state.project.phase}`,
            `最近上报：${state.mobileReports[0]?.title || "暂无"}`
        ]
            .map((item) => `<div class="mobile-list-item"><p>${escapeHtml(item)}</p></div>`)
            .join("");
    }
}

function initMobileReportPage() {
    const form = $("#mobileReportForm");
    const state = getState();
    $("#mobileReportProject").value = state.project.name;
    if (!form) {
        return;
    }
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const title = $("#mobileReportTitle").value.trim();
        const content = $("#mobileReportContent").value.trim();
        const priority = $("#mobileReportPriority").value;
        if (!title || !content) {
            alert("请完整填写上报标题和内容。");
            return;
        }
        const nextState = getState();
        nextState.mobileReports.unshift({
            title,
            content,
            priority,
            createdAt: formatNow()
        });
        nextState.messages.unshift({
            from: "移动端上报",
            to: "需求分析 Agent",
            content: `${title}：${content}`,
            time: formatNow().slice(11)
        });
        nextState.project.phase = "收到移动端上报";
        saveState(nextState);
        setText("#mobileReportFeedback", "上报成功，PC端Agent消息流已同步新增一条记录。");
        form.reset();
        $("#mobileReportProject").value = nextState.project.name;
    });
}

function initMobileMessagesPage() {
    const state = getState();
    const list = $("#mobileMessageList");
    if (!list) {
        return;
    }
    list.innerHTML = state.messages
        .map(
            (item) => `
            <div class="mobile-list-item">
                <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:8px;">
                    <h4>${escapeHtml(item.from)}</h4>
                    <span class="mobile-tag">${escapeHtml(item.time)}</span>
                </div>
                <p>${escapeHtml(item.content)}</p>
            </div>`
        )
        .join("");
}

function initMobileDocsPage() {
    const state = getState();
    const docs = $("#mobileDocList");
    const history = $("#mobileSubmissionHistory");
    if (docs) {
        docs.innerHTML = state.documents
            .map(
                (item) => `
                <div class="mobile-list-item">
                    <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:8px;">
                        <h4>${escapeHtml(item.title)}</h4>
                        <span class="mobile-tag ${statusClass(item.status)}">${escapeHtml(item.status)}</span>
                    </div>
                    <p>${escapeHtml(item.version)} · ${escapeHtml(item.updatedAt)}</p>
                </div>`
            )
            .join("");
    }
    if (history) {
        history.innerHTML = state.submissions
            .slice(0, 3)
            .map(
                (item) => `
                <div class="mobile-list-item">
                    <h4>${escapeHtml(item.batch)}</h4>
                    <p>${escapeHtml(item.submittedAt)} · ${escapeHtml(item.status)}</p>
                </div>`
            )
            .join("");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const page = document.body.dataset.page;
    requireAuth(page);
    bindGlobalActions();

    switch (page) {
        case "index":
            initLandingPage();
            break;
        case "login":
            initLoginPage(false);
            break;
        case "dashboard":
            renderDashboard();
            break;
        case "analysis":
            initAnalysisPage();
            break;
        case "drg":
            initDrgPage();
            break;
        case "agents":
            initAgentsPage();
            break;
        case "documents":
            initDocumentsPage();
            break;
        case "tests":
            initTestsPage();
            break;
        case "submit":
            initSubmitPage();
            break;
        case "mobile-login":
            initLoginPage(true);
            break;
        case "mobile-home":
            initMobileHomePage();
            break;
        case "mobile-report":
            initMobileReportPage();
            break;
        case "mobile-messages":
            initMobileMessagesPage();
            break;
        case "mobile-docs":
            initMobileDocsPage();
            break;
        default:
            break;
    }
});
