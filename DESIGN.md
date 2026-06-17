# DESIGN.md — 架构约束

> 本文件描述 Simple CTF Platform 的运行时架构、模块边界、HTTP / 任务 / 数据契约，是 [CLAUDE.md](CLAUDE.md) 的延伸。修改本仓库前请先读这里。

---

## 1. 运行时架构 / Runtime Architecture

```
                ┌───────────────────────────────────────────┐
                │              Browser (Bootstrap)          │
                │   - Auth pages / Frontend / Admin / API   │
                └────────────────┬──────────────────────────┘
                                 │ HTTPS (cookie session)
                                 ▼
            ┌────────────────────────────────────────────────┐
            │                Flask app (Gunicorn)            │
            │   blueprints: auth / frontend / admin / api    │
            │              / teams + /uploads/<f>            │
            │     Flask-Login · Flask-Babel · WTForms        │
            └──┬───────────────────────┬──────────────┬──────┘
               │                       │              │
       SQLAlchemy ORM              Celery .delay      requests.post
               │                       │              │
               ▼                       ▼              ▼
        ┌─────────────┐         ┌──────────┐   ┌──────────────────┐
        │ PostgreSQL  │         │  Redis   │   │  Dify workflow   │
        │ (14 tables) │◀────────┤ broker + │   │  /v1/chat-       │
        └─────────────┘  ORM ▲  │ result   │   │   messages       │
                              │ └──────────┘   └──────────────────┘
                              │      │
                              │      ▼
                              │ ┌──────────────────┐
                              └─┤  Celery worker   │
                                │  (tasks.celery)  │
                                │  trigger_external│
                                │  _hook(sub_id)   │
                                └──────────────────┘

Filesystem: ./uploads (bind-mount)  — 用户提交图片，由 web 与 celery 共享
```

### 关键流程

1. **用户提交**：`POST /challenge/<id>` → 写入 `submissions` + `submission_files` → 若启用 hook，`trigger_external_hook.delay(submission_id)`。
2. **Dify 回调**（同步阻塞，celery worker 内）：HTTP POST → 解析 `answer` JSON → 写 `submission_dify_logs` → 视 `auto_approved` / `success` 修改 `submissions.status` 与 `points_awarded`。
3. **排行榜查询**：纯只读 SQL（`MAX` per (user, challenge) → `SUM` per user），由 `routes/api.py:leaderboard_api` 与 `routes/frontend.py:leaderboard` 共享语义；战队榜在 `frontend.py:leaderboard` 中合并计算。
4. **PIN / 组队**：Flask 路由层强约束，没有任何任务侧检查。

---

## 2. 模块边界 / Module Boundaries

| 模块 | 职责 | 不该做的事 |
|---|---|---|
| `app.py` | Application Factory、扩展初始化、默认管理员 / 设置、Babel locale | 业务逻辑、路由实现 |
| `config.py` | 读取环境变量 → Config 类 | 任何业务计算 |
| `models.py` | 全部 ORM 模型 + 简单领域方法（如 `Competition.is_running()`） | 直接调外部 API、操作 Flask 上下文 |
| `forms.py` | WTForms 校验 | DB 查询、业务流转 |
| `routes/auth.py` | 注册 / 登录 / 改密 / 切语言 | 业务对象 |
| `routes/frontend.py` | 用户视角：竞赛 / 题目 / 提交 / PIN / 排行榜 / 我的提交 | 修改其他用户数据、管理员动作 |
| `routes/admin.py` | 管理员后台 CRUD + 审核 + 导入导出 | 普通用户可达的 URL（必须靠 `is_admin` 守卫） |
| `routes/api.py` | 给前端 JS / 第三方拉数据的只读 JSON 接口 | 写入操作 |
| `routes/teams.py` | 战队生命周期（创建 / 加入 / 退出 / 踢人 / 转移队长） | 计分逻辑、跨竞赛逻辑 |
| `tasks.py` | Celery 任务（目前只有 Dify 自动评分） | Web 请求 / 模板渲染 |
| `dify_secrets.py` | 对称加密 + 脱敏的 Dify Key 处理 | 任何业务逻辑 |
| `templates/` | Jinja2 视图，只调用 `url_for` / `_('...')` / 简单循环 | 直接执行 SQL（请通过路由传 context） |

> **新增功能时第一步**：判断它属于哪一层，避免把"业务规则"写进模板或把"模型方法"写进路由。

---

## 3. HTTP API 契约 / Route Contract

### 3.1 认证相关 `/auth/*`（`routes/auth.py`）

| Method | URL | 鉴权 | 说明 |
|---|---|---|---|
| GET / POST | `/auth/register` | 公开 | 邮箱 + 用户名注册；已登录跳转首页 |
| GET / POST | `/auth/login` | 公开 | 邮箱登录，禁用账号被拦截 |
| GET | `/auth/logout` | 已登录 | 清会话 |
| GET | `/auth/set-locale/<en|zh>` | 公开 | 写 session.locale |
| GET / POST | `/auth/change-password` | 已登录 | 必须先校验当前密码 |

### 3.2 前台 `/`（`routes/frontend.py`）

| Method | URL | 鉴权 | 说明 |
|---|---|---|---|
| GET | `/` | 公开 | 列出 `running` / `paused` 竞赛 |
| GET | `/competition/<id>` | 已登录 + PIN | 进入竞赛，列出 `is_active` 题目 |
| GET / POST | `/challenge/<id>` | 已登录 + PIN + 竞赛 running | 题目详情 + 提交（多图） |
| GET / POST | `/competition/<id>/pin` | 已登录 | PIN 校验页（管理员跳过） |
| GET | `/leaderboard/<comp_id>` | 公开 | 个人榜 + 战队榜（HTML） |
| GET | `/leaderboard/<comp_id>/team/<team_id>` | 公开 | 单战队详情（成员、各题最高分） |
| GET | `/my-submissions` | 已登录 | 我的提交列表 |
| GET | `/my-submissions/<sub_id>` | 仅本人 | 我的提交详情（含上传图片）— 越权 403 |
| GET | `/uploads/<filename>` | 公开（已知文件名） | 静态文件代理 |

### 3.3 组队 `/teams/*`（`routes/teams.py`）

| Method | URL | 鉴权 | 说明 |
|---|---|---|---|
| GET | `/teams` | 已登录 | 战队列表 |
| GET / POST | `/teams/create` | 已登录 + 未入队 | 创建战队 |
| GET | `/teams/my` | 已登录 + 已入队 | 我的战队 |
| POST | `/teams/join` | 已登录 + 未入队 | 邀请码加入 |
| POST | `/teams/leave` | 已登录 + 已入队 | 退出（队长会移交或解散） |
| POST | `/teams/<tid>/kick/<uid>` | 队长 | 踢人，403 if 非队长 |

### 3.4 管理员 `/admin/*`（`routes/admin.py`）

> 所有路由都需 `is_admin`。下表只列对外契约稳定的 URL，详细参数见 `forms.py` 与各路由实现。

| URL | 用途 |
|---|---|
| `GET /admin/` | 仪表盘 |
| `GET / POST /admin/settings` | 平台名 / Logo / Footer |
| `GET /admin/competitions` 及 `*/new`、`*/<id>/edit`、`*/<id>/delete` | 竞赛 CRUD |
| `POST /admin/competitions/<id>/{start,pause,stop,reset,reset-pin,duplicate}` | 状态机操作 |
| `GET /admin/competitions/<id>/export`<br>`GET /admin/competitions/export-all`<br>`GET / POST /admin/competitions/import` | JSON / ZIP 导入导出 |
| `GET /admin/challenges` 及 `*/new`、`*/<id>/edit`、`*/<id>/delete`、`*/<id>/toggle`、`*/<id>/copy` | 题目 CRUD |
| `POST /admin/challenges/<id>/move-{up,down}`、`POST /admin/challenges/reorder` | 顺序调整 |
| `GET /admin/challenges/<id>/export` | 导出单题 |
| `POST /admin/upload-image` | Markdown 编辑器图片上传 |
| `GET /admin/submissions` 及 `*/<id>/review` | 审核中心 |
| `GET /admin/users` 及 `*/<id>/{toggle-admin,toggle-disable,delete,reset-password}` | 用户管理 |
| `GET /admin/submission-history` 及 `*/<id>` | 历史提交（reset 后归档） |

### 3.5 JSON API `/api/*`（`routes/api.py`）

| Method | URL | 返回 |
|---|---|---|
| GET | `/api/leaderboard/<comp_id>` | `{competition: {id,name,is_running}, leaderboard: [{rank, username, total_points, last_solve_time}]}` |
| GET | `/api/competitions/<comp_id>/stats` | `{competition_id, challenges_count, submissions_count, is_running}` |

> **API 契约稳定性**：这些是给前端 JS（自动刷新）使用的，字段一旦上线就不要改名，加字段可以、删字段不行。

---

## 4. Dify 评分契约 / External Hook Contract

### 4.1 出站请求（`tasks.trigger_external_hook`）

`POST <hook_url>`
- `Authorization: Bearer <api_key>`（题目级 → 解密题目级 token；否则 → 全局 `DIFY_API_KEY`）
- `Content-Type: application/json`
- `timeout=30s`

```json
{
  "inputs": {},
  "query": "<answer_text or '评分'>",
  "response_mode": "blocking",
  "conversation_id": "",
  "user": "user-<user_id>",
  "files": [
    { "type": "image|file", "transfer_method": "remote_url",
      "url": "<UPLOAD_URL_PREFIX>/<filename>" }
  ]
}
```

### 4.2 入站响应

期望 `dify_response.answer` 是合法 JSON 字符串（允许包在 ```` ```json ```` 代码块中，会自动剥离）：

```json
{ "success": bool, "score": int, "feedback": str, "auto_approved": bool }
```

| `auto_approved` | `success` | `submission.status` | `points_awarded` | `reviewed_by_name` |
|---|---|---|---|---|
| true | true | `approved` | `score` | `AI` |
| true | false | `rejected` | `0` | `AI` |
| false | – | `pending` | `0` | – |

`feedback` 与 `score` 始终写入 `submission_dify_logs`，给管理员二审参考。

### 4.3 错误处理

- 没配 hook URL → 任务返回 `{success: false, error: '...'}`，提交保持 `pending`，不抛异常。
- HTTP 异常 / JSON 解析失败 / 字段缺失 → 同上；UI 显示提交仍在 `pending`，需人工兜底。
- **不会**因为 Dify 失败把提交置为 `rejected`，避免误伤。

---

## 5. 数据模型契约 / Data Model

完整定义见 [models.py](models.py)。下表为关键实体与外键关系。

| 表 | 关键字段 | 关系 | 备注 |
|---|---|---|---|
| `users` | `id, email(uniq), username(uniq), is_admin, is_disabled` | 1-N submissions | 默认 admin 由 `app.py` 创建 |
| `competitions` | `id, name, status, pin(6 digit), countdown_minutes, countdown_started_at` | 1-N challenges, 1-N competition_access | 状态机见 CLAUDE.md §4 |
| `challenges` | `id, title, description(MD), points, category, order_index, is_active, competition_id` | 1-N submissions, 1-1 dify_config, 1-1 dify_credential | order_index 必须保留 |
| `challenge_dify_configs` | `challenge_id(uniq), enabled, base_url, api_path` | belongs to challenge | 题目级 hook 开关 |
| `challenge_dify_credentials` | `challenge_id(uniq), api_key_token(加密), api_key_masked` | belongs to challenge | API Key 不存明文 |
| `submissions` | `id, user_id, challenge_id, answer_text, status, points_awarded, submitted_at, reviewed_*` | 1-N files, 1-1 dify_log | 状态机：pending → approved/rejected |
| `submission_files` | `id, submission_id, filename, filepath` | belongs to submission | filepath 是 UPLOAD_FOLDER 内的相对路径 |
| `submission_dify_logs` | `submission_id(uniq), feedback, score` | belongs to submission | Dify 评分快照 |
| `competition_access` | `(user_id, competition_id) uniq` | belongs to user / competition | PIN 解锁记录 |
| `platform_settings` | `key(uniq), value` | – | 平台名 / Logo / Footer |
| `submission_history` / `submission_file_history` | 与 submissions / submission_files 同构 | – | 竞赛 reset 时归档，不影响排行榜 |
| `teams` | `id, name(uniq), invite_code(8 char, uniq), captain_id` | 1-N members | 默认随机 invite_code |
| `team_members` | `team_id, user_id(uniq)` | belongs to team / user | 一人最多一队 |

### 状态字段取值表

| 字段 | 合法值 | 默认 |
|---|---|---|
| `users.is_admin` | bool | false |
| `users.is_disabled` | bool | false |
| `competitions.status` | `draft | running | paused | stopped` | `draft` |
| `submissions.status` | `pending | approved | rejected` | `pending` |

### 排行榜 SQL 范式（不可破坏）

```sql
WITH max_scores AS (
    SELECT user_id, challenge_id, MAX(points_awarded) AS max_points
    FROM submissions s JOIN challenges c ON c.id = s.challenge_id
    WHERE c.competition_id = :cid AND s.status = 'approved'
    GROUP BY user_id, challenge_id
)
SELECT user_id, SUM(max_points) AS total
FROM max_scores
GROUP BY user_id
ORDER BY total DESC, last_solve_time ASC;
```

战队榜额外做一层 `MAX over team_id, challenge_id`，保证一题在战队内不重复计分。

---

## 6. 配置契约 / Environment

### 必填
| 变量 | 说明 |
|---|---|
| `SECRET_KEY` | Flask session + Dify Key 加密派生 |
| `DATABASE_URL` | postgresql://… |
| `REDIS_URL` | redis://… |

### 选填（带默认值）
| 变量 | 默认 | 说明 |
|---|---|---|
| `UPLOAD_FOLDER` | `uploads` | 相对 basedir |
| `MAX_CONTENT_LENGTH` | 16MB | 单请求大小上限 |
| `BABEL_DEFAULT_LOCALE` | `en` | 备选 `zh` |
| `EXTERNAL_HOOK_ENABLED` | `false` | 全局开关 |
| `EXTERNAL_HOOK_URL` | `''` | Dify chat-messages URL |
| `DIFY_API_KEY` | `''` | 全局 Key |
| `UPLOAD_URL_PREFIX` | `http://localhost:5000/uploads` | Dify 拉取附件用的公网前缀 |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | `admin@ctf.local / admin123` | 首次启动建账号 |
| `PLATFORM_NAME` / `PLATFORM_LOGO` / `FOOTER_TEXT` | – | 默认平台展示项 |

### 文件上传白名单
`png, jpg, jpeg, gif, txt, pdf, zip` —— 修改时需同步检查 Dify `files[].type` 推断逻辑（`tasks.py`）。

---

## 7. 非功能性约束 / Non-Functional

- **会话**：Flask-Login cookie，未实现"踢出全部会话"。改密**不**自动失效旧 cookie。
- **并发**：Gunicorn 4 worker；`order_index` 上下移动是单条 SQL 交换，未加锁，并发管理员同时点会有竞态（可接受）。
- **审计**：除 `submission_history` 外没有完整审计日志。重要动作建议未来落表。
- **多语言**：`translations.json` 是单一真源；新增文案需同时给 zh / en，否则模板会 fallback 显示英文 key。
- **时区**：DB UTC，模板里如有日期展示需在前端处理本地化。
- **可观测性**：仅依赖 `docker compose logs`，无指标 / 链路追踪。

---

## 8. 演进策略 / Evolution

下面这些方向在 [CLAUDE.md](CLAUDE.md) 的工作守则与 [docs/CHANGELOG.md](docs/CHANGELOG.md) 中已暗示，正式列在这里：

1. `routes/admin.py` 体量过大（>1000 行），新增功能优先考虑拆为子蓝图（`admin/competitions.py` / `admin/challenges.py` / `admin/submissions.py` / `admin/dify.py`）。
2. `models.py` 14 张表已在单文件里，下次大改时拆为 `models/` 包并 re-export，保留 `from models import X` 兼容。
3. Dify 调用建议抽出 `services/dify_client.py`（HTTP + 重试 + 解析）和 `services/scoring.py`（业务规则），让 `tasks.py` 只剩 Celery 包装。
4. `tests/` 覆盖薄弱，新增功能尽量带 pytest，并给 `tests/` 添加 `conftest.py` 公共 fixture。

> 这些都是非紧急重构。**正在做某个具体任务时不要顺手做大重构**——单独立项、单独 PR。
