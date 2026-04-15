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
- `run_server.py`：本地启动脚本
- `requirements.txt`：Python 依赖
- `smoke_test.py`：基础回归测试脚本
- `templates/`：Jinja2 模板
- `static/css/style.css`：完整项目样式
- `static/js/app.js`：前端交互脚本
- `instance/drg_platform.db`：运行后自动生成的 SQLite 数据库

## 已实现功能

- 用户登录与注册
- 项目数据持久化到 SQLite
- 需求分析表单与分析结果刷新
- DRG 病例展示
- 多 Agent 协作状态与消息流
- 文档中心和文档预览
- 测试用例重生成
- 提交中心与提交记录留痕
- 响应式移动端首页、上报、消息和文档页面

## 回归测试

可以直接运行以下命令验证主流程和关键校验：

```bash
python smoke_test.py
```

脚本会自动验证：首页访问、登录、注册校验、需求分析、提交中心和移动端上报。

## 兼容说明

- 根目录旧的 `index.html` 已改为跳转说明页，用于避免误打开旧原型入口。
- `pages/`、`css/`、`js/` 等旧原型目录仅保留作历史兼容，不参与 Flask 正式运行。
- 正式项目只依赖：`app.py`、`run_server.py`、`templates/`、`static/`、`instance/`。
