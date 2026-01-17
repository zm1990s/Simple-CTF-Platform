# Dify 自动审核逻辑更新

## 📋 问题描述

### 旧逻辑的问题
之前的代码要求 `success=true` **且** `auto_approved=true` 才会自动审核：

```python
if answer_data.get('success') and answer_data.get('auto_approved'):
    submission.status = 'approved'  # 只能自动通过
```

这导致：
- ❌ Dify 返回 `success=false, auto_approved=true` 时无法自动拒绝
- ❌ 必须人工审核明显错误的答案
- ❌ 违背了"自动审核"的初衷

### 实际场景
```json
// Dify 返回答案错误但想自动拒绝
{
  "success": false,
  "score": 0,
  "feedback": "答案不完整或无效，请提供具体的攻击步骤或结果。",
  "auto_approved": true
}

旧逻辑：保持 pending ❌
期望：自动 rejected ✅
```

## ✅ 新逻辑

### 核心改进
只要 `auto_approved=true`，系统就会自动审核，根据 `success` 决定通过或拒绝：

```python
if answer_data.get('auto_approved'):
    if answer_data.get('success'):
        submission.status = 'approved'  # 自动通过
        submission.points_awarded = answer_data.get('score', 0)
    else:
        submission.status = 'rejected'  # 自动拒绝
        submission.points_awarded = 0
```

### 三种审核模式

| Dify 返回 | 系统行为 | 状态 | 得分 | 审核人 |
|----------|---------|------|------|--------|
| `success=true, auto_approved=true` | 自动通过 | `approved` ✅ | Dify 的 score | AI |
| `success=false, auto_approved=true` | 自动拒绝 | `rejected` ❌ | 0 | AI |
| `auto_approved=false` | 待人工审核 | `pending` ⏳ | 0 | - |

## 📝 Dify 工作流配置建议

### 场景 1：完全自动审核（推荐）
```json
// 答案完全正确
{
  "success": true,
  "score": 10,
  "feedback": "答案完全正确！",
  "auto_approved": true
}

// 答案部分正确
{
  "success": true,
  "score": 5,
  "feedback": "答案部分正确，缺少关键信息。",
  "auto_approved": true
}

// 答案错误
{
  "success": false,
  "score": 0,
  "feedback": "答案错误或无效。",
  "auto_approved": true
}
```

### 场景 2：仅自动通过，错误的人工审核
```json
// 答案正确 - 自动通过
{
  "success": true,
  "score": 10,
  "feedback": "答案正确！",
  "auto_approved": true
}

// 答案可疑 - 人工审核
{
  "success": false,
  "score": 0,
  "feedback": "答案需要人工确认。",
  "auto_approved": false
}
```

### 场景 3：所有提交都需要人工审核
```json
{
  "success": false,  // 这个值不影响
  "score": 0,        // 这个值不影响
  "feedback": "已收到提交，等待人工审核。",
  "auto_approved": false  // 关键：设为 false
}
```

## 🧪 测试验证

### 测试用例 1：自动拒绝
**Dify 返回：**
```json
{
  "success": false,
  "score": 0,
  "feedback": "答案不完整",
  "auto_approved": true
}
```

**预期结果：**
- 状态：`rejected` ❌
- 得分：`0`
- 审核人：`AI`
- 排行榜：不计分

### 测试用例 2：自动通过
**Dify 返回：**
```json
{
  "success": true,
  "score": 10,
  "feedback": "完全正确",
  "auto_approved": true
}
```

**预期结果：**
- 状态：`approved` ✅
- 得分：`10`
- 审核人：`AI`
- 排行榜：计入 10 分

### 测试用例 3：人工审核
**Dify 返回：**
```json
{
  "success": false,
  "score": 0,
  "feedback": "需要人工确认",
  "auto_approved": false
}
```

**预期结果：**
- 状态：`pending` ⏳
- 得分：`0`
- 审核人：`-`
- 需要管理员在后台审核

## 🚀 部署说明

### Docker 环境
```bash
# 重启 web 和 celery 服务
docker-compose restart web celery
```

### 本地环境
```bash
# 重启 Flask 应用和 Celery worker
# 终端 1: Flask
python app.py

# 终端 2: Celery
celery -A tasks.celery worker --loglevel=info
```

## ✨ 优势

1. ✅ **更灵活**：支持自动通过和自动拒绝
2. ✅ **减少人工**：明显错误的答案自动拒绝
3. ✅ **提高效率**：管理员只需审核可疑提交
4. ✅ **更精准**：AI 可以明确告知答案正确性
5. ✅ **可追溯**：所有自动审核都标记为 "AI"

## 📊 实际效果对比

### 旧逻辑
```
100 个提交：
- 60 个正确 → AI 自动通过 ✅
- 30 个错误 → 需要人工拒绝 ❌（浪费时间）
- 10 个可疑 → 需要人工审核 ⏳

管理员需要审核：40 个
```

### 新逻辑
```
100 个提交：
- 60 个正确 → AI 自动通过 ✅
- 30 个错误 → AI 自动拒绝 ✅（节省时间）
- 10 个可疑 → 需要人工审核 ⏳

管理员需要审核：10 个
```

**效率提升：75% 👍**

## 🔧 Dify 工作流示例

### LLM 提示词建议
```
你是一个 CTF 题目评分助手。根据用户提交的答案评估其正确性。

输出 JSON 格式：
{
  "success": boolean,  // 答案是否正确
  "score": number,     // 得分 (0-题目总分)
  "feedback": string,  // 评分反馈
  "auto_approved": boolean  // 是否自动审核
}

评分标准：
1. 答案完全正确且完整 -> success=true, score=满分, auto_approved=true
2. 答案部分正确 -> success=true, score=部分分, auto_approved=true
3. 答案明显错误或无效 -> success=false, score=0, auto_approved=true
4. 答案需要人工判断 -> success=false, score=0, auto_approved=false

请严格输出 JSON，不要添加其他内容。
```

## 📋 回归测试清单

- [ ] AI 自动通过（success=true）正常工作
- [ ] AI 自动拒绝（success=false, auto_approved=true）正常工作
- [ ] 人工审核（auto_approved=false）保持 pending
- [ ] 审核人显示为 "AI"
- [ ] 排行榜只计算 approved 的分数
- [ ] rejected 的提交不计分
- [ ] 所有提交记录都保留

## 🆕 修改的文件

1. `tasks.py` - 更新自动审核逻辑
2. `README.md` - 更新文档说明

## 🔄 无需数据库迁移

此更新只修改了业务逻辑，无需更改数据库结构。
