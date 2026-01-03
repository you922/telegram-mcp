# 手机号登录功能测试指南

## 功能概述

支持 **177 个国家/地区** 的手机号 + 验证码登录，包括两步验证（2FA）支持。

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/accounts/send-code` | POST | 发送验证码到手机号 |
| `/api/accounts/verify-code` | POST | 验证手机验证码 |
| `/api/accounts/{account_id}/phone-2fa` | POST | 提交两步验证密码 |
| `/api/accounts/{account_id}/phone-status` | GET | 获取登录状态 |
| `/api/accounts/{account_id}/phone-login` | DELETE | 取消登录 |

## 测试步骤

### 1. 启动 Dashboard

```bash
python3 dashboard.py
```

访问 http://localhost:8080/static/dashboard.html

### 2. 使用 Web UI 测试

**步骤**：

1. 点击"添加账号"按钮
2. 切换到"手机号登录"标签
3. 选择国家/地区（如：中国 🇨🇳 +86）
4. 输入手机号（如：13800138000）
5. 点击"发送验证码"
6. 在 Telegram 中收到的验证码
7. 输入验证码
8. 如有两步验证，输入 2FA 密码
9. 等待登录完成

### 3. 使用 API 测试

**Step 1: 发送验证码**

```bash
curl -X POST http://localhost:8080/api/accounts/send-code \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "test_account_001",
    "phone": "+8613800138000"
  }'
```

响应：
```json
{
  "success": true,
  "account_id": "test_account_001",
  "phone": "+8613800138000",
  "has_2fa": false
}
```

**Step 2: 验证验证码**

```bash
curl -X POST http://localhost:8080/api/accounts/verify-code \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "test_account_001",
    "code": "12345"
  }'
```

**Step 3: 提交 2FA 密码（如果需要）**

```bash
curl -X POST http://localhost:8080/api/accounts/test_account_001/phone-2fa \
  -H "Content-Type: application/json" \
  -d '{
    "password": "your_2fa_password"
  }'
```

**Step 4: 检查状态**

```bash
curl http://localhost:8080/api/accounts/test_account_001/phone-status
```

## 支持的国家/地区（部分）

| 国家 | 代码 | 标志 | 国家 | 代码 | 标志 |
|------|------|------|------|------|------|
| 中国 | 86 | 🇨🇳 | 美国 | 1 | 🇺🇸 |
| 香港 | 852 | 🇭🇰 | 英国 | 44 | 🇬🇧 |
| 澳门 | 853 | 🇲🇴 | 日本 | 81 | 🇯🇵 |
| 台湾 | 886 | 🇹🇼 | 韩国 | 82 | 🇰🇷 |
| 新加坡 | 65 | 🇸🇬 | 澳大利亚 | 61 | 🇦🇺 |
| ... | ... | ... | ... | ... | ... |

完整列表：177 个国家/地区

## 前端 UI 元素

### 国家选择器
- 支持搜索过滤
- 快速选择热门国家
- 显示国旗和国家名称

### 手机号输入
- 自动添加国家代码前缀
- 国际格式验证

### 验证码输入
- 6 位数字验证码
- 自动聚焦

### 2FA 密码输入
- 密码隐藏显示
- 可切换显示/隐藏

## 错误处理

| 错误 | 描述 | 解决方案 |
|------|------|----------|
| 连接超时 | 网络连接超时 | 检查网络或设置代理 |
| 请求过于频繁 | Flood 等待 | 等待几分钟后重试 |
| 手机号格式无效 | 手机号格式错误 | 检查国家代码和手机号 |
| 验证码错误 | 验证码不正确 | 重新输入验证码 |
| 验证码已过期 | 验证码超时 | 重新发送验证码 |
| 需要两步验证 | 账号设置了 2FA | 输入两步验证密码 |
| 密码错误 | 2FA 密码错误 | 重新输入密码 |

## 代码流程

```python
# 1. 发送验证码
account_manager.send_phone_code(
    account_id="test_001",
    phone="+8613800138000",
    proxy=None
)
# → 发送验证码到手机
# → 保存会话到 phone_sessions

# 2. 验证验证码
account_manager.verify_phone_code(
    account_id="test_001",
    code="12345"
)
# → 如果成功 → 保存账号
# → 如果需要 2FA → 返回 needs_2fa=True

# 3. 提交 2FA（如果需要）
account_manager.submit_2fa_for_phone(
    account_id="test_001",
    password="my_2fa_password"
)
# → 完成登录
# → 保存账号到 config.json
```

## 注意事项

1. **手机号格式**：必须以 `+` 开头，包含国家代码
2. **验证码有效期**：通常几分钟内有效
3. **Flood 等待**：频繁请求会被 Telegram 限制
4. **2FA 密码**：如果账号设置了两步验证，必须输入
5. **代理支持**：可以为手机号登录配置代理

## 测试检查清单

- [ ] 发送验证码 API 正常
- [ ] 接收验证码（Telegram 短信/应用）
- [ ] 验证验证码 API 正常
- [ ] 2FA 密码提交 API 正常
- [ ] 账号保存到 config.json
- [ ] 账号在 Dashboard 中显示
- [ ] MCP 可以使用该账号
- [ ] 取消登录功能正常
- [ ] 错误处理正确显示

## 已知问题

无

## 更新日志

- 2026-01-02: 初始实现，支持 177 个国家/地区
