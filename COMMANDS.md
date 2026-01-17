# 🚀 CTF平台 - 常用命令参考
# Quick Command Reference

## 📋 目录 / Table of Contents
1. [初始化和启动](#初始化和启动)
2. [Docker命令](#docker命令)
3. [数据库操作](#数据库操作)
4. [开发调试](#开发调试)
5. [测试命令](#测试命令)
6. [生产部署](#生产部署)

---

## 🎬 初始化和启动 / Initialization & Startup

### 首次安装 / First Time Setup
```bash
# 1. 进入项目目录
cd /Users/mazhang/ai/CTF

# 2. 复制环境配置
cp .env.example .env

# 3. 编辑配置（重要！）
nano .env  # 或使用其他编辑器

# 4. 检查部署准备
chmod +x check_deployment.sh
./check_deployment.sh
```

### 快速启动 / Quick Start
```bash
# 使用Docker Compose（推荐）
./deploy.sh

# 或手动启动
docker compose up -d
```

---

## 🐳 Docker命令 / Docker Commands

### 启动服务 / Start Services
```bash
# 启动所有服务
docker compose up -d

# 启动并重新构建
docker compose up -d --build

# 查看启动日志
docker compose up
```

### 查看状态 / Check Status
```bash
# 查看运行中的容器
docker compose ps

# 查看日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f web
docker compose logs -f postgres
docker compose logs -f redis
docker compose logs -f celery
```

### 停止和清理 / Stop & Clean
```bash
# 停止服务
docker compose stop

# 停止并删除容器
docker compose down

# 停止并删除容器和卷
docker compose down -v

# 重启服务
docker compose restart

# 重启特定服务
docker compose restart web
```

### 进入容器 / Enter Container
```bash
# 进入web容器
docker compose exec web bash

# 进入数据库容器
docker compose exec postgres psql -U ctf_user -d ctf_platform

# 进入Redis容器
docker compose exec redis redis-cli
```

---

## 🗄️ 数据库操作 / Database Operations

### 初始化数据库 / Initialize Database
```bash
# 使用初始化脚本（推荐）
python init_db.py

# 创建示例数据
python create_sample_data.py
```

### Flask-Migrate命令 / Flask-Migrate Commands
```bash
# 初始化迁移
flask db init

# 创建迁移
flask db migrate -m "描述信息"

# 应用迁移
flask db upgrade

# 回退迁移
flask db downgrade

# 查看迁移历史
flask db history
```

### 直接数据库访问 / Direct Database Access
```bash
# 使用Docker连接PostgreSQL
docker compose exec postgres psql -U ctf_user -d ctf_platform

# PostgreSQL常用命令
\dt              # 列出所有表
\d table_name    # 查看表结构
\l               # 列出所有数据库
\q               # 退出
```

### 数据库备份和恢复 / Backup & Restore
```bash
# 备份数据库
docker compose exec postgres pg_dump -U ctf_user ctf_platform > backup.sql

# 恢复数据库
cat backup.sql | docker compose exec -T postgres psql -U ctf_user ctf_platform
```

---

## 💻 开发调试 / Development & Debugging

### 本地开发环境 / Local Development
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python app.py

# 或使用Flask命令
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

### Celery开发 / Celery Development
```bash
# 启动Celery worker
celery -A tasks.celery worker --loglevel=info

# 启动Celery worker（自动重载）
watchmedo auto-restart -d . -p '*.py' -- celery -A tasks.celery worker --loglevel=info
```

### Python交互式调试 / Python Interactive Debugging
```bash
# 进入Flask shell
flask shell

# 在shell中操作数据库
>>> from models import *
>>> User.query.all()
>>> Competition.query.first()
```

---

## 🧪 测试命令 / Testing Commands

### 运行测试 / Run Tests
```bash
# 运行测试脚本
python test_platform.py

# 检查部署准备
./check_deployment.sh
```

### 手动测试 / Manual Testing
```bash
# 测试API端点
curl http://localhost:5000/api/leaderboard/1

# 测试健康检查
curl http://localhost:5000/

# 查看响应头
curl -I http://localhost:5000/
```

---

## 🚀 生产部署 / Production Deployment

### Docker生产部署 / Docker Production
```bash
# 设置生产环境变量
export FLASK_ENV=production

# 构建生产镜像
docker build -t ctf-platform:latest .

# 启动生产服务
docker compose -f docker compose.yml up -d
```

### Kubernetes部署 / Kubernetes Deployment
```bash
# 应用K8s配置
kubectl apply -f k8s-deployment.yaml

# 查看Pod状态
kubectl get pods -n ctf-platform

# 查看服务
kubectl get svc -n ctf-platform

# 查看日志
kubectl logs -n ctf-platform -l app=ctf-web -f

# 进入Pod
kubectl exec -it -n ctf-platform <pod-name> -- bash

# 删除部署
kubectl delete -f k8s-deployment.yaml
```

### 使用Gunicorn / Using Gunicorn
```bash
# 启动Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app

# 后台运行
gunicorn --bind 0.0.0.0:5000 --workers 4 --daemon wsgi:app

# 查看进程
ps aux | grep gunicorn

# 停止
pkill gunicorn
```

---

## 🔧 维护命令 / Maintenance Commands

### 清理和优化 / Cleanup & Optimization
```bash
# 清理Python缓存
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# 清理Docker
docker system prune -a

# 清理未使用的卷
docker volume prune
```

### 查看系统资源 / Check System Resources
```bash
# Docker资源使用
docker stats

# 磁盘使用
docker system df

# 查看容器资源限制
docker compose exec web cat /sys/fs/cgroup/memory/memory.limit_in_bytes
```

### 日志管理 / Log Management
```bash
# 清理日志
docker compose logs --tail=0 -f > /dev/null

# 导出日志
docker compose logs > logs.txt

# 按时间过滤日志
docker compose logs --since 2024-01-01 --until 2024-01-02
```

---

## 📊 监控命令 / Monitoring Commands

### 实时监控 / Real-time Monitoring
```bash
# 查看容器资源使用
docker stats

# 查看实时日志
docker compose logs -f --tail=100

# 查看数据库连接
docker compose exec postgres psql -U ctf_user -d ctf_platform -c "SELECT * FROM pg_stat_activity;"
```

### 性能检查 / Performance Check
```bash
# 检查响应时间
time curl http://localhost:5000/

# 压力测试（需要安装ab）
ab -n 1000 -c 10 http://localhost:5000/

# 或使用wrk
wrk -t4 -c100 -d30s http://localhost:5000/
```

---

## 🔐 安全相关 / Security Related

### 更新密码 / Update Passwords
```bash
# 进入Flask shell
flask shell

# 更新管理员密码
>>> from models import User
>>> admin = User.query.filter_by(email='admin@ctf.local').first()
>>> admin.set_password('new_password')
>>> db.session.commit()
```

### 检查安全配置 / Check Security Config
```bash
# 检查SECRET_KEY是否已修改
grep SECRET_KEY .env

# 检查密码强度
# 确保生产环境使用强密码
```

---

## 📝 常用快捷命令 / Useful Shortcuts

### 一键重启 / One-Click Restart
```bash
# 重启所有服务
docker compose restart

# 重新构建并启动
docker compose up -d --build --force-recreate
```

### 快速重置 / Quick Reset
```bash
# 停止、删除、重新构建、启动
docker compose down && docker compose up -d --build
```

### 完全重置（危险！）/ Full Reset (Dangerous!)
```bash
# 删除所有数据和容器
docker compose down -v
rm -rf uploads/*
docker compose up -d --build
python init_db.py
```

---

## 🆘 故障排查 / Troubleshooting

### 容器无法启动 / Container Won't Start
```bash
# 查看详细日志
docker compose logs web

# 检查端口占用
lsof -i :5000
lsof -i :5432

# 重新构建
docker compose build --no-cache
```

### 数据库连接问题 / Database Connection Issues
```bash
# 检查数据库是否运行
docker compose ps postgres

# 测试数据库连接
docker compose exec postgres pg_isready -U ctf_user

# 查看数据库日志
docker compose logs postgres
```

### 权限问题 / Permission Issues
```bash
# 修复uploads目录权限
chmod -R 755 uploads/

# 修复脚本权限
chmod +x deploy.sh check_deployment.sh
```

---

## 📚 参考资料 / References

### 官方文档 / Official Documentation
- Flask: https://flask.palletsprojects.com/
- Docker: https://docs.docker.com/
- Kubernetes: https://kubernetes.io/docs/
- PostgreSQL: https://www.postgresql.org/docs/

### 项目文档 / Project Documentation
- README.md - 项目概述
- QUICKSTART.md - 快速开始
- STRUCTURE.md - 项目结构

---

**最后更新 / Last Updated**: 2026-01-16  
**版本 / Version**: 1.0.0
