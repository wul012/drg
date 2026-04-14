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

## 默认演示账号

- `admin / 123456`
- `doctor / 123456`
- `analyst / 123456`

## 项目结构

- `app.py`：Flask 主应用，包含路由、数据库初始化和业务逻辑
- `run_server.py`：本地启动脚本
- `requirements.txt`：Python 依赖
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
