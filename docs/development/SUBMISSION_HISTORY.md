# 竞赛重置历史记录功能说明

## 功能概述

现在重置竞赛时，所有提交记录和评分将被保存到历史记录表中，而不是直接删除。这样可以保留完整的数据用于后续分析和审计。

## 数据库更改

### 新增表

1. **submission_history** - 归档的提交记录
   - original_submission_id: 原始提交ID
   - answer_text: 答案文本
   - status: 状态 (pending/approved/rejected)
   - points_awarded: 获得分数
   - submitted_at: 提交时间
   - reviewed_at: 审核时间
   - archived_at: 归档时间
   - user_id: 用户ID
   - challenge_id: 题目ID
   - competition_id: 竞赛ID
   - reviewed_by_id: 审核人ID

2. **submission_file_history** - 归档的提交文件记录
   - original_file_id: 原始文件ID
   - filename: 文件名
   - filepath: 文件路径
   - uploaded_at: 上传时间
   - archived_at: 归档时间
   - submission_history_id: 对应的历史提交ID

### 索引
- competition_id 索引：快速按竞赛查询
- user_id 索引：快速按用户查询
- archived_at 索引：按归档时间排序
- submission_history_id 索引：快速关联文件

## 迁移步骤

运行迁移脚本创建历史记录表：

```bash
docker compose exec web python migrate_submission_history.py
```

## 新增功能

### 1. 管理后台菜单
- 在管理控制台添加了"Submission History"（提交历史）入口
- 可以快速访问所有归档的提交记录

### 2. 历史记录列表页面
- 路径: `/admin/submission-history`
- 功能:
  - 查看所有归档的提交记录
  - 按竞赛筛选
  - 显示提交状态、分数、时间等信息
  - 点击查看详细信息

### 3. 历史记录详情页面
- 路径: `/admin/submission-history/<id>`
- 功能:
  - 查看完整的提交信息
  - 查看答案文本
  - 查看提交的文件（保留原文件）
  - 查看题目详情
  - 查看审核信息

### 4. 竞赛重置功能更新
- 重置竞赛时自动归档所有提交
- 保留所有文件（不删除物理文件）
- 显示归档数量的提示信息

## 使用场景

1. **数据审计**: 查看历史竞赛的所有提交记录
2. **成绩分析**: 分析用户在不同竞赛中的表现
3. **问题追溯**: 当用户反馈问题时可以查看历史提交
4. **统计报告**: 生成历史数据的统计报告

## 注意事项

1. **文件存储**: 归档的提交文件仍然保留在 uploads 目录中，不会被删除
2. **数据隐私**: 历史记录只有管理员可以访问
3. **存储空间**: 长期运行后历史记录会占用较多空间，建议定期备份后清理旧数据
4. **性能考虑**: 查询大量历史记录时可能较慢，已添加必要的索引优化

## 未来改进建议

1. 添加导出功能（CSV/Excel）
2. 添加批量删除旧历史记录的功能
3. 添加更多筛选条件（用户、状态、时间范围等）
4. 添加数据统计图表
5. 支持历史记录的全文搜索
