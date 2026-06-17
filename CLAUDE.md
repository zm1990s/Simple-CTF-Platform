# CLAUDE.md — 项目记忆

> 本文件供 AI 协作者（Claude / Cursor / Copilot 等）阅读，定义本仓库的身份、技术栈、约定与禁忌，作为每次对话开始时的"硬上下文"。

## 1. 身份 / Identity

- **项目名**：Simple CTF Platform（简称 CTF Platform）
- **类型**：自托管的 Capture The Flag 竞赛平台
- **形态**：Python Flask 单体应用 + PostgreSQL + Redis + Celery worker；通过 Docker Compose 或 Kubernetes 部署
- **语言**：界面与文档以**中英双语**为主（zh / en），数据库与日志使用 UTC
- **目标用户**：
  - **管理员**：举办 CTF 比赛，创建竞赛与题目，审核提交
  - **参赛用户**：注册账号、加入战队、答题、查看排行榜
- **核心特色**：
  - 富文本（Markdown + 图片）题目
  - 提交可由人工审核，或经由 **Dify 工作流**自动评分
  - 支持**全局 Dify** 与**题目级 Dify**（带独立 API Key）
  - 竞赛 **PIN 码**访问控制
  - 个人榜 + 战队榜双视角
  - 竞赛 / 题目 JSON 导出导入

## 2. 技术栈 / Tech Stack

### 后端
- Python 3.11+
- **Flask 3.0** + 蓝图（auth / frontend / admin / api / teams）
- **Flask-SQLAlchemy 3.1**（ORM） / **Flask-Migrate 4.0**（Alembic）
- **Flask-Login 0.6**（会话认证）
- **Flask-WTF 1.2 + WTForms 3.1**（表单）
- **Flask-Babel 4.0** + 自维护的 `translations.json`（中英文）
- **Celery 5.3 + Redis 5**（异步任务，目前只跑 `trigger_external_hook`）
- **Werkzeug** 密码哈希、**Pillow** 图片处理、**markdown2** 渲染
- **requests** 调 Dify HTTP API

### 数据 / 基础设施
- PostgreSQL 15（主库）
- Redis 7（Celery broker + result backend）
- Gunicorn（生产 WSGI，4 worker）
- Docker / Docker Compose / Kubernetes（`k8s-deployment.yaml`）

### 前端
- Bootstrap 5 + Jinja2 模板（无 SPA 框架）
- Marked.js（前端 Markdown 预览）

### 测试
- `pytest`（位于 `tests/`，3 个测试文件，整体覆盖率有限）

## 3. 仓库结构 / Layout

```
.
├── app.py                  Application Factory + 蓝图注册 + Babel + 默认管理员/设置
├── wsgi.py                 Gunicorn 入口
├── config.py               Config / DevelopmentConfig / ProductionConfig
├── models.py               全部 ORM 模型（单文件，14 张表）
├── forms.py                WTForms 定义
├── tasks.py                Celery 任务（Dify 自动评分）
├── dify_secrets.py         Dify API Key 加解密 / 打码
├── init_db.py              首次启动建表 + 默认数据
├── translations.json       i18n 词条（zh / en）
├── routes/
│   ├── auth.py             /auth/*            登录 / 注册 / 改密 / 切语言
│   ├── frontend.py         /                  竞赛、题目、提交、PIN、排行榜
│   ├── admin.py            /admin/*           管理后台（最大文件，~1064 行）
│   ├── api.py              /api/*             JSON 接口（排行榜、统计）
│   └── teams.py            /teams/*           组队（创建、加入、退出、踢人）
├── templates/              Jinja2（base + auth/admin/frontend/teams 4 子目录）
├── static/                 style.css / logo
├── uploads/                运行期生成的用户上传文件
├── tests/                  pytest
└── docs/                   补充文档（quickstart / commands / migrations / export-import / CHANGELOG）
```

完整路由清单与契约见 [DESIGN.md](DESIGN.md)。

## 4. 关键业务约定 / Domain Rules

> 这一节是**最容易被改坏**的部分，修改前请先阅读。

### 提交与计分
- 同一用户对同一题目允许**多次提交**，所有记录都保留。
- 排行榜**只计每题最高分**（`MAX(points_awarded) GROUP BY user_id, challenge_id` 后再 `SUM`）。
- 排序规则：`总分 DESC, 最后解题时间 ASC`（同分先到者靠前）。
- 提交状态机：`pending → approved | rejected`，由人工或 Dify 推动。
- `reviewed_by_name = 'AI'` 表示 Dify 自动审核；`reviewed_by_id` 为 None。

### Dify 自动审核协议
Dify 工作流必须在 `answer` 字段返回 JSON 字符串：

```json
{ "success": bool, "score": int, "feedback": str, "auto_approved": bool }
```

- `auto_approved=true` + `success=true` → 自动 `approved`，得分取 `score`
- `auto_approved=true` + `success=false` → 自动 `rejected`，得分 0
- `auto_approved=false` → 保持 `pending`，等待人工审核
- 题目级 `ChallengeDifyConfig.enabled=True` 时优先使用题目级 Hook URL + API Key，否则回退全局 `EXTERNAL_HOOK_URL` / `DIFY_API_KEY`。
- API Key 不直接落库，存的是经 `dify_secrets.obfuscate_api_key` 加密后的 `api_key_token`，加上脱敏的 `api_key_masked` 用于展示。

### 竞赛状态机
`draft → running → paused → stopped`，可被 admin 在后台切换。
- `running` 才接受提交；`paused` 可见但不可提交；`draft` / `stopped` 对普通用户隐藏。
- `countdown_minutes` + `countdown_started_at` 实现倒计时，到点自动转 `paused`。

### PIN 码访问控制
- 每个 `Competition` 都有 6 位数字 `pin`（创建时自动生成，可重置）。
- 普通用户首次进入 `/competition/<id>/...` 时，未在 `competition_access` 表登记会被强制跳转到 `/competition/<id>/pin`。
- PIN 校验通过即写入 `CompetitionAccess`，会话内不再要求。
- **管理员永远跳过 PIN 校验**。

### 组队
- 一个用户**至多归属一个战队**（`team_members.user_id` 唯一约束）。
- 战队榜上：**用户加入战队后从个人榜消失**（避免双重计分），战队总分 = 战队内每题最高分之和。
- 队长退出时若还有成员，队长自动转给最早加入者；若是最后一人，战队自动解散。

### 题目顺序
- `Challenge.order_index`（默认 0）控制前台显示顺序，越小越靠前；同值再按 `id` 升序。
- 克隆 / 导入 / 导出竞赛时**必须保留** `order_index`。

## 5. 配置与运行 / Config & Runtime

- 所有可调项通过环境变量（`.env`）注入，参考 `.env.example` 与 `config.py`。
- 关键变量：`SECRET_KEY` / `DATABASE_URL` / `REDIS_URL` / `EXTERNAL_HOOK_*` / `DIFY_API_KEY` / `UPLOAD_URL_PREFIX` / `ADMIN_EMAIL` / `ADMIN_PASSWORD`。
- 启动方式：
  - 一键：`./deploy.sh` →  `docker compose up -d --build`
  - 手动：`python init_db.py && python app.py` + `celery -A tasks.celery worker`
- 默认 admin：`admin@ctf.local / admin123`（`app.py:create_default_admin`），首次登录后必须改密。
- 所有时间在数据库里以 UTC 存储；前端展示由模板按本地化处理。

## 6. 风格与禁忌 / Style & Don'ts

- **不要把 API Key、PIN 等明文存进数据库**。Dify Key 走 `dify_secrets.py` 加解密；竞赛 PIN 是 6 位数字、可由管理员重置但不参与排行榜计分。
- **不要绕过 PIN / 战队约束直接 SQL 改库**。这些规则在路由层校验，绕过会让排行榜错乱。
- **不要在 `celery worker` 里直接 `import app`**：使用 `from app import create_app` 拿 app context，避免 SQLAlchemy 实例错位。
- **路由分布要稳定**：现有 URL 已有外部链接（导出文件、邮件提示等）依赖。新增 URL 优先而非重命名旧的。
- **前端模板里所有用户可见文本走 `_('...')` 翻译函数**；新增文案需同步加进 `translations.json` 的 zh / en 两侧。
- **新增模型字段时同步更新**：导入导出（`routes/admin.py` 的 `competition_export` / `competition_import` / `competitions_export_all` / `competition_duplicate`）和 `models.py` 的 `__repr__` / 关系定义。
- **不要把"运行期数据"提交进 git**：`uploads/`、`data/`（PostgreSQL 数据卷）、`__pycache__/`、`.env`。
- **测试 / 文档**：`docs/CHANGELOG.md` 记录用户可见变更；其他实现细节文档**不再保留**，请直接读代码。

## 7. AI 协作守则 / How to Work in This Repo

1. **先读 [DESIGN.md](DESIGN.md)**：所有 URL、数据流、外部契约都在那里。
2. 改动需要数据库结构时：用 Flask-Migrate 生成迁移脚本，更新 `models.py`，然后在 PR / 回复里说明对存量数据的影响（是否需 backfill、是否破坏导入旧 JSON）。
3. 改动 Dify 协议时：同步更新 [README.md](README.md) 的 Dify 章节、[DESIGN.md](DESIGN.md) 的 Dify 契约表，以及 `docs/CHANGELOG.md`。
4. 写代码默认遵循现有风格：4 空格缩进、`snake_case`、Flask 蓝图、`db.relationship` + `cascade='all, delete-orphan'`。
5. 不引入未在 `requirements.txt` 中的依赖；引入前确认包是否真的需要（项目体量不大，慎加运行时依赖）。
6. 涉及"自动行为"或"快捷指令"时：本仓库**没有**任何 hook / cron / 后台守护进程，除了 Celery worker。请勿假设。
