# Challenge Order Index 问题修复

## 🐛 问题描述

克隆 Competition 后，所有 Challenge 的顺序调整功能失效。

### 根本原因

在克隆/导入/导出 Competition 时，**没有正确处理 `order_index` 字段**：

1. **Competition 克隆** (`competition_duplicate`) - ❌ 未复制 `order_index`
2. **Competition 导出** (`competition_export`) - ❌ 未导出 `order_index`
3. **Competition 批量导出** (`competitions_export_all`) - ❌ 未导出 `order_index`
4. **Competition 导入** (`competition_import`) - ❌ 未导入 `order_index`
5. **Challenge 复制** (`challenge_copy`) - ✅ 已正确处理

## ✅ 修复内容

### 1. `competition_duplicate()` - Competition 克隆

**修复前：**
```python
# Duplicate all challenges
for challenge in original.challenges:
    new_challenge = Challenge(
        title=challenge.title,
        description=challenge.description,
        points=challenge.points,
        category=challenge.category,
        competition_id=new_competition.id,
        is_active=challenge.is_active
        # ❌ 缺少 order_index
    )
```

**修复后：**
```python
# Duplicate all challenges (sorted by order_index to maintain order)
original_challenges = Challenge.query.filter_by(
    competition_id=original.id
).order_by(Challenge.order_index.asc(), Challenge.id.asc()).all()

for challenge in original_challenges:
    new_challenge = Challenge(
        title=challenge.title,
        description=challenge.description,
        points=challenge.points,
        category=challenge.category,
        competition_id=new_competition.id,
        order_index=challenge.order_index,  # ✅ 保留原始顺序
        is_active=challenge.is_active
    )
```

### 2. `competition_export()` - Competition 导出

**修复前：**
```python
# Add all challenges
for challenge in competition.challenges:
    challenge_data = {
        'title': challenge.title,
        'description': challenge.description,
        'points': challenge.points,
        'category': challenge.category,
        'is_active': challenge.is_active
        # ❌ 缺少 order_index
    }
```

**修复后：**
```python
# Add all challenges (sorted by order_index to preserve order)
sorted_challenges = Challenge.query.filter_by(
    competition_id=competition.id
).order_by(Challenge.order_index.asc(), Challenge.id.asc()).all()

for challenge in sorted_challenges:
    challenge_data = {
        'title': challenge.title,
        'description': challenge.description,
        'points': challenge.points,
        'category': challenge.category,
        'order_index': challenge.order_index,  # ✅ 导出顺序
        'is_active': challenge.is_active
    }
```

### 3. `competitions_export_all()` - 批量导出

修复逻辑同 `competition_export()`。

### 4. `competition_import()` - Competition 导入

**修复前：**
```python
for challenge_data in data['challenges']:
    challenge = Challenge(
        title=challenge_data['title'],
        description=challenge_data['description'],
        points=challenge_data.get('points', 100),
        category=challenge_data.get('category', ''),
        competition_id=competition.id,
        is_active=challenge_data.get('is_active', True)
        # ❌ 缺少 order_index
    )
```

**修复后：**
```python
for idx, challenge_data in enumerate(data['challenges']):
    challenge = Challenge(
        title=challenge_data['title'],
        description=challenge_data['description'],
        points=challenge_data.get('points', 100),
        category=challenge_data.get('category', ''),
        competition_id=competition.id,
        order_index=challenge_data.get('order_index', idx),  # ✅ 使用导出的顺序或索引
        is_active=challenge_data.get('is_active', True)
    )
```

## 🔄 影响范围

### 需要重新导入的数据

如果之前已经导出过 Competition：

1. **旧的导出文件** - 不包含 `order_index`，导入时会使用数组索引 (0, 1, 2, ...)
2. **新的导出文件** - 包含 `order_index`，导入时会保留原始顺序

### 已克隆的 Competition

之前克隆的 Competition，所有 Challenge 的 `order_index` 都是 0（默认值）：

**解决方法：**
1. 在管理后台使用 ⬆️ ⬇️ 按钮手动调整顺序
2. 或删除克隆的 Competition，重新克隆（新代码会保留顺序）

## 📝 测试验证

运行测试脚本检查当前状态：

```bash
docker exec ctf_web python test_order_index.py
```

输出示例：
```
======================================================================
测试 order_index 功能 / Testing order_index functionality
======================================================================

📊 Test 1: 检查现有 Challenges 的 order_index

🏆 Competition: CTF 2026 (ID: 1)
   ID     order_index  Title
   ------------------------------------------------------------
   1      0            Web Basics
   2      1            Crypto Challenge
   3      2            Reverse Engineering

📊 Test 2: 验证 order_index 字段是否存在
   ✅ order_index 字段存在

======================================================================
测试完成 / Test completed
======================================================================
```

## 🚀 部署步骤

### 1. 应用代码更新

```bash
# 重启服务以应用新代码
docker-compose restart web
```

### 2. 验证修复

1. **克隆测试**：
   - 克隆一个有多个题目的 Competition
   - 检查克隆后的题目顺序是否保持一致
   - 测试 ⬆️ ⬇️ 按钮是否正常工作

2. **导出/导入测试**：
   - 导出一个 Competition
   - 检查 JSON 文件中是否包含 `order_index` 字段
   - 导入该 Competition
   - 验证导入后的题目顺序

## 📊 相关文件

- `routes/admin.py` - 修复了 4 个函数
- `models.py` - Challenge 模型包含 `order_index` 字段
- `add_challenge_order.py` - 数据库迁移脚本
- `test_order_index.py` - 测试脚本

## 🔗 相关文档

- `docs/changelog/CHALLENGE_ORDER_FEATURE.md` - 题目排序功能文档
- `MIGRATIONS.md` - 数据库迁移指南

---

**修复日期**: 2026-01-17  
**影响版本**: 所有使用 order_index 功能的版本
