# Telegram MCP 权威版协议覆盖矩阵

> 目标：把 Telegram 的公开协议面系统化映射为 MCP 工具，而不是只做“群发器”。
> 边界：只覆盖 Telegram 官方/公开接口与公开协议；不包含绕风控、盗号、私密接口滥用、垃圾群发、规避封禁等内容。

## 1. 官方协议/接口源

| 协议面 | 官方入口 | 说明 | MCP 实现优先级 |
|---|---|---|---|
| Telegram API / MTProto | https://core.telegram.org/api | 用户账号级能力，Telethon/Pyrogram/TDLib 均基于此 | P0 |
| MTProto 协议 | https://core.telegram.org/mtproto | 加密传输、授权、消息容器、RPC 基础 | P1（解释/诊断，不建议裸实现） |
| TL Schema | https://core.telegram.org/schema | 当前公开 TL schema，约 900 个方法、929 个构造器 | P0（做 coverage 索引） |
| Methods | https://core.telegram.org/methods | 官方方法索引 | P0 |
| Bot API | https://core.telegram.org/bots/api | HTTP Bot 能力，当前页面解析到约 175 个方法 | P0 |
| Bot Features | https://core.telegram.org/bots/features | Bot 能力说明 | P1 |
| TDLib | https://core.telegram.org/tdlib | 官方跨语言客户端库 | P1/P2 |
| Mini Apps / Web Apps | https://core.telegram.org/bots/webapps | Telegram 内嵌应用能力 | P1 |
| Bot Payments | https://core.telegram.org/bots/payments | Bot 支付能力 | P1 |

## 2. TL Schema 命名空间覆盖

当前官方 TL Schema 粗解析：约 **900 methods / 929 constructors**。

| 命名空间 | 方法数 | 推荐 MCP 分类 |
|---|---:|---|
| messages | 294 | 消息、对话、搜索、媒体、草稿、投票、置顶、反应 |
| account | 125 | 账号、隐私、安全、通知、主题、授权会话 |
| payments | 83 | 付款、Stars、发票、收据、礼物 |
| channels | 69 | 频道/超级群、成员、权限、管理日志 |
| phone | 43 | 通话/群组通话 |
| auth | 42 | 登录、验证码、2FA、导出授权 |
| stories | 40 | Stories 发布/读取/互动 |
| help | 39 | 配置、条款、支持、App 信息 |
| bots | 32 | Bot 菜单、Bot 信息、Bot 相关配置 |
| contacts | 31 | 联系人、拉黑、搜索、Top peers |
| chatlists | 16 | 聊天列表/文件夹/邀请 |
| upload | 13 | 文件上传/下载/CDN |
| stats | 12 | 频道/群组统计 |
| stickers | 12 | 贴纸包、表情、收藏 |
| users | 11 | 用户查询与资料 |
| updates | 10 | 差量更新、状态同步 |
| photos | 8 | 头像/照片 |
| premium | 7 | Premium 相关 |
| smsjobs | 5 | SMS Jobs |
| langpack | 5 | 语言包 |
| fragment | 2 | Fragment 相关 |
| folders | 1 | 文件夹 |

## 3. 当前仓库覆盖现状

当前仓库 MCP 工具数量：**154 个**。

- `main.py`: 123 个 Telegram 操作工具
- `account_tools.py`: 31 个账号/代理/健康/批量工具

已有覆盖：

| 分类 | 已有能力 |
|---|---|
| 对话/聊天 | get_chats, get_chat, archive/unarchive, pin/unpin chat |
| 消息 | send/get/reply/edit/delete/forward/copy/search/filter/history |
| 媒体 | photo/video/document/voice/audio/sticker/gif/media_group/download/search |
| 群组/频道 | create_group/create_channel/supergroup, admin, ban, invite, permissions, topics |
| 账号 | get_me/update_profile/status/privacy/username/bio/session |
| 联系人 | get/search/add/delete/block/unblock contacts |
| 搜索 | public/global/date/sender/hashtag/media |
| 计划任务 | schedule_message/create_schedule/list/toggle/delete |
| 代理/健康 | proxy assign/test, health report, risk accounts |

主要缺口：

| 缺口 | 说明 | 优先级 |
|---|---|---|
| Bot API 独立实现 | 现在主要是用户账号 Telethon，缺官方 Bot API HTTP 工具面 | P0 |
| TDLib 模式 | 缺官方 TDLib 后端/可选客户端模式 | P1 |
| Updates 流式订阅 | MCP 资源/通知化不足，不能稳定暴露实时更新 | P0 |
| Business Bot | 缺 business connection/message 能力 | P1 |
| Mini Apps | 缺 WebApp initData 校验、launch params、invoice/link 辅助工具 | P1 |
| Payments/Stars | 只有零散 Telegram API 面，缺 Bot payments 工具组 | P1 |
| Stories | TL Schema 有 stories 40 个方法，当前基本未覆盖 | P1 |
| Admin Log / Audit | 有部分管理操作，缺可审计 admin log 工具组 | P1 |
| Takeout/export | 缺合规数据导出能力与限速机制 | P2 |
| Tool schema 标准化 | 当前 154 工具命名/参数/错误返回不够统一 | P0 |

## 4. 权威版工具分层设计

### 4.1 `telegram.account.*`

账号与授权能力。高危边界：session/token/2FA/设备会话。

- `account.list`
- `account.me`
- `account.health`
- `account.active_sessions.list`
- `account.active_sessions.terminate`
- `account.privacy.get`
- `account.privacy.set`
- `account.profile.update`
- `account.username.set`
- `account.notifications.set`

发布版原则：**不暴露明文 session export**。需要备份时使用本地加密导出 + 二次确认。

### 4.2 `telegram.chats.*`

- `chats.list`
- `chats.get`
- `chats.search_public`
- `chats.join_public`
- `chats.join_invite`
- `chats.leave`
- `chats.archive`
- `chats.pin`
- `chats.invite_link.check`
- `chats.invite_link.create/revoke`

### 4.3 `telegram.messages.*`

- `messages.list`
- `messages.get`
- `messages.search`
- `messages.search_by_sender`
- `messages.search_by_date`
- `messages.send`
- `messages.reply`
- `messages.edit`
- `messages.delete`
- `messages.forward`
- `messages.copy`
- `messages.pin`
- `messages.mark_read`
- `messages.react`
- `messages.schedule`

约束：发送类默认 `destructiveHint=true`，发布版应支持 dry-run、速率限制、目标白名单、人工确认。

### 4.4 `telegram.media.*`

- `media.send_photo/video/document/audio/voice/sticker/gif`
- `media.send_group`
- `media.download`
- `media.search`
- `media.save`
- `media.chat_photos.list`
- `media.chat_photo.set/delete`

约束：所有本地文件路径必须限制到允许目录，避免读取任意本机文件。

### 4.5 `telegram.groups.*` / `telegram.channels.*`

- `groups.create`
- `groups.members.list`
- `groups.admins.list`
- `groups.admin.promote/demote/edit_rights`
- `groups.member.ban/unban/restrict`
- `groups.permissions.set`
- `groups.slowmode.set`
- `groups.topics.create/list/edit/delete`
- `channels.create/edit/delete`
- `channels.stats.get`
- `channels.post_stats.get`
- `channels.admin_log.list`

### 4.6 `telegram.contacts.*`

- `contacts.list`
- `contacts.search`
- `contacts.import`
- `contacts.delete`
- `contacts.block/unblock`

约束：手机号/联系人属于 PII，默认脱敏。

### 4.7 `telegram.bots.*`（Bot API）

Bot API 应独立于用户账号工具，走 HTTP `https://api.telegram.org/bot<TOKEN>/<method>`。

核心组：

- Updates: `getUpdates`, `setWebhook`, `deleteWebhook`, `getWebhookInfo`
- Bot identity: `getMe`, `logOut`
- Send: `sendMessage`, `sendPhoto`, `sendDocument`, `sendVideo`, `sendMediaGroup`, `sendPoll`, `sendDice`
- Edit/Delete: `editMessageText`, `editMessageMedia`, `deleteMessage`, `deleteMessages`
- Callback: `answerCallbackQuery`
- Inline: `answerInlineQuery`, `savePreparedInlineMessage`
- Chat admin: `banChatMember`, `restrictChatMember`, `promoteChatMember`, `setChatPermissions`
- Invite/join: `createChatInviteLink`, `approveChatJoinRequest`
- Business: `getBusinessConnection`, business message APIs
- Payments: `sendInvoice`, `createInvoiceLink`, `answerShippingQuery`, `answerPreCheckoutQuery`, `refundStarPayment`
- Mini Apps: initData 校验、WebApp 数据解析、deep link 生成

### 4.8 `telegram.updates.*`

权威版必须支持实时事件：

- `updates.subscribe`
- `updates.poll`
- `updates.get_state`
- `updates.diff`
- `updates.watch_chat`
- `updates.watch_mentions`

MCP 形态：建议用 resource/notification，而不是只返回一次性字符串。

### 4.9 `telegram.protocol.*`

用于权威性和教学，不直接发请求：

- `protocol.tl_schema.search`
- `protocol.tl_method.describe`
- `protocol.coverage.report`
- `protocol.method_map.telethon`
- `protocol.method_map.botapi`

这组能把项目包装成“最权威 Telegram MCP”，因为它不仅能操作，还能解释 Telegram 协议面。

## 5. Tool Schema 标准

每个工具统一返回：

```json
{
  "ok": true,
  "data": {},
  "meta": {
    "account_id": "default",
    "backend": "telethon|bot_api|tdlib",
    "method": "messages.sendMessage|sendMessage",
    "rate_limit": {"bucket": "messages.send", "remaining": 0},
    "request_id": "..."
  },
  "warnings": []
}
```

错误统一返回：

```json
{
  "ok": false,
  "error": {
    "code": "FLOOD_WAIT|SESSION_REQUIRED|PERMISSION_DENIED|NOT_FOUND|VALIDATION_ERROR",
    "message": "...",
    "retry_after": 0
  },
  "meta": {}
}
```

## 6. 发布版安全底线

发布前必须满足：

1. 无明文 `.telegram_session` / `*.session` / session string。
2. Dashboard 默认只监听 `127.0.0.1`。
3. 所有 Web API / WebSocket 强制鉴权。
4. Session 导出默认禁用。
5. CORS 禁止 `* + credentials`。
6. 发送/邀请/加群/删号/导出类工具必须 `destructiveHint=true` 并支持确认/限额。
7. 文件上传/下载路径限制到 allowlist 目录。
8. 日志脱敏手机号、二维码 URL、2FA hint、session、token。
9. Bot token / API hash / 代理密码只读环境变量或加密存储。
10. README 明确合法使用边界：仅用于自有账号、授权管理、公开频道/群组运营、Bot 管理与研究。

## 7. 发布定位

建议项目名：**Telegram MCP Ultimate / Telegram MCP Complete**。

一句话：

> The most complete and protocol-aware Telegram MCP server, covering MTProto user accounts, Bot API, channels, groups, media, updates, admin tools and protocol documentation.

中文：

> 最完整、最懂 Telegram 协议的 MCP Server：覆盖 MTProto 用户账号、Bot API、频道/群组、消息媒体、实时更新、管理工具与协议文档索引。
