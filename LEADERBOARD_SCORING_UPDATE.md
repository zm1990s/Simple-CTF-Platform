# 排行榜计分规则更新说明

## 📊 更新内容

### 问题
之前的排行榜逻辑会将同一用户对同一题目的所有通过提交的分数**累加**，导致：
- 用户可以通过多次提交同一题目获得重复分数
- 排行榜分数不真实，违反 CTF 竞赛规则

### 解决方案
修改排行榜计算逻辑，**每个用户对每道题只计算最高分**：
- ✅ 用户可以多次提交同一题目
- ✅ 所有提交记录都会保留
- ✅ 但排行榜只计入每题的最高得分
- ✅ 其他提交只作为历史记录，不影响排名

## 🔧 技术实现

### 修改的文件
1. `routes/frontend.py` - 前台排行榜页面
2. `routes/api.py` - 排行榜 API 接口

### SQL 查询逻辑

**旧逻辑（错误）：**
```sql
-- 直接对所有 approved 提交求和
SELECT user_id, SUM(points_awarded) as total_points
FROM submissions
WHERE status = 'approved'
GROUP BY user_id
```

**新逻辑（正确）：**
```sql
-- 第一步：每个用户每道题取最高分
SELECT user_id, challenge_id, MAX(points_awarded) as max_points
FROM submissions
WHERE status = 'approved'
GROUP BY user_id, challenge_id

-- 第二步：对每个用户的最高分求和
SELECT user_id, SUM(max_points) as total_points
FROM (上述子查询)
GROUP BY user_id
ORDER BY total_points DESC
```

## 📝 使用场景示例

### 场景 1：用户多次提交同一题
```
用户 A 对题目 1 的提交记录：
- 第 1 次提交：8 分（approved）
- 第 2 次提交：10 分（approved）
- 第 3 次提交：7 分（rejected）

旧逻辑计分：8 + 10 = 18 分 ❌
新逻辑计分：max(8, 10) = 10 分 ✅
```

### 场景 2：完整竞赛示例
```
用户 A 的提交：
- 题目 1：[5分, 8分, 10分] → 计入 10 分
- 题目 2：[15分] → 计入 15 分
- 题目 3：[20分, 18分] → 计入 20 分
总分：10 + 15 + 20 = 45 分

用户 B 的提交：
- 题目 1：[10分] → 计入 10 分
- 题目 2：[15分, 12分] → 计入 15 分
- 题目 4：[25分] → 计入 25 分
总分：10 + 15 + 25 = 50 分

排行榜：
1. 用户 B - 50 分
2. 用户 A - 45 分
```

## ✅ 验证方法

### 测试步骤
1. 创建一个竞赛和一道题目（例如 10 分）
2. 用户 A 提交答案并获得 5 分（部分正确）
3. 管理员审核通过，用户 A 获得 5 分
4. 检查排行榜：用户 A 应显示 5 分 ✅
5. 用户 A 再次提交答案并获得 10 分（完全正确）
6. 管理员审核通过，用户 A 获得 10 分
7. 检查排行榜：用户 A 应显示 10 分（不是 15 分）✅
8. 在"我的提交"页面应该看到两条记录 ✅

### SQL 验证查询
```sql
-- 查看用户的所有提交
SELECT 
    u.username,
    c.title as challenge,
    s.points_awarded,
    s.status,
    s.reviewed_at
FROM submissions s
JOIN users u ON s.user_id = u.id
JOIN challenges c ON s.challenge_id = c.id
WHERE u.id = 1  -- 替换为测试用户ID
ORDER BY s.reviewed_at DESC;

-- 验证排行榜计算
WITH max_scores AS (
    SELECT 
        user_id,
        challenge_id,
        MAX(points_awarded) as max_points
    FROM submissions
    WHERE status = 'approved'
    GROUP BY user_id, challenge_id
)
SELECT 
    u.username,
    SUM(ms.max_points) as total_points
FROM max_scores ms
JOIN users u ON ms.user_id = u.id
GROUP BY u.id, u.username
ORDER BY total_points DESC;
```

## 🎯 预期效果

### 用户体验
- ✅ 鼓励用户不断改进答案
- ✅ 允许多次尝试而不会被"惩罚"
- ✅ 更公平的竞赛环境
- ✅ 符合标准 CTF 竞赛规则

### 数据完整性
- ✅ 所有提交历史完整保留
- ✅ 可追溯用户的进步过程
- ✅ 管理员可查看所有提交记录
- ✅ 审核历史不丢失

## 🔄 部署说明

此更新**无需数据库迁移**，只修改了查询逻辑。

### 部署步骤
1. 拉取最新代码：
```bash
git pull
```

2. 重启服务：
```bash
# Docker 环境
docker-compose restart web

# 本地环境
# 重启 Flask 应用即可
```

3. 清除浏览器缓存（如果排行榜有缓存）

## 📋 回归测试检查清单

- [ ] 用户可以正常提交答案
- [ ] 管理员可以正常审核提交
- [ ] 排行榜正确显示（只计最高分）
- [ ] API 接口返回正确数据
- [ ] 自动刷新功能正常工作
- [ ] "我的提交"页面显示所有记录
- [ ] 多次提交同一题不会累加分数

## 💡 相关功能

这个更新影响以下页面和功能：
- `/leaderboard/<competition_id>` - 排行榜页面
- `/api/leaderboard/<competition_id>` - 排行榜 API
- 前台首页的排行榜预览（如有）
- 实时排行榜自动刷新功能

## 📚 标准 CTF 规则参考

大多数 CTF 竞赛平台（如 CTFd、FBCTF）都遵循以下规则：
- 每题只计一次分数
- 取最高/最后一次成功提交的分数
- 允许多次提交但不重复计分
- 所有提交记录保留用于审计

此更新使我们的平台符合业界标准 ✅
