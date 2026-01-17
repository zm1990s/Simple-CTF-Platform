# CTF Platform - 项目结构说明
# Project Structure Documentation

## 📁 目录结构 / Directory Structure

```
CTF/
├── app.py                      # Flask应用主文件 / Main Flask application
├── wsgi.py                     # WSGI入口 / WSGI entry point
├── config.py                   # 配置文件 / Configuration
├── models.py                   # 数据库模型 / Database models
├── forms.py                    # WTForms表单 / Form definitions
├── tasks.py                    # Celery异步任务 / Celery tasks
├── init_db.py                  # 数据库初始化脚本 / DB initialization
├── test_platform.py            # 测试脚本 / Test script
│
├── requirements.txt            # Python依赖 / Python dependencies
├── .env.example               # 环境变量模板 / Environment template
├── .gitignore                 # Git忽略文件 / Git ignore
│
├── Dockerfile                 # Docker镜像配置 / Docker image config
├── docker compose.yml         # Docker Compose配置 / Compose config
├── k8s-deployment.yaml        # Kubernetes部署配置 / K8s deployment
├── deploy.sh                  # 部署脚本 / Deployment script
│
├── routes/                    # 路由模块 / Route modules
│   ├── __init__.py
│   ├── auth.py               # 认证路由 / Authentication routes
│   ├── frontend.py           # 前台路由 / Frontend routes
│   ├── admin.py              # 后台路由 / Admin routes
│   └── api.py                # API路由 / API routes
│
├── templates/                 # Jinja2模板 / Templates
│   ├── base.html             # 基础模板 / Base template
│   ├── auth/                 # 认证页面 / Auth pages
│   │   ├── login.html
│   │   └── register.html
│   ├── frontend/             # 前台页面 / Frontend pages
│   │   ├── index.html
│   │   ├── competition.html
│   │   ├── challenge.html
│   │   ├── leaderboard.html
│   │   └── my_submissions.html
│   └── admin/                # 后台页面 / Admin pages
│       ├── dashboard.html
│       ├── settings.html
│       ├── users.html
│       ├── competitions.html
│       ├── competition_form.html
│       ├── challenges.html
│       ├── challenge_form.html
│       ├── submissions.html
│       └── submission_review.html
│
├── static/                    # 静态文件 / Static files
│   ├── style.css             # 自定义样式 / Custom styles
│   └── logo.png              # (平台Logo / Platform logo)
│
├── uploads/                   # 上传文件目录 / Upload directory
│   └── .gitkeep
│
├── translations.json          # 国际化翻译 / i18n translations
├── README.md                  # 项目说明 / Project readme
├── QUICKSTART.md             # 快速启动指南 / Quick start guide
├── SETUP.md                  # 安装说明 / Setup instructions
└── STRUCTURE.md              # 本文件 / This file
```

## 🔧 核心文件说明 / Core Files

### app.py
Flask应用工厂，负责：
- 初始化Flask应用
- 配置数据库和扩展
- 注册蓝图（blueprints）
- 创建默认管理员

### config.py
配置管理，包含：
- 开发/生产环境配置
- 数据库连接配置
- 上传文件配置
- 外部Hook配置

### models.py
数据库模型定义：
- `User`: 用户模型
- `Competition`: 竞赛模型
- `Challenge`: 题目模型
- `Submission`: 提交模型
- `SubmissionFile`: 提交文件模型
- `PlatformSettings`: 平台设置模型

### forms.py
WTForms表单定义：
- `LoginForm`: 登录表单
- `RegisterForm`: 注册表单
- `ChallengeForm`: 题目表单
- `CompetitionForm`: 竞赛表单
- `SubmissionForm`: 提交表单
- `ReviewForm`: 审核表单

### tasks.py
Celery异步任务：
- `trigger_external_hook`: 触发外部Hook（如Dify工作流）

## 📋 路由模块说明 / Route Modules

### routes/auth.py
认证相关路由：
- `/auth/register`: 用户注册
- `/auth/login`: 用户登录
- `/auth/logout`: 用户登出
- `/auth/set-locale/<locale>`: 切换语言

### routes/frontend.py
前台用户路由：
- `/`: 首页，显示竞赛列表
- `/competition/<id>`: 竞赛详情页
- `/challenge/<id>`: 题目详情和答题页
- `/leaderboard/<id>`: 排行榜
- `/my-submissions`: 个人提交历史

### routes/admin.py
后台管理路由：
- `/admin/`: 管理后台首页
- `/admin/settings`: 平台设置
- `/admin/users`: 用户管理
- `/admin/competitions`: 竞赛管理
- `/admin/challenges`: 题目管理
- `/admin/submissions`: 提交审核
- `/admin/upload-image`: 图片上传（Markdown编辑器）

### routes/api.py
API接口：
- `/api/leaderboard/<id>`: 排行榜API（用于实时刷新）
- `/api/competitions/<id>/stats`: 竞赛统计API

## 🗄️ 数据库模型关系 / Database Model Relationships

```
User (用户)
  ├── 1:N → Submission (提交)
  └── is_admin (管理员标识)

Competition (竞赛)
  ├── 1:N → Challenge (题目)
  └── start_time, end_time (时间范围)

Challenge (题目)
  ├── N:1 → Competition
  ├── 1:N → Submission
  └── description (Markdown描述)

Submission (提交)
  ├── N:1 → User
  ├── N:1 → Challenge
  ├── 1:N → SubmissionFile (上传的文件)
  └── status: pending/approved/rejected

SubmissionFile (提交文件)
  └── N:1 → Submission

PlatformSettings (平台设置)
  └── key-value存储
```

## 🎨 前端技术栈 / Frontend Stack

- **Bootstrap 5**: UI框架
- **Bootstrap Icons**: 图标
- **Marked.js**: Markdown渲染
- **Jinja2**: 模板引擎

## 🔌 后端技术栈 / Backend Stack

- **Flask**: Web框架
- **SQLAlchemy**: ORM
- **Flask-Login**: 用户认证
- **Flask-Migrate**: 数据库迁移
- **Flask-WTF**: 表单处理
- **Celery**: 异步任务队列
- **Redis**: 缓存和任务队列
- **PostgreSQL**: 数据库

## 🚀 部署架构 / Deployment Architecture

### Docker Compose架构
```
┌─────────────┐
│   Nginx     │ (可选 / Optional)
└──────┬──────┘
       │
┌──────▼──────┐
│  Flask Web  │ (Gunicorn)
└──────┬──────┘
       │
  ┌────┼────┐
  │    │    │
┌─▼─┐ ┌▼──┐ ┌▼────────┐
│DB │ │Red│ │ Celery  │
│SQL│ │is │ │ Worker  │
└───┘ └───┘ └─────────┘
```

### Kubernetes架构
```
┌──────────────────────────────────┐
│         Load Balancer            │
└────────────┬─────────────────────┘
             │
┌────────────▼─────────────────────┐
│     Flask Web Pods (3 replicas)  │
│     + HPA (Auto-scaling)         │
└────────────┬─────────────────────┘
             │
   ┌─────────┼─────────┐
   │         │         │
┌──▼───┐  ┌─▼──┐  ┌──▼──────────┐
│ PG   │  │Red │  │Celery Worker│
│ SQL  │  │is  │  │   Pods      │
└──────┘  └────┘  └─────────────┘
   │
┌──▼────────────┐
│ PersistentVol │
│   (Database)  │
└───────────────┘
```

## 🔄 数据流 / Data Flow

### 用户答题流程 / User Submission Flow
```
1. 用户登录 / User Login
   ↓
2. 查看竞赛 / View Competition
   ↓
3. 选择题目 / Select Challenge
   ↓
4. 提交答案 / Submit Answer
   ├─ 文本答案 / Text Answer
   └─ 图片上传 / Image Upload
   ↓
5. 存储到数据库 / Store in DB
   ↓
6. (可选) 触发外部Hook / (Optional) Trigger Hook
   ↓
7. 管理员审核 / Admin Review
   ↓
8. 更新排行榜 / Update Leaderboard
```

### 管理员创建题目流程 / Admin Challenge Creation Flow
```
1. 登录管理后台 / Login Admin
   ↓
2. 创建/编辑题目 / Create/Edit Challenge
   ↓
3. 使用Markdown编辑器 / Use Markdown Editor
   ├─ 实时预览 / Live Preview
   └─ 上传图片 / Upload Images
   ↓
4. 设置分数和分类 / Set Points & Category
   ↓
5. 关联竞赛 / Link to Competition
   ↓
6. 保存并发布 / Save & Publish
```

## 🔐 权限控制 / Access Control

### 公开页面 / Public Pages
- 首页（竞赛列表）
- 排行榜
- 登录/注册

### 需要登录 / Requires Login
- 查看题目详情
- 提交答案
- 个人提交历史

### 需要管理员 / Requires Admin
- 所有 `/admin/*` 路由
- 平台设置
- 用户管理
- 竞赛管理
- 题目管理
- 提交审核

## 📝 扩展开发指南 / Extension Guide

### 添加新的路由 / Adding New Routes

1. 在对应的蓝图文件中添加路由
2. 创建对应的模板文件
3. 更新导航菜单（如需要）

### 添加新的数据模型 / Adding New Models

1. 在 `models.py` 中定义模型
2. 运行数据库迁移：
```bash
flask db migrate -m "Add new model"
flask db upgrade
```

### 添加新的表单 / Adding New Forms

1. 在 `forms.py` 中定义表单
2. 在路由中使用表单
3. 在模板中渲染表单

### 自定义样式 / Customizing Styles

编辑 `static/style.css` 添加自定义CSS

## 🧪 测试 / Testing

运行测试脚本：
```bash
python test_platform.py
```

## 📚 更多资源 / More Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Bootstrap Documentation](https://getbootstrap.com/)
- [Marked.js Documentation](https://marked.js.org/)

---

最后更新 / Last Updated: 2026-01-16
