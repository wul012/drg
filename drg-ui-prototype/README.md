# 医保DRG智能协同平台原型

这是一个可直接在 PyCharm 中打开并运行的课程实验二原型项目。

## 运行方式

### 方式一：直接运行 Python 启动脚本

1. 用 PyCharm 打开项目目录 `d:\C\drg-ui-prototype`
2. 右键运行 `run_server.py`
3. 浏览器会自动打开 `http://127.0.0.1:8000/index.html`

### 方式二：使用命令行运行

```bash
python run_server.py
```

## 项目结构

- `index.html`：项目首页，提供 PC 端和移动端入口
- `pages/login.html`：PC 端登录页
- `pages/dashboard.html`：工作台首页
- `pages/analysis.html`：需求分析页
- `pages/drg.html`：DRG 规则匹配页
- `pages/agents.html`：多 Agent 协作页
- `pages/documents.html`：文档中心
- `pages/tests.html`：测试用例中心
- `pages/submit.html`：提交中心
- `pages/mobile-*.html`：移动端页面
- `css/style.css`：全局样式
- `js/main.js`：交互逻辑与本地数据联动
- `run_server.py`：本地启动脚本

## 已实现功能

- PC 端登录与工作台展示
- 需求分析结果生成
- DRG 病例与规则匹配展示
- 多 Agent 协作与消息流
- 文档预览与测试用例展示
- 提交中心与提交记录
- 移动端需求上报、消息查看与文档查看
- 使用浏览器本地存储保存演示数据
