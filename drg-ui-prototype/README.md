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

## 模板化文案生成

项目当前使用确定性的模板字符串生成说明文本，不伪装成本地 LLM，也不依赖任何外部 API。

- 主要展示点：DRG 入组原因说明
- 联动场景：需求分析、文档正文、测试用例文案
- 模式切换：需求分析页可切换 `严谨模式 / 平衡模式 / 展示模式`

其中：

- `template_generation.py` 负责原因说明、需求分析、文档和测试用例的模板化文案生成
- DRG 入组说明按“主诊断 -> MDC、主手术 -> ADRG、次诊断 -> MCC/CC、最终 DRG”的固定路径拼接

## 运行前准备

当前项目依赖 `Flask`。

如果是从 GitHub 克隆项目，建议按下面步骤配置：

```bash
git clone https://github.com/wul012/drg.git
cd drg/drg-ui-prototype
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_server.py
```

macOS / Linux 激活虚拟环境时使用：

```bash
source venv/bin/activate
```

如果已经在项目目录中，只需要先安装依赖：

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

## 页面操作指南

第一次打开系统不知道怎么操作时，请先看：

```text
docs/页面操作指南.md
```

这份指南按页面说明了登录、需求分析、DRG 入组、文档下载、测试用例、提交中心和移动端上报的具体点击路径与示例数据。

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
- `drg_case_utils.py`：病例筛选、分页、排序和分布统计辅助函数
- `template_generation.py`：模板化文案生成模块，负责原因说明、分析、文档和测试文案生成
- `run_server.py`：本地启动脚本
- `requirements.txt`：Python 依赖
- `smoke_test.py`：基础回归测试脚本
- `tests/test_template_generation.py`：模板文案生成专项测试
- `docs/页面操作指南.md`：面向首次使用者的页面点击与演示说明
- `templates/`：Jinja2 模板
- `static/css/style.css`：完整项目样式
- `static/js/app.js`：前端交互脚本
- `instance/drg_platform.db`：运行后自动生成的 SQLite 数据库

## 已实现功能

- 用户登录与注册
- 项目数据持久化到 SQLite
- 需求分析表单与分析结果刷新
- DRG 病例展示与模板化原因说明
- 多 Agent 协作状态与消息流
- 文档中心和模板化文档预览
- 测试用例重生成与模式化文案输出
- 提交中心与提交记录留痕
- 响应式移动端首页、上报、消息和文档页面
- 模板文案模式切换

## 回归测试

可以直接运行以下命令验证主流程和关键校验：

```bash
python tests/test_template_generation.py
python tests/test_drg_rules.py
python tests/test_case_helpers.py
python tests/test_drg_json_examples.py
python smoke_test.py
```

脚本会自动验证：首页访问、登录、需求分析模式切换、DRG 入组、JSON 样例分组、无编码样例自动补码、病例筛选分页、模板文案生成、提交中心和移动端上报。

## 兼容说明

- 根目录旧的 `index.html` 已改为跳转说明页，用于避免误打开旧原型入口。
- `pages/`、`css/`、`js/` 等旧原型目录仅保留作历史兼容，不参与 Flask 正式运行。
- 正式项目只依赖：`app.py`、`common.py`、`data_services.py`、`drg_case_utils.py`、`drg_rules.py`、`template_generation.py`、`storage.py`、`platform_config.py`、`run_server.py`、`templates/`、`static/`、`CHS_DRG_20/`。
- `instance/` 会在首次运行时自动创建，数据库、虚拟文档和提交清单也会自动生成。
