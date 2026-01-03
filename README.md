<div align="center">

# Telegram MCP Complete

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Protocol-orange.svg)](https://modelcontextprotocol.io/)

**功能完整的 Telegram MCP 服务器 + 可视化管理后台**

支持 AI 通过 117+ 工具操作 Telegram，同时提供 Web Dashboard 进行可视化管理

[功能特性](#-核心特性) • [快速开始](#-快速开始) • [文档](#-文档) • [截图](#-界面预览)

</div>

---

## 核心特性

### 🤖 MCP 服务器
- **117 个工具** - 覆盖 Telegram 所有常用操作
- **智能代理** - AI 可像真人一样操作账号
- **多账号管理** - 同时管理多个 Telegram 账号
- **Session 复用** - Dashboard 添加的账号，AI 直接可用

### 🌐 Web Dashboard
- **可视化界面** - 直观的账号管理面板
- **多种登录方式** - 二维码登录 + 手机号验证码登录（支持 177 个国家/地区）
- **代理管理** - 全局代理 + 独立代理分配
- **健康监控** - 实时监控账号状态和风险
- **定时任务** - Cron 表达式支持，自动化消息发送
- **消息模板** - 变量替换，批量发送

### 🔐 安全可靠
- **本地存储** - Session 仅保存在本地
- **2FA 支持** - 两步验证密码保护
- **代理支持** - HTTP/SOCKS5 代理，保护隐私
- **风险监控** - 登录失败追踪，风险账号识别

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/telegram-mcp-complete.git
cd telegram-mcp-complete
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动 Dashboard（推荐）

```bash
python3 dashboard.py
```

访问 http://localhost:8080/static/dashboard.html

![Dashboard 登录界面](docs/images/dashboard-login.png)

### 4. 添加账号

**方式一：二维码登录**

1. 点击"添加账号" → "二维码登录"
2. 用手机 Telegram 扫描二维码
3. 等待登录完成

**方式二：手机号登录**

1. 选择国家/地区（支持 177 个国家）
2. 输入手机号
3. 输入验证码
4. 如有 2FA，输入两步验证密码

### 5. 配置 Claude Code

编辑配置文件：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "telegram": {
      "command": "python3",
      "args": ["/path/to/telegram-mcp-complete/main.py"]
    }
  }
}
```

### 6. 开始使用

重启 Claude Code，然后：

```
你: 查看我的 Telegram 聊天列表
AI: [调用 get_chats 工具]

你: 给 @username 发消息说你好
AI: [调用 send_message 工具]

你: 创建一个群组叫"测试群"
AI: [调用 create_group 工具]
```

---

## 界面预览

### Dashboard 主界面

![Dashboard 主界面](docs/images/dashboard-main.png)

### 账号管理

- 多账号管理，状态实时监控
- 批量操作：发送消息、检查健康、导出 Session
- 代理分配，每个账号独立代理

### 定时任务

- Cron 表达式配置
- 消息发送、模板消息
- 执行历史记录

### 健康监控

- 登录失败追踪
- 代理响应时间
- 风险账号识别

---

## MCP 工具列表

### 💬 聊天管理 (6 个)
| 工具 | 描述 |
|------|------|
| `get_chats` | 获取聊天列表（分页） |
| `search_chat` | 搜索公开群组/频道 |
| `get_chat` | 获取聊天详情 |
| `join_channel` | 加入公开频道 |
| `leave_chat` | 离开聊天 |
| `get_dialogs` | 获取对话列表 |

### 📝 消息操作 (39 个)
| 工具 | 描述 |
|------|------|
| `send_message` | 发送消息 |
| `reply_message` | 回复消息 |
| `edit_message` | 编辑消息 |
| `delete_message` | 删除消息 |
| `forward_message` | 转发消息 |
| `pin_message` | 置顶消息 |
| `unpin_message` | 取消置顶 |
| `mark_read` | 标记已读 |
| `search_messages` | 搜索消息 |
| `send_photo` | 发送图片 |
| `send_video` | 发送视频 |
| `send_file` | 发送文件 |
| `download_media` | 下载媒体 |
| ... | |

### 👥 联系人管理 (10 个)
| 工具 | 描述 |
|------|------|
| `get_contacts` | 获取联系人列表 |
| `search_contacts` | 搜索联系人 |
| `add_contact` | 添加联系人 |
| `delete_contact` | 删除联系人 |
| `block_user` | 拉黑用户 |
| `unblock_user` | 解除拉黑 |
| ... | |

### 👥 群组管理 (17 个)
| 工具 | 描述 |
|------|------|
| `create_group` | 创建群组 |
| `get_members` | 获取群组成员 |
| `get_admins` | 获取管理员列表 |
| `invite_to_chat` | 邀请进群 |
| `promote_admin` | 提升管理员 |
| `demote_admin` | 降级管理员 |
| `ban_user` | 封禁用户 |
| `unban_user` | 解除封禁 |
| `get_invite_link` | 获取邀请链接 |
| ... | |

### 📊 媒体操作 (19 个)
| 工具 | 描述 |
|------|------|
| `send_photo` | 发送图片 |
| `send_video` | 发送视频 |
| `send_file` | 发送文件 |
| `send_voice` | 发送语音 |
| `send_audio` | 发送音频 |
| `download_media` | 下载媒体 |
| `get_chat_photos` | 获取聊天图片 |
| `set_chat_photo` | 设置群组头像 |
| ... | |

### 👤 个人资料 (18 个)
| 工具 | 描述 |
|------|------|
| `get_me` | 获取我的信息 |
| `update_profile` | 更新资料 |
| `get_user_status` | 获取用户状态 |
| `mute_chat` | 静音聊天 |
| `unmute_chat` | 取消静音 |
| ... | |

完整工具列表请查看 [TOOLS.md](docs/TOOLS.md)

---

## Dashboard API

### 账号管理
```bash
# 获取账号列表
GET /api/accounts

# 生成二维码登录
POST /api/accounts/generate-qr
{"account_id": "account_001"}

# 获取二维码状态
GET /api/accounts/{account_id}/qr-status

# 导出 Session
GET /api/accounts/{account_id}/export-session
```

### 代理管理
```bash
# 获取代理列表
GET /api/proxies

# 添加代理
POST /api/proxies/add
{
  "proxy_id": "proxy_001",
  "protocol": "socks5",
  "host": "127.0.0.1",
  "port": 1080
}

# 设置全局代理
POST /api/proxies/set-global
```

### 健康监控
```bash
# 获取健康报告
GET /api/health/report

# 检查账号健康
POST /api/health/check/{account_id}
```

完整 API 文档：http://localhost:8080/docs

---

## 配置说明

### 环境变量

创建 `.env` 文件：

```bash
# Telegram API 凭证（可选，使用内置凭证可留空）
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Dashboard 配置
DASHBOARD_PORT=8080
DASHBOARD_HOST=0.0.0.0
```

### 代理配置

**全局代理**（所有账号使用）：
```json
{
  "global": {
    "protocol": "socks5",
    "host": "127.0.0.1",
    "port": 1080
  }
}
```

**独立代理**（特定账号使用）：
```json
{
  "proxies": {
    "proxy_001": {
      "protocol": "http",
      "host": "proxy.example.com",
      "port": 8080,
      "assigned_to": ["account_001", "account_002"]
    }
  }
}
```

---

## 项目结构

```
telegram-mcp-complete/
├── main.py                  # MCP 服务器 (111KB)
├── dashboard.py             # FastAPI Dashboard (27KB)
├── account_manager.py       # 账号管理
├── proxy_manager.py         # 代理管理
├── template_manager.py      # 消息模板
├── scheduler.py             # 定时任务
├── health_monitor.py        # 健康监控
├── log_manager.py           # 日志管理
├── stats_tracker.py         # 统计追踪
├── batch_operations.py      # 批量操作
├── static/
│   └── dashboard.html       # Web 管理界面
├── accounts/                # 数据存储目录
│   ├── config.json          # 账号配置
│   ├── proxies.json         # 代理配置
│   ├── templates.json       # 消息模板
│   ├── schedules.json       # 定时任务
│   ├── logs.json            # 操作日志
│   ├── health.json          # 健康数据
│   └── stats.json           # 统计数据
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量示例
├── Dockerfile               # Docker 配置
├── docker-compose.yml       # Docker Compose
├── BUGFIXES.md              # Bug 修复记录
├── VERIFICATION_REPORT.md   # 系统验证报告
└── README.md                # 本文件
```

---

## Docker 部署

### 使用 Docker Compose（推荐）

```bash
docker-compose up -d
```

访问 http://localhost:8080

### 手动 Docker

```bash
# 构建镜像
docker build -t telegram-mcp .

# 运行容器
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/accounts:/app/accounts \
  --name telegram-mcp \
  telegram-mcp
```

---

## 文档

- [完整工具列表](docs/TOOLS.md)
- [API 文档](docs/API.md)
- [故障排除](docs/TROUBLESHOOTING.md)
- [Bug 修复记录](BUGFIXES.md)
- [系统验证报告](VERIFICATION_REPORT.md)

---

## 常见问题

### Q: 支持 Docker 部署吗？
A: 支持！使用 `docker-compose up -d` 即可一键启动。

### Q: 如何添加多个账号？
A: 在 Dashboard 中点击"添加账号"，支持二维码和手机号两种登录方式。

### Q: Session 安全吗？
A: Session 仅保存在本地 `accounts/config.json`，不会上传到任何服务器。

### Q: 可以在服务器上运行吗？
A: 可以！使用 Docker 部署或直接运行 `nohup python3 dashboard.py &`。

### Q: 支持哪些代理协议？
A: 支持 HTTP 和 SOCKS5 代理。

### Q: MCP 工具和 Dashboard 是什么关系？
A: Dashboard 用于可视化管理，MCP 工具供 AI 调用。两者共享同一个账号存储，Dashboard 添加的账号 AI 可以直接使用。

---

## 贡献

欢迎提交 Issue 和 Pull Request！

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/telegram-mcp-complete.git
cd telegram-mcp-complete

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/
```

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 致谢

- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram 客户端库
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP 框架
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架

---

<div align="center">

**Made with ❤️ for AI-powered Telegram automation**

[⭐ Star](https://github.com/yourusername/telegram-mcp-complete) • [🍴 Fork](https://github.com/yourusername/telegram-mcp-complete/fork) • [🐛 Report Bug](https://github.com/yourusername/telegram-mcp-complete/issues)

</div>
