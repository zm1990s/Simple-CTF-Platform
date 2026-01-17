# CTF平台快速启动指南
# Quick Start Guide for CTF Platform

## 🚀 方式一：Docker Compose 部署（推荐）/ Method 1: Docker Compose (Recommended)

### 前置要求 / Prerequisites
- Docker
- Docker Compose

### 步骤 / Steps

1. **进入项目目录 / Navigate to project directory**
```bash
cd /Users/mazhang/ai/CTF
```

2. **复制环境配置文件 / Copy environment file**
```bash
cp .env.example .env
```

3. **编辑 .env 文件，修改以下配置 / Edit .env file and update:**
```bash
# 重要：修改密钥！/ Important: Change the secret key!
SECRET_KEY=your-super-secret-key-here

# 可选：修改管理员账号 / Optional: Change admin credentials
ADMIN_EMAIL=admin@ctf.local
ADMIN_PASSWORD=admin123
```

4. **使用部署脚本启动 / Start using deploy script**
```bash
chmod +x deploy.sh
./deploy.sh
```

或者手动启动 / Or manually:
```bash
docker compose up -d --build
```

5. **访问平台 / Access the platform**
- URL: http://localhost:5000
- 管理员账号 / Admin account: admin@ctf.local
- 密码 / Password: admin123

6. **查看日志 / View logs**
```bash
docker compose logs -f
```

7. **停止服务 / Stop services**
```bash
docker compose down
```

---

## 💻 方式二：本地开发部署 / Method 2: Local Development

### 前置要求 / Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 步骤 / Steps

1. **创建虚拟环境 / Create virtual environment**
```bash
cd /Users/mazhang/ai/CTF
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
```

2. **安装依赖 / Install dependencies**
```bash
pip install -r requirements.txt
```

3. **启动 PostgreSQL 和 Redis / Start PostgreSQL and Redis**

使用 Docker / Using Docker:
```bash
# PostgreSQL
docker run -d --name ctf_postgres \
  -e POSTGRES_USER=ctf_user \
  -e POSTGRES_PASSWORD=ctf_password \
  -e POSTGRES_DB=ctf_platform \
  -p 5432:5432 \
  postgres:15-alpine

# Redis
docker run -d --name ctf_redis \
  -p 6379:6379 \
  redis:7-alpine
```

或使用本地安装 / Or use local installation:
```bash
# macOS with Homebrew
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis
```

4. **配置环境变量 / Configure environment**
```bash
cp .env.example .env
# 编辑 .env 文件 / Edit .env file
```

5. **初始化数据库 / Initialize database**
```bash
python init_db.py
```

6. **启动应用 / Start application**
```bash
python app.py
```

7. **（可选）启动 Celery worker / (Optional) Start Celery worker**

新开一个终端 / Open a new terminal:
```bash
source venv/bin/activate
celery -A tasks.celery worker --loglevel=info
```

8. **访问平台 / Access the platform**
- URL: http://localhost:5000
- 管理员 / Admin: admin@ctf.local / admin123

---

## ☸️ 方式三：Kubernetes 部署 / Method 3: Kubernetes Deployment

### 前置要求 / Prerequisites
- Kubernetes 集群 / Kubernetes cluster
- kubectl 已配置 / kubectl configured

### 步骤 / Steps

1. **构建镜像 / Build image**
```bash
docker build -t your-registry/ctf-platform:latest .
docker push your-registry/ctf-platform:latest
```

2. **更新配置 / Update configuration**

编辑 `k8s-deployment.yaml`，修改：
- 镜像地址 / Image URL: `your-registry/ctf-platform:latest`
- Secrets 中的敏感信息 / Secrets values

3. **部署 / Deploy**
```bash
kubectl apply -f k8s-deployment.yaml
```

4. **查看状态 / Check status**
```bash
kubectl get pods -n ctf-platform
kubectl get svc -n ctf-platform
```

5. **获取访问地址 / Get access URL**
```bash
kubectl get svc ctf-web -n ctf-platform
```

---

## 🎯 首次使用步骤 / First Time Setup

### 1. 登录管理后台 / Login to Admin Panel
- 访问 / Visit: http://localhost:5000/auth/login
- 邮箱 / Email: admin@ctf.local
- 密码 / Password: admin123

### 2. 修改管理员密码 / Change Admin Password
⚠️ **重要！首次登录后请立即修改密码**

### 3. 配置平台设置 / Configure Platform Settings
- 进入 / Go to: Admin → Platform Settings
- 修改平台名称 / Update platform name
- 上传 Logo / Upload logo

### 4. 创建竞赛 / Create Competition
- Admin → Manage Competitions → New Competition
- 填写竞赛信息 / Fill in competition details
- 设置开始和结束时间 / Set start and end time

### 5. 创建题目 / Create Challenges
- Admin → Manage Challenges → New Challenge
- 使用 Markdown 编辑题目描述 / Use Markdown for description
- 可以上传图片并插入 / Can upload and insert images
- 设置分数和分类 / Set points and category

### 6. 测试用户注册和答题 / Test Registration and Submission
- 注销管理员账号 / Logout
- 注册新用户 / Register new user
- 查看竞赛和题目 / View competitions and challenges
- 提交答案 / Submit answers

### 7. 审核提交 / Review Submissions
- 以管理员身份登录 / Login as admin
- Admin → Review Submissions
- 审核用户提交的答案 / Review user submissions
- 批准或拒绝 / Approve or reject

---

## 🔧 常见问题 / Troubleshooting

### 问题：无法连接数据库 / Issue: Cannot connect to database
**解决方案 / Solution:**
- 检查 PostgreSQL 是否运行 / Check if PostgreSQL is running
- 验证 `.env` 中的数据库连接字符串 / Verify database URL in `.env`
- 确保数据库已创建 / Ensure database is created

### 问题：静态文件无法加载 / Issue: Static files not loading
**解决方案 / Solution:**
```bash
# 确保 static 目录存在 / Ensure static directory exists
mkdir -p static uploads
```

### 问题：图片上传失败 / Issue: Image upload fails
**解决方案 / Solution:**
```bash
# 创建 uploads 目录并设置权限 / Create uploads directory with permissions
mkdir -p uploads
chmod 755 uploads
```

### 问题：Celery worker 无法启动 / Issue: Celery worker won't start
**解决方案 / Solution:**
- 检查 Redis 是否运行 / Check if Redis is running
- 验证 REDIS_URL 配置 / Verify REDIS_URL configuration
- 查看错误日志 / Check error logs

---

## 📊 功能测试清单 / Feature Testing Checklist

- [ ] 用户注册 / User registration
- [ ] 用户登录 / User login
- [ ] 查看竞赛列表 / View competitions
- [ ] 查看题目 / View challenges
- [ ] 提交文本答案 / Submit text answer
- [ ] 上传图片答案 / Upload image answer
- [ ] 查看提交历史 / View submission history
- [ ] 查看排行榜 / View leaderboard
- [ ] 管理员审核提交 / Admin review submissions
- [ ] 创建/编辑竞赛 / Create/edit competitions
- [ ] 创建/编辑题目 / Create/edit challenges
- [ ] Markdown 编辑和预览 / Markdown editing and preview
- [ ] 图片上传到题目 / Upload images to challenges
- [ ] 语言切换（中英文）/ Language switch (EN/CN)

---

## 🔐 安全建议 / Security Recommendations

1. ⚠️ **立即修改默认密码** / Change default passwords immediately
2. 🔑 **使用强随机密钥** / Use strong random SECRET_KEY
3. 🔒 **生产环境使用 HTTPS** / Use HTTPS in production
4. 🛡️ **定期备份数据库** / Regular database backups
5. 📝 **监控日志和异常** / Monitor logs and exceptions
6. 🚫 **限制管理员数量** / Limit number of admins
7. 🔐 **启用防火墙规则** / Enable firewall rules

---

## 📞 获取帮助 / Get Help

如有问题，请：
- 查看 README.md
- 检查日志文件
- 提交 Issue

For help:
- Check README.md
- Review log files
- Submit an issue

---

## 🎉 完成！/ Done!

平台已就绪，开始你的 CTF 竞赛吧！
Platform is ready, start your CTF competition!
