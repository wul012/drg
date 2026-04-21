# 医保DRG智能协同平台

这是一个基于 `Flask + SQLite` 的完整课程项目，不再是纯静态原型。

项目覆盖：

- 桌面端工作台
- 需求分析与数据库写入
- DRG 病例与规则匹配展示
- 多 Agent 协作消息流
- 文档中心
- 测试用例中心
- 提交中心与提交记录
- 响应式移动端页面

## 本地微型LLM能力

项目内置了一个纯 Python 实现的本地微型LLM，不依赖任何外部 API。

- 主要展示点：DRG 入组原因说明
- 联动场景：需求分析、文档正文、测试用例文案
- 模式切换：需求分析页可切换 `严谨模式 / 平衡模式 / 增强模式`
- 外部语料文件：`local_llm_corpus.json`

其中：

- `local_llm.py` 负责本地语料加载、n-gram 风格生成和模式控制
- `local_llm_corpus.json` 可直接编辑，用于扩充四类生成语料

## 运行前准备

当前项目依赖 `Flask`。

先在项目目录执行：

```bash
pip install -r requirements.txt
```

## 运行方式

### 方式一：PyCharm 中直接运行

1. 用 PyCharm 打开项目目录 `d:\C\drg-ui-prototype`
2. 确保已经安装依赖：`pip install -r requirements.txt`
3. 右键运行 `run_server.py`
4. 浏览器会自动打开 `http://127.0.0.1:5000`

### 方式二：命令行运行

```bash
python run_server.py
```

## 数据库位置

项目运行后会自动生成 SQLite 数据库：

```text
instance/drg_platform.db
```

如果你在 PyCharm 中连接数据库，请选择这个文件，而不是旧的示例库文件。

## 默认演示账号

- `admin / 123456`
- `doctor / 123456`
- `analyst / 123456`

## 项目结构

- `app.py`：Flask 主应用，包含路由、数据库初始化和业务逻辑
- `local_llm.py`：本地微型LLM模块，负责原因说明、分析、文档和测试文案生成
- `local_llm_corpus.json`：本地微型LLM扩展语料文件
- `run_server.py`：本地启动脚本
- `requirements.txt`：Python 依赖
- `smoke_test.py`：基础回归测试脚本
- `tests/test_local_llm.py`：本地微型LLM专项测试
- `templates/`：Jinja2 模板
- `static/css/style.css`：完整项目样式
- `static/js/app.js`：前端交互脚本
- `instance/drg_platform.db`：运行后自动生成的 SQLite 数据库

## 已实现功能

- 用户登录与注册
- 项目数据持久化到 SQLite
- 需求分析表单与分析结果刷新
- DRG 病例展示与本地微型LLM原因说明
- 多 Agent 协作状态与消息流
- 文档中心和本地微型LLM增强文档预览
- 测试用例重生成与模式化文案输出
- 提交中心与提交记录留痕
- 响应式移动端首页、上报、消息和文档页面
- 本地微型LLM模式切换与外部语料扩展

## 回归测试

可以直接运行以下命令验证主流程和关键校验：

```bash
python tests/test_local_llm.py
python tests/test_drg_rules.py
python smoke_test.py
```

脚本会自动验证：首页访问、登录、需求分析模式切换、DRG 入组、本地微型LLM 文案生成、提交中心和移动端上报。

## 兼容说明

- 根目录旧的 `index.html` 已改为跳转说明页，用于避免误打开旧原型入口。
- `pages/`、`css/`、`js/` 等旧原型目录仅保留作历史兼容，不参与 Flask 正式运行。
- 正式项目只依赖：`app.py`、`run_server.py`、`templates/`、`static/`、`instance/`。
