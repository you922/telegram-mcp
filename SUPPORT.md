# 获取支持

欢迎使用 Telegram MCP Complete！这里有各种获取帮助的方式。

## 📚 文档

首先，我们建议查看项目文档：

- 📖 [README.md](README.md) - 项目概述和快速开始
- 🔧 [配置指南](#配置帮助) - 详细配置说明
- 🐛 [故障排除](#故障排除) - 常见问题解决方案
- 📝 [API 文档](#api-文档) - MCP 工具和 Dashboard API 参考

---

## 💬 社区支持

### GitHub Discussions

对于使用问题、功能讨论和一般疑问，请使用 [GitHub Discussions](https://github.com/yourusername/telegram-mcp-complete/discussions)：

- **使用问题** - 如何使用某个功能
- **功能讨论** - 讨论新功能想法
- **一般疑问** - 项目相关问题

### GitHub Issues

对于 Bug 报告和具体的功能请求，请使用 [GitHub Issues](https://github.com/yourusername/telegram-mcp-complete/issues)：

- 🐛 [报告 Bug](https://github.com/yourusername/telegram-mcp-complete/issues/new?template=bug_report.md)
- ✨ [功能请求](https://github.com/yourusername/telegram-mcp-complete/issues/new?template=feature_request.md)

---

## 🔧 配置帮助

### 常见配置问题

#### Telegram API 凭证

**Q: 如何获取 Telegram API ID 和 Hash？**

1. 访问 https://my.telegram.org/apps
2. 登录您的 Telegram 账号
3. 创建新应用获取 API credentials

**Q: 可以使用内置凭证吗？**

A: 可以！项目内置了测试凭证，可以直接使用。

#### 代理配置

**Q: 如何配置代理？**

在 `accounts/proxies.json` 中配置：

```json
{
  "global": {
    "protocol": "socks5",
    "host": "127.0.0.1",
    "port": 1080
  }
}
```

支持的协议：`http`, `https`, `socks4`, `socks5`

#### Dashboard 配置

**Q: 如何修改 Dashboard 端口？**

在 `.env` 文件中设置：

```bash
DASHBOARD_PORT=8080
DASHBOARD_HOST=0.0.0.0
```

---

## 🐛 故障排除

### 常见问题

#### 登录问题

**问题**: 二维码登录失败

**解决方案**:
1. 确保手机已安装最新版 Telegram
2. 检查网络连接
3. 尝试使用手机号登录

**问题**: 验证码收不到

**解决方案**:
1. 检查手机号格式是否正确
2. 确认选择了正确的国家代码
3. 等待 60 秒后重新发送

#### 连接问题

**问题**: 账号频繁掉线

**解决方案**:
1. 配置稳定的代理
2. 检查代理连接质量
3. 使用健康监控功能检测账号状态

**问题**: 代理连接失败

**解决方案**:
1. 验证代理地址和端口
2. 测试代理可用性
3. 尝试不同代理协议

#### MCP 工具问题

**问题**: Claude Code 无法调用 MCP 工具

**解决方案**:
1. 检查 `claude_desktop_config.json` 配置
2. 确保 main.py 路径正确
3. 重启 Claude Code

**问题**: 工具调用报错

**解决方案**:
1. 查看 `mcp_errors.log` 日志
2. 确认账号已登录
3. 检查 API 权限

---

## 📝 API 文档

### MCP 工具列表

详细工具文档：[完整工具列表](docs/TOOLS.md)

主要类别：
- 💬 聊天管理 (6 个工具)
- 📝 消息操作 (39 个工具)
- 👥 联系人管理 (10 个工具)
- 👥 群组管理 (17 个工具)
- 📊 媒体操作 (19 个工具)
- 👤 个人资料 (18 个工具)
- 🔄 其他工具 (8 个工具)

### Dashboard API

启动 Dashboard 后，访问 http://localhost:8080/docs 查看完整 API 文档（Swagger UI）。

主要端点：
- `GET /api/accounts` - 获取账号列表
- `POST /api/accounts/generate-qr` - 生成二维码
- `POST /api/accounts/send-code` - 发送验证码
- `GET /api/health/report` - 健康报告

---

## 📢 获取最新信息

### 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。

### 发布公告

在 GitHub Releases 页面查看每个版本的详细说明。

### 社交媒体

关注我们的更新：
- GitHub: [https://github.com/yourusername/telegram-mcp-complete](https://github.com/yourusername/telegram-mcp-complete)

---

## 🤝 贡献

我们欢迎贡献！

查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与项目开发。

---

## 📧 联系方式

### 商业咨询

如需商业支持或定制开发，请发送邮件至：[your-email@example.com](mailto:your-email@example.com)

### 安全问题

如发现安全漏洞，请直接发送邮件至：[security@example.com](mailto:security@example.com)

**请不要**公开报告安全问题。

---

## 🌐 资源链接

### 相关项目

- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram 客户端库
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP 框架
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架

### 学习资源

- [MCP 协议规范](https://modelcontextprotocol.io/)
- [Telegram API 文档](https://core.telegram.org/api)
- [Claude Code 文档](https://claude.ai/code/docs)

---

## ⚠️ 获取帮助的最佳实践

1. **搜索现有问题** - 在提出新问题前，先搜索 Issues 和 Discussions
2. **提供详细信息** - 包含环境信息、错误日志和重现步骤
3. **使用模板** - 创建 Issue 时使用相应的模板
4. **保持礼貌** - 社区成员都是志愿者，请保持友好
5. **跟进回复** - 及时回应维护者的问题

---

## 📋 支持 SLA

| 支持类型 | 响应时间 | 适用对象 |
|---------|---------|---------|
| 社区支持 | 最佳努力 | 所有用户 |
| 商业支持 | 48 小时 | 商业客户 |
| 安全问题 | 24 小时 | 所有用户 |

---

感谢您使用 Telegram MCP Complete！🎉
