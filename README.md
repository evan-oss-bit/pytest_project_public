# PyTestTool

PyTestTool 是一个基于 Flask + Vue 的 pytest 自动化测试管理平台，用于管理脚本项目、业务部门、用例、测试集、测试任务、执行结果和测试报告。

## 项目定位

这是一个面向企业内部测试团队的 pytest 测试平台、自动化测试平台和测试工具项目，可用于接口自动化测试、UI 自动化测试、pytest 用例管理、测试集自由编排、定时任务执行、失败重跑、测试报告预览、日志查看和账号权限控制。适合作为接口自动化测试框架、UI 自动化测试框架、pytest 自动化测试框架或测试管理平台的二次开发基础。

关键词：pytest测试平台、测试平台、pytest工具、接口自动化测试框架、自动化测试框架、UI自动化测试框架、自动化测试平台、测试管理平台、pytest用例管理、测试报告平台。

## 页面截图

### 脚本项目列表

![脚本项目列表](vue_pytest_tool/docs/screenshots/project-list.png)

### 用例列表

![用例列表](vue_pytest_tool/docs/screenshots/case-list.png)

### 测试任务列表

![测试任务列表](vue_pytest_tool/docs/screenshots/test-task.png)

### 测试报告列表

![测试报告列表](vue_pytest_tool/docs/screenshots/report-list.png)

## 功能概览

- 脚本项目管理：项目列表、项目总览、项目文件预览、脚本扫描/同步、配置检查。
- 业务部门管理：维护业务部门，并将脚本项目归属到对应部门。
- 用例管理：从 pytest 脚本扫描用例，支持源码预览和在线维护。
- 测试集/测试任务：支持自由编排、排序、定时任务、失败重跑、运行历史和执行时间线。
- 测试报告：报告列表、详情抽屉、在线预览、日志高亮、统计摘要和趋势信息。
- 账号权限：管理员账号、项目账号、按脚本项目分配查看/编辑/运行权限，支持修改密码和重置密码。

## 目录结构

```text
pytest_project/
├─ flaskProject/       # 后端服务，Flask API、模型、执行逻辑、报告生成
│  └─ .env.example     # 后端环境变量示例
├─ vue_pytest_tool/    # 前端项目，Vue + Element UI
├─ .gitignore          # 忽略本地运行数据、日志、数据库、依赖目录
└─ README.md
```

首次启动时后端会自动创建 SQLite 数据库 `flaskProject/db/database.db`，并初始化管理员账号。后续运行产生的数据库、日志、报告、缓存、`node_modules`、虚拟环境、SQLite WAL/SHM 文件和额外脚本项目工作目录不会提交到仓库。

## 环境要求

- Python 3.8
- Node.js 14.x / npm
- Redis：用于定时任务 job store
- Git

项目目前主要按 Python 3.8 虚拟环境运行。前端依赖包含 `node-sass@4.14.1`，建议使用 Node.js 14.x；Node.js 18/20 可能会出现依赖安装失败。

## 后端启动

```powershell
cd flaskProject
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

默认后端地址：

```text
http://127.0.0.1:5400
```

Swagger 地址：

```text
http://127.0.0.1:5400/traffic/apidocs/
```

生产入口：

```powershell
cd flaskProject
.\venv\Scripts\activate
python app.py
```

`production_server.py` 目前暂不作为推荐入口，待生产启动链路验证完成后再启用。

## 前端启动

```powershell
cd vue_pytest_tool
npm install
npm run dev
```

前端开发代理配置在：

```text
vue_pytest_tool/config/index.js
```

后端 API 基础地址在：

```text
vue_pytest_tool/src/api/api.js
```

## 新环境部署检查

别人从 GitHub 拉取项目后，需要先安装后端和前端依赖，不能直接跳过依赖安装。

当前仓库已经补齐了直接启动所需的关键文件：

- 后端依赖：`flaskProject/requirements.txt`
- 前端依赖：`vue_pytest_tool/package.json`、`vue_pytest_tool/package-lock.json`
- 运行目录占位：`db/logs/report/files/material/data/instance/testscriptproject` 等目录的 `.gitkeep`
- 示例脚本项目：`flaskProject/testscriptproject/testcenter_demo_new`
- 环境变量样例：`flaskProject/.env.example`

新机器还需要自己准备：

- Python 3.8 环境。当前项目主要按 Python 3.8 验证。
- Node.js 14.x / npm 6.x。老版 `node-sass` 对 Node 18/20 不友好。
- Git 命令行。脚本项目 Git 拉取功能依赖 `git` 在 PATH 中可用。
- Redis。定时任务 job store 依赖 Redis，默认 `127.0.0.1:6379`、DB `3`。不启动 Redis 时，普通页面和部分功能仍可打开，但后端会持续打印 Redis 连接失败日志，定时任务不可用。

推荐启动顺序：先启动 Redis，再启动后端 `python app.py`，最后启动前端 `npm run dev`。

后端：

```powershell
git clone https://github.com/evan-oss-bit/pytest_project_public.git
cd pytest_project\flaskProject
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

前端：

```powershell
cd pytest_project\vue_pytest_tool
npm install
npm run dev
```

已在 fresh clone 目录验证：

- 后端 `create_app()` 可以初始化。
- 运行目录会自动创建。
- 前端 `npm install` 可以恢复依赖。
- 前端 `npm run build` 退出码为 0。

## 配置说明

后端环境变量示例放在 `flaskProject/.env.example`。进入后端目录后，复制示例文件即可使用默认 SQLite 初始化库；如果要改 Redis、MySQL、邮件等配置，再按本地环境调整实际值：

```powershell
cd flaskProject
copy .env.example .env
```

常用环境变量：

- `PYTEST_TOOL_SECRET_KEY`
- `PYTEST_TOOL_DATABASE_URL`：默认留空，自动使用 `flaskProject/db/database.db`
- `PYTEST_TOOL_REDIS_HOST`
- `PYTEST_TOOL_REDIS_PORT`
- `PYTEST_TOOL_REDIS_DB`
- `PYTEST_TOOL_EMAIL_HOST`
- `PYTEST_TOOL_EMAIL_TOKEN`

??? `.env`?????????????????SQLite `*.db` / `*.db-wal` / `*.db-shm` ????????

## 运行目录

仓库中保留了以下空目录占位，方便新环境 clone 后直接启动：

```text
flaskProject/db/                 # SQLite 数据库目录
flaskProject/logs/               # 服务日志和用例日志
flaskProject/report/             # HTML 测试报告
flaskProject/testscriptproject/   # pytest 脚本项目根目录
flaskProject/files/              # 临时/导出文件
flaskProject/material/           # 物料目录
flaskProject/data/               # 本地数据目录
flaskProject/instance/           # Flask instance 目录
```

???????????????? `.gitignore` ?????? `.gitkeep` ???????????????????????

## 示例脚本项目

仓库内保留了一个可参考的 pytest 脚本项目：

```text
flaskProject/testscriptproject/testcenter_demo_new/
```

别人拉取代码后，可以在“脚本项目列表”点击“全部项目列表”，找到 `testcenter_demo_new` 并快捷新建脚本项目，然后执行“扫描/同步脚本”导入用例。

该示例项目包含前置/后置 fixture、公共模块、参数化用例、共享 token 示例、DEBUG/ERROR 日志，以及部分故意失败的断言，方便验证测试报告、失败趋势和日志展示效果。

## 默认账号

系统会自动初始化管理员账号。

```text
用户名：admin
初始密码：123456789
```

账号密码已使用哈希存储。管理员可以在“账号权限”页面维护账号，并将其他账号密码重置为初始密码。

