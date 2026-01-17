# Dify 自动评分功能更新说明

## 📋 更新内容

### 1. 新增字段
在 `submissions` 表中添加了 `reviewed_by_name` 字段：
- 用于存储审核人名称（如 "AI" 或管理员用户名）
- 类型：VARCHAR(100)
- 可为空

### 2. 自动评分标记
当 Dify 自动审核通过时：
- `reviewed_by_name` 自动设置为 **"AI"**
- `reviewed_by_id` 保持为 NULL（表示非人工审核）
- 系统自动记录审核时间和得分

### 3. 手动审核标记
当管理员手动审核时：
- `reviewed_by_name` 设置为管理员的用户名
- `reviewed_by_id` 设置为管理员的用户ID

### 4. 界面显示
审核人显示优先级：
1. 优先显示 `reviewed_by_name`（"AI" 或管理员用户名）
2. 如果为空，则显示关联用户的用户名
3. 都为空时显示 "-"

## 🔧 部署步骤

### Docker 环境

1. 拉取最新代码：
```bash
git pull
```

2. 运行数据库迁移：
```bash
docker exec ctf_web python add_reviewed_by_name.py
```

或者重启服务（会自动执行迁移）：
```bash
docker-compose down
docker-compose up -d --build
```

### 本地开发环境

1. 拉取最新代码：
```bash
git pull
```

2. 激活虚拟环境并运行迁移：
```bash
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

python add_reviewed_by_name.py
```

或使用迁移脚本：
```bash
./migrate_db.sh
```

## ✅ 验证

迁移完成后，你可以：

1. 提交一个测试答案
2. 等待 Dify 自动审核
3. 在后台查看提交记录，审核人应显示为 "**AI**"

## 📝 配置示例

确保 `.env` 文件包含以下配置：

```bash
# Dify 自动评分配置
EXTERNAL_HOOK_ENABLED=true
EXTERNAL_HOOK_URL=https://aisec.halfcoffee.com/v1/chat-messages
DIFY_API_KEY=app-your-api-key
UPLOAD_URL_PREFIX=http://your-public-ip:5000/uploads
```

## 🎯 预期行为

### 自动审核通过
- 状态：`approved`
- 审核人：`AI`
- 得分：Dify 返回的分数

### 自动审核失败
- 状态：`pending`（保持待审核）
- 审核人：`-`
- 需要管理员手动审核

### 手动审核
- 状态：`approved` 或 `rejected`
- 审核人：管理员用户名（如 `admin`）
- 得分：管理员设置的分数

## 🐛 故障排查

### 迁移失败
如果迁移脚本报错，可以手动执行 SQL：

```sql
-- 添加字段
ALTER TABLE submissions ADD COLUMN reviewed_by_name VARCHAR(100);

-- 迁移现有数据（可选）
UPDATE submissions 
SET reviewed_by_name = users.username 
FROM users 
WHERE submissions.reviewed_by_id = users.id 
AND submissions.reviewed_by_name IS NULL;
```

### Celery worker 无法导入模块
确保 docker-compose.yml 中的 celery 服务包含：
```yaml
environment:
  - PYTHONPATH=/app
```

然后重启服务：
```bash
docker-compose restart celery
```

## 📊 数据库更改摘要

| 表名 | 字段名 | 类型 | 说明 |
|------|--------|------|------|
| submissions | reviewed_by_name | VARCHAR(100) | 审核人名称（AI或用户名） |

## 🔄 回滚（如需要）

如果需要回滚此更改：

```sql
ALTER TABLE submissions DROP COLUMN reviewed_by_name;
```

**注意**：回滚前请确保已备份数据。
