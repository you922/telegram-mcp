# Bug 修复总结

本文档记录了对 Telegram 多账号管理系统的所有 bug 修复和改进。

## 修复的问题

### 1. 定时任务接口错位问题 ✅
**问题描述**: `dashboard.py` 向 `task_scheduler.add_schedule` 传递 `account_ids` 参数，但调度器只接收 `accounts` 参数；调用不存在的 `delete_schedule`/`get_next_run` 方法。

**修复内容**:
- `scheduler.py:57-69` - 添加 `account_ids` 参数支持，兼容两种参数名
- `scheduler.py:128-137` - 添加 `delete_schedule` 和 `get_next_run` 方法
- `scheduler.py:95-114` - 数据结构同时包含 `id`/`schedule_id` 和 `last_run`/`lastRun` 字段
- `scheduler.py:154-170` - `list_schedules` 方法确保返回所有前端需要的字段

### 2. 定时任务目标无效问题 ✅
**问题描述**: 前端硬编码 `target: 'all'`，但 Telethon 无法解析该实体，任何计划都会报错。

**修复内容**:
- `scheduler.py:174-175` - 将 `'all'` 转换为 `'me'`（Saved Messages），使消息发送到自己的收藏夹

### 3. 模板 ID 不一致问题 ✅
**问题描述**: 模板持久化时字段叫 `id`，前端期望 `template_id`，导致删除模板、选择模板等功能失败。

**修复内容**:
- `template_manager.py:68-77` - 同时保存 `id` 和 `template_id` 字段
- `template_manager.py:82-89` - `get_template` 方法确保返回 `template_id` 字段
- `template_manager.py:91-110` - `list_templates` 方法确保返回所有模板都包含 `template_id` 字段
- `static/dashboard.html:868,1318` - 前端同时支持 `template_id` 和 `id` 字段

### 4. 日志功能显示错误及无法清空问题 ✅
**问题描述**:
- 日志记录字段叫 `time`，前端解析 `timestamp`
- 返回最旧的记录而非最新的
- 清空按钮只清空本地数组，未调用 API

**修复内容**:
- `log_manager.py:50-58` - 同时保存 `time` 和 `timestamp` 字段
- `log_manager.py:86-89` - 返回最新记录而非最旧
- `static/dashboard.html:570` - 清空按钮调用 `clearLogs` 方法
- `static/dashboard.html:1007-1016` - 添加 `clearLogs` 方法调用 `/api/logs/clear`
- `static/dashboard.html:577` - 移除重复的 `reverse()`

### 5. 统计与健康监控未接入 ✅
**问题描述**:
- `stats_tracker.record_use` 从未被调用
- `health_monitor.start_monitoring` 从未被调用
- `/api/health/report` 缺少前端需要的 `risk_accounts` 字段

**修复内容**:
- `dashboard.py:59-61` - 在 `lifespan` 中启动健康监控（每5分钟检查一次）
- `dashboard.py:66-67` - 关闭时停止健康监控
- `health_monitor.py:152-165` - 添加 `risk_accounts` 字段到健康报告
- `dashboard.py:140,167,200` - 在关键操作处添加 `stats_tracker.record_use` 调用

### 6. 代理配置形同虚设 ✅
**问题描述**:
- `account_manager.get_client` 不自动读取 `proxy_manager`
- `health_monitor.check_account_health` 将账号 ID 当作代理 ID 查找

**修复内容**:
- `account_manager.py:478-481` - `get_client` 自动从 `proxy_manager` 获取代理配置
- `health_monitor.py:193-206` - 修复代理查找逻辑，正确获取账号关联的代理

### 7. 批量 API 请求体声明错误 ✅
**问题描述**: `/api/batch/check-health` 和 `/api/batch/export-sessions` 的 `account_ids` 参数被声明为普通形参，POST 请求体被忽略。

**修复内容**:
- `dashboard.py:647-660` - 将参数改为从请求体读取 `account_ids`

### 8. 日志和监控覆盖不足 ✅
**问题描述**: 账号增删、代理设置、模板操作等都没有日志记录。

**修复内容**:
- `dashboard.py:180,201,251,262,278,288,301,486,497,559,570,584` - 在各 API 端点添加 `log_manager.add_log` 调用
- 所有操作现在都会被正确记录到 `logs.json`

## 数据结构兼容性

为确保前后端兼容性，所有数据结构现在同时包含：
- `id` 和 `schedule_id`/`template_id`（用于定时任务和模板）
- `last_run` 和 `lastRun`（驼峰命名）
- `accounts` 和 `account_ids`（账号列表）
- `time` 和 `timestamp`（日志时间戳）

## 启动说明

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python3 dashboard.py

# 访问管理界面
# http://localhost:8080/static/dashboard.html
```

## API 端点

### 账号管理
- `GET /api/accounts` - 获取账号列表
- `POST /api/accounts/generate-qr` - 生成二维码登录
- `GET /api/accounts/{account_id}/qr-status` - 获取二维码状态
- `POST /api/accounts/{account_id}/2fa-password` - 提交两步验证密码
- `DELETE /api/accounts/{account_id}` - 删除账号
- `POST /api/accounts/add-session` - 使用 Session 添加账号
- `GET /api/accounts/{account_id}/export-session` - 导出 Session

### 代理管理
- `GET /api/proxies` - 获取代理列表
- `POST /api/proxies/add` - 添加代理
- `DELETE /api/proxies/{proxy_id}` - 删除代理
- `POST /api/proxies/set-global` - 设置全局代理
- `DELETE /api/proxies/global` - 移除全局代理
- `POST /api/proxies/assign` - 为账号分配代理
- `DELETE /api/proxies/{proxy_id}/accounts/{account_id}` - 取消代理分配
- `POST /api/proxies/test` - 测试代理

### 健康监控
- `GET /api/health/report` - 获取健康报告
- `POST /api/health/check/{account_id}` - 检查账号健康状态
- `GET /api/health/risk-accounts` - 获取高风险账号列表

### 统计
- `GET /api/stats/summary` - 获取统计摘要
- `GET /api/stats/account/{account_id}` - 获取账号统计
- `GET /api/stats/daily` - 获取每日统计
- `GET /api/stats/weekly` - 获取每周统计
- `GET /api/stats/top` - 获取最活跃账号
- `GET /api/stats/trend/{account_id}` - 获取活跃度趋势

### 日志
- `GET /api/logs` - 获取操作日志
- `GET /api/logs/stats` - 获取日志统计
- `POST /api/logs/clear` - 清空日志

### 模板
- `GET /api/templates` - 获取模板列表
- `POST /api/templates` - 添加模板
- `DELETE /api/templates/{template_id}` - 删除模板
- `GET /api/templates/{template_id}/preview` - 预览模板

### 定时任务
- `GET /api/schedules` - 获取定时任务列表
- `POST /api/schedules` - 添加定时任务
- `DELETE /api/schedules/{schedule_id}` - 删除定时任务
- `POST /api/schedules/{schedule_id}/toggle` - 切换任务状态
- `GET /api/schedules/{schedule_id}/next-run` - 获取下次执行时间

### 批量操作
- `POST /api/batch/send-message` - 批量发送消息
- `POST /api/batch/send-template` - 批量发送模板消息
- `POST /api/batch/check-health` - 批量检查账号健康状态
- `POST /api/batch/export-sessions` - 批量导出 Session
- `POST /api/batch/delete-accounts` - 批量删除账号
- `POST /api/batch/get-dialogs` - 批量获取对话列表

## 配置文件

所有配置文件存储在 `./accounts/` 目录：
- `config.json` - 账号配置
- `proxies.json` - 代理配置
- `templates.json` - 消息模板
- `schedules.json` - 定时任务
- `logs.json` - 操作日志
- `health.json` - 健康数据
- `stats.json` - 统计数据

## WebSocket

实时状态推送端点：`ws://localhost:8080/ws`

每 5 秒推送一次状态更新，包含：
- 账号列表
- 健康报告
- 统计摘要
