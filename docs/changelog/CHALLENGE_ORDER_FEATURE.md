# 题目顺序管理功能

## 📋 功能说明

管理员现在可以自定义题目的显示顺序，让竞赛题目按照期望的顺序展示给用户。

## ✨ 新增功能

### 1. 题目顺序字段
- 在 `challenges` 表中添加了 `order_index` 字段
- 数值越小，显示越靠前
- 默认值为 0

### 2. 管理界面排序控制
在**后台管理 → 管理题目**页面，每道题目都有上下移动按钮：
- ⬆️ **向上移动**：题目在列表中上移一位
- ⬇️ **向下移动**：题目在列表中下移一位

### 3. 前台显示
- 用户看到的题目按 `order_index` 升序排列
- 同一 `order_index` 的题目按 ID 排序
- 确保显示顺序稳定一致

## 🎯 使用场景

### 场景 1：难度递进
```
题目顺序：
1. 基础题（简单） - order_index: 0
2. 进阶题（中等） - order_index: 1
3. 高级题（困难） - order_index: 2
4. 终极挑战     - order_index: 3
```

### 场景 2：知识点分组
```
Web 安全系列：
1. SQL 注入基础  - order_index: 0
2. XSS 漏洞      - order_index: 1
3. CSRF 攻击     - order_index: 2

密码学系列：
1. 凯撒密码      - order_index: 3
2. RSA 加密      - order_index: 4
```

### 场景 3：故事线引导
```
闯关模式：
1. 第一章：入门  - order_index: 0
2. 第二章：探索  - order_index: 1
3. 第三章：挑战  - order_index: 2
4. 最终关卡      - order_index: 3
```

## 🔧 部署步骤

### 1. 数据库迁移

**Docker 环境：**
```bash
docker exec ctf_web python add_challenge_order.py
```

**本地环境：**
```bash
python add_challenge_order.py
```

### 2. 重启服务

**Docker 环境：**
```bash
docker-compose restart web
```

**本地环境：**
```bash
# 重启 Flask 应用
```

## 📝 使用说明

### 调整题目顺序

1. 登录管理后台
2. 进入 **管理题目** 页面
3. 找到需要调整的题目
4. 点击 ⬆️ 向上移动或 ⬇️ 向下移动按钮
5. 题目顺序立即生效

### 查看效果

1. 前往竞赛页面
2. 查看题目列表
3. 题目按照设置的顺序显示

## 🆕 修改的文件

1. **models.py**
   - 在 `Challenge` 模型中添加 `order_index` 字段

2. **routes/admin.py**
   - 添加 `challenge_move_up()` 路由 - 向上移动题目
   - 添加 `challenge_move_down()` 路由 - 向下移动题目
   - 修改 `challenges()` 查询按 `order_index` 排序
   - 修改 `challenge_copy()` 复制 `order_index` 值

3. **routes/frontend.py**
   - 修改 `competition_detail()` 查询按 `order_index` 排序

4. **templates/admin/challenges.html**
   - 添加"Order"列显示排序按钮
   - 每道题目显示上下移动按钮

5. **add_challenge_order.py** (新增)
   - 数据库迁移脚本

## 💡 工作原理

### 排序逻辑

**向上移动：**
```
题目A (order_index: 2) 向上移动
题目B (order_index: 1) ← 当前在上面

操作后：
题目A (order_index: 1) ← 交换
题目B (order_index: 2) ← 交换
```

**向下移动：**
```
题目A (order_index: 1) 向下移动
题目B (order_index: 2) ← 当前在下面

操作后：
题目A (order_index: 2) ← 交换
题目B (order_index: 1) ← 交换
```

### 查询顺序

```python
# 前台显示
challenges = Challenge.query.filter_by(
    competition_id=competition_id, 
    is_active=True
).order_by(
    Challenge.order_index.asc(),  # 主要排序
    Challenge.id.asc()             # 次要排序
).all()
```

## ✅ 验证步骤

1. **创建测试题目**
   - 创建 3-5 道题目

2. **调整顺序**
   - 在管理后台使用上下移动按钮
   - 观察列表顺序变化

3. **前台验证**
   - 访问竞赛页面
   - 确认题目按新顺序显示

4. **多竞赛验证**
   - 不同竞赛的题目独立排序
   - 互不影响

## 🎨 界面示例

### 管理后台

```
Order | Title          | Competition | Category | Points | Status | Actions
------|----------------|-------------|----------|--------|--------|----------
 ⬆️⬇️ | 基础题         | CTF 2026    | Web      | 100    | Active | [编辑][复制]...
 ⬆️⬇️ | 进阶题         | CTF 2026    | Web      | 200    | Active | [编辑][复制]...
 ⬆️⬇️ | 高级题         | CTF 2026    | Crypto   | 300    | Active | [编辑][复制]...
```

### 前台显示

```
题目列表（按order_index排序）：
┌─────────────────────────────┐
│ 1. 基础题 - 100分           │
│    [查看题目]               │
└─────────────────────────────┘
┌─────────────────────────────┐
│ 2. 进阶题 - 200分           │
│    [查看题目]               │
└─────────────────────────────┘
┌─────────────────────────────┐
│ 3. 高级题 - 300分           │
│    [查看题目]               │
└─────────────────────────────┘
```

## 🔄 导入导出兼容性

导出竞赛时，`order_index` 会被包含在 JSON 中：

```json
{
  "name": "CTF Competition",
  "challenges": [
    {
      "title": "Challenge 1",
      "order_index": 0,
      ...
    }
  ]
}
```

导入时需要确保导出的 JSON 包含 `order_index` 字段。

## 📊 数据库更改

| 表名 | 字段名 | 类型 | 默认值 | 说明 |
|------|--------|------|--------|------|
| challenges | order_index | INTEGER | 0 | 显示顺序（越小越靠前） |

## 🐛 常见问题

### Q: 如果两道题的 order_index 相同怎么办？
A: 按题目 ID 升序排列（创建时间早的在前）。

### Q: 删除题目后顺序会乱吗？
A: 不会。其他题目的 `order_index` 保持不变。

### Q: 可以批量设置顺序吗？
A: 目前只支持逐个调整。未来可以添加拖拽排序或批量编号功能。

### Q: 不同竞赛的题目顺序互相影响吗？
A: 不会。排序只在同一竞赛内生效。

## 🚀 未来优化

可能的功能增强：
- 拖拽排序（Drag & Drop）
- 批量设置顺序号
- 自动排序（按分数、类别等）
- 竞赛级别的"重置顺序"功能

## ✅ 总结

题目顺序管理功能让管理员完全掌控题目的展示顺序，提供更好的用户体验和故事引导。无需数据库手动操作，通过简单的上下移动按钮即可轻松调整。
