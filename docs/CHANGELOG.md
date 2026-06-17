# 更新日志 / Changelog

本文件记录 CTF Platform 的功能演进与重要修复。条目按时间倒序排列。

> 仅保留对使用与运维有影响的变更摘要；具体实现细节请直接参考代码与提交记录。

---

## 2026-06 — 组队、PIN 码、Dify 优化

### 新增 / Added
- **组队功能**：用户可创建战队、邀请加入；排行榜支持「个人榜 / 战队榜」两种视角。
- **竞赛 PIN 码**：管理员可为竞赛设置 PIN 码以限制访问；空 PIN 表示公开竞赛。
- **题目级 Dify 工作流**：每道题可独立配置 Hook URL 与 API Key，未配置时回退到全局 `DIFY_API_KEY`。
- **提交内容查看**：用户可在「我的提交」中查看每次提交的完整答案文本与上传图片。

### 优化 / Changed
- **Dify 接口调用**：超时与重试更稳健；对长答复与图片附件处理更可靠；错误日志更完整。
- **管理员审核界面**：Dify 返回的 `score` 与 `feedback` 直接展示，作为人工复核参考。

### 修复 / Fixed
- 用户提交详情页面无法查看历史提交内容的问题。

---

## 2026-01 — 自动审核与排行榜规则

### Dify 自动审核逻辑更新
- 旧逻辑要求 `success=true` 且 `auto_approved=true` 才会自动审核，导致明显错误的答案也要人工拒绝。
- 新逻辑：只要 `auto_approved=true`，根据 `success` 自动决定 `approved` / `rejected`；`auto_approved=false` 时保持 `pending` 等待人工审核。
- 三种模式总览：

  | Dify 返回 | 状态 | 得分 | 审核人 |
  |---|---|---|---|
  | `success=true, auto_approved=true` | `approved` | Dify 的 `score` | AI |
  | `success=false, auto_approved=true` | `rejected` | 0 | AI |
  | `auto_approved=false` | `pending` | 0 | - |

- **无需数据库迁移**，重启 `web` 与 `celery` 服务即可生效。

### 排行榜计分规则修正
- 旧逻辑会把同一用户对同一题目的全部 `approved` 提交分数累加，违反 CTF 标准规则。
- 新逻辑：每个用户对每道题**只计最高分**，所有提交记录依然完整保留。
- 影响：`/leaderboard/<competition_id>`、`/api/leaderboard/<competition_id>` 及首页排行榜预览。
- **无需数据库迁移**，重启 `web` 即可生效。

---

## 2026-01 — 题目顺序

### 题目顺序管理
- `challenges` 表新增 `order_index` 字段（默认 0），值越小越靠前。
- 管理后台「管理题目」页面提供 ⬆️ / ⬇️ 调序按钮。
- 前台与排行榜按 `order_index` 升序、`id` 升序展示，保证顺序稳定。
- 数据库迁移：执行 `python add_challenge_order.py`（容器内 `docker exec ctf_web python add_challenge_order.py`），完成后重启服务。

### `order_index` 在克隆 / 导入 / 导出中的修复
- 修复了 `competition_duplicate` / `competition_export` / `competitions_export_all` / `competition_import` 不带 `order_index` 的问题。
- 旧导出文件不含 `order_index`，导入时会按数组下标自动赋值；新导出文件保留原始顺序。
- 之前克隆出的竞赛全部为默认值 0，可在后台手动调整顺序，或删除后重新克隆。

---

## 导出 / 导入

竞赛与题目支持导出为 JSON、批量导出为 ZIP，并支持从 JSON 导入。详情参见 [export-import.md](export-import.md)。
