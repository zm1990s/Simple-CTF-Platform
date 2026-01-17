# 竞赛/题目导出导入功能实现总结

## 已完成功能

### 1. 后端路由 (routes/admin.py)

新增了以下路由：

#### `/admin/competitions/<id>/export` - 导出单个竞赛
- 导出竞赛元数据和所有题目
- 生成 JSON 格式文件
- 文件名格式: `competition_name_export_YYYYMMDD_HHMMSS.json`

#### `/admin/competitions/import` - 导入竞赛
- GET: 显示导入表单
- POST: 处理上传的 JSON 文件
- 创建竞赛和所有题目
- 导入的竞赛状态为 "draft"（草稿）
- 包含错误处理和事务回滚

#### `/admin/challenges/<id>/export` - 导出单个题目
- 导出题目元数据
- 包含原始竞赛名称
- JSON 格式

#### `/admin/competitions/export-all` - 导出所有竞赛
- 将所有竞赛打包成 ZIP 文件
- 每个竞赛一个 JSON 文件
- 文件名格式: `all_competitions_export_YYYYMMDD_HHMMSS.zip`

### 2. 前端界面

#### templates/admin/competition_import.html (新建)
- 文件上传表单
- 导入说明信息
- 响应式设计
- 支持中英文

#### templates/admin/competitions.html (修改)
- 顶部添加 "导出全部" 按钮
- 顶部添加 "导入" 按钮
- 每个竞赛添加 "导出" 按钮

#### templates/admin/challenges.html (修改)
- 每个题目添加 "导出" 按钮

### 3. 国际化支持 (translations.json)

新增翻译项：
- Export / 导出
- Import / 导入
- Export All / 导出全部
- Import Competition / 导入竞赛
- Select JSON File / 选择 JSON 文件
- Upload a competition export file (.json) / 上传竞赛导出文件 (.json)
- Import Information / 导入说明
- The competition will be created in draft status / 竞赛将以草稿状态创建
- All challenges from the export will be imported / 导出文件中的所有题目都将被导入
- Challenge files are not included in basic JSON exports / 基本 JSON 导出不包含题目文件

## 导出文件格式

### 竞赛导出格式

```json
{
  "name": "竞赛名称",
  "description": "竞赛描述",
  "countdown_minutes": 60,
  "export_date": "2024-01-15T10:30:00",
  "challenges": [
    {
      "title": "题目标题",
      "description": "题目描述",
      "points": 100,
      "category": "Web",
      "is_active": true
    }
  ]
}
```

### 题目导出格式

```json
{
  "title": "题目标题",
  "description": "题目描述",
  "points": 100,
  "category": "Web",
  "is_active": true,
  "competition_name": "所属竞赛",
  "export_date": "2024-01-15T10:30:00"
}
```

## 使用场景

1. **跨平台迁移**
   - 开发环境 → 生产环境
   - 服务器迁移
   - 创建多个平台实例

2. **备份与归档**
   - 定期备份竞赛数据
   - 归档已完成的竞赛
   - 保存竞赛模板

3. **题目共享**
   - 与其他 CTF 组织者分享题目
   - 创建题目库
   - 分发题目集

4. **快速部署**
   - 使用模板快速创建竞赛
   - 复用优质竞赛结构
   - 批量创建类似竞赛

## 功能特点

### 安全性
- 导入前验证 JSON 格式
- 数据库事务保护（失败自动回滚）
- 导入的竞赛默认为草稿状态
- 文件名安全处理（secure_filename）

### 用户体验
- 清晰的导入说明
- 友好的错误提示
- 直观的按钮图标
- 中英文完整支持

### 数据完整性
- 导出包含所有竞赛元数据
- 包含所有关联题目
- 保留题目分类和分值
- 记录导出时间戳

## 当前限制

1. **不包含文件**
   - 基本 JSON 导出不包含题目描述图片
   - 不包含附件文件
   - 文件需要手动上传

2. **不包含提交历史**
   - 只导出竞赛结构
   - 不包含用户提交记录
   - 不包含评分历史

3. **ID 会改变**
   - 导入后会生成新的数据库 ID
   - 不保留原始 ID

## 技术实现

### 依赖项
```python
import json
import zipfile
from io import BytesIO
from flask import send_file
from werkzeug.utils import secure_filename
```

### 关键功能
- `send_file()` - 发送文件下载
- `BytesIO()` - 内存中创建文件
- `zipfile.ZipFile()` - 创建 ZIP 压缩包
- `secure_filename()` - 文件名安全处理
- `db.session.flush()` - 获取新创建对象的 ID
- `db.session.rollback()` - 错误时回滚事务

## 文档

- `EXPORT_IMPORT.md` - 完整的功能文档（英文）
- `IMPLEMENTATION_SUMMARY.md` - 本实现总结（中文）

## 测试建议

1. **单个竞赛导出**
   - 创建测试竞赛
   - 添加多个题目
   - 导出并检查 JSON 格式

2. **竞赛导入**
   - 导入导出的 JSON 文件
   - 验证竞赛和题目都已创建
   - 检查所有字段是否正确

3. **全部导出**
   - 创建多个竞赛
   - 导出全部
   - 检查 ZIP 文件内容

4. **错误处理**
   - 上传非 JSON 文件
   - 上传格式错误的 JSON
   - 上传缺少必需字段的 JSON

## 未来改进

1. **包含文件** - ZIP 导出中包含题目图片和附件
2. **批量题目导入** - 一次导入多个独立题目
3. **部分导入** - 选择性导入竞赛中的部分题目
4. **导入预览** - 导入前预览将要创建的内容
5. **导出历史** - 记录导出操作历史
6. **自动备份** - 定时自动导出竞赛

## 总结

成功实现了完整的竞赛/题目导出导入功能，支持：
- ✅ 单个竞赛导出
- ✅ 全部竞赛导出（ZIP）
- ✅ 竞赛导入
- ✅ 单个题目导出
- ✅ 完整的 UI 集成
- ✅ 中英文支持
- ✅ 错误处理
- ✅ 完整文档

该功能为 CTF 平台提供了强大的跨平台迁移和备份能力。
