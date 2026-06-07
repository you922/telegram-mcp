# Telegram MCP 权威版发布计划

## 结论

当前仓库功能数量已经很强：154 个 MCP tools，覆盖聊天、消息、媒体、群组、频道、联系人、账号、代理、健康、计划任务等主干能力。

但它现在还不是“权威版”，主要差在三点：

1. **安全边界不够发布级**：session 明文、后台无鉴权、CORS 全开、导出 session 接口。
2. **协议覆盖不够系统**：主要是 Telethon 用户账号能力，缺 Bot API / TDLib / Business / Mini Apps / Payments / Stories 的系统化覆盖。
3. **工具形态不够标准**：154 个工具已有规模，但返回结构、命名、错误码、权限提示、速率限制、审计还不统一。

## P0：发布前必须修

| 项 | 文件/范围 | 目标 |
|---|---|---|
| 删除明文 session | `.telegram_session`, accounts 配置 | 不允许任何 session 进入仓库/日志 |
| Web 后台鉴权 | `dashboard.py` | API/WS 全部 require admin token |
| 默认本地监听 | `dashboard.py` | `127.0.0.1`，公网必须显式开启 |
| 禁用 Session 导出 | `dashboard.py`, `account_tools.py` | 默认移除/隐藏，或二次确认 + 加密导出 |
| CORS 收紧 | `dashboard.py`, `web_login.py`, `qr_web_login.py` | 禁止 `allow_origins=["*"]` + credentials |
| 统一加密 session | `account_manager.py` | QR/手机号/session 添加全路径加密 |
| 日志脱敏 | `main.py`, `dashboard.py`, `log_manager.py` | 不记录 QR URL、手机号、2FA hint、token |
| 文件路径沙箱 | `main.py` | send/download/export 统一 validate path |

## P1：权威版核心增强

### 1. 协议索引工具

新增 `telegram.protocol.*`：

- `protocol.namespaces.list`
- `protocol.methods.search`
- `protocol.method.describe`
- `protocol.bot_api.search`
- `protocol.coverage.report`

价值：让仓库从“能操作 Telegram”升级成“懂 Telegram 协议”。

### 2. Bot API 后端

新增独立模块：

```text
telegram_mcp/
  backends/
    telethon_backend.py
    bot_api_backend.py
    tdlib_backend.py
  tools/
    bot_updates.py
    bot_messages.py
    bot_admin.py
    bot_payments.py
    bot_business.py
```

第一批 Bot API 工具：

- `bot.get_me`
- `bot.get_updates`
- `bot.set_webhook`
- `bot.send_message`
- `bot.send_photo`
- `bot.edit_message_text`
- `bot.delete_message`
- `bot.answer_callback_query`
- `bot.create_invoice_link`
- `bot.get_business_connection`

### 3. Updates 实时化

把 Telegram updates 做成 MCP resource/notification：

- 订阅某账号/某聊天/某关键词
- 输出标准事件：`message.new`, `message.edited`, `message.deleted`, `reaction.updated`, `member.joined`, `member.left`, `channel.posted`
- 支持 offset/state/checkpoint

### 4. Tool schema 统一

所有工具统一：

- `ok/data/error/meta/warnings`
- 错误码标准化
- destructive/readOnly/idempotent/openWorld hints 正确标注
- flood wait 自动结构化返回 `retry_after`

## P2：高级能力

| 能力 | 说明 |
|---|---|
| TDLib backend | 作为官方库模式，适合生产稳定运行 |
| Stories | stories.* 约 40 个 TL 方法，补 Stories 读写/互动 |
| Payments/Stars | Bot payments + Telegram Stars 能力 |
| Mini Apps | initData 校验、deep link、launch params、invoice link |
| Admin Log | 频道/群组审计日志工具 |
| Takeout | 合规导出，强限速 |
| Coverage dashboard | 展示 TL Schema / Bot API 覆盖率 |

## README 发布结构

建议 README 顶部结构：

1. DreamSeed 头图（已加）
2. 项目一句话定位
3. 协议覆盖徽章：MTProto / Bot API / TDLib / Mini Apps / Payments
4. 安全边界声明
5. 154+ Tools 展示
6. 权威协议矩阵链接
7. 快速开始
8. 工具分类表
9. 合法使用边界
10. Roadmap

## GitHub Star 包装标题

可用标题：

- `Telegram MCP Ultimate: 154+ Tools for MTProto, Bot API, Channels, Groups and Media`
- `The Most Complete Telegram MCP Server for Claude, Cursor and AI Agents`
- `Protocol-Aware Telegram MCP: MTProto + Bot API + Admin + Media + Updates`
- `AI Agent 操作 Telegram 的最强 MCP：154+ 工具，覆盖账号、频道、群组、媒体和实时消息`

## 合法边界文案

建议 README 放这段：

> This project is designed for managing your own Telegram accounts, bots, channels and groups, or systems you are explicitly authorized to operate. It does not support spam, credential theft, bypassing Telegram restrictions, account takeover, or unauthorized data access.

中文：

> 本项目仅用于管理你本人或明确授权的 Telegram 账号、Bot、频道和群组。禁止用于垃圾信息、盗号、绕过 Telegram 限制、未授权数据访问或任何违法用途。

## 最终发布标准

达到以下状态再对外强推：

- [ ] 安全 P0 全部修完
- [ ] README 展示 154+ tools + 协议覆盖矩阵
- [ ] Bot API 至少 20 个核心工具上线
- [ ] protocol coverage 工具上线
- [ ] 所有 destructive 工具支持确认/限额/审计
- [ ] CI 测试通过
- [ ] 无 secrets/session 历史泄漏
- [x] 发布 v1.1.0 tag
