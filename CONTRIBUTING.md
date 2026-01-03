# 贡献指南

感谢您考虑为 Telegram MCP Complete 做出贡献！我们欢迎任何形式的贡献。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [问题反馈](#问题反馈)

---

## 行为准则

### 我们的承诺

为了营造开放和友好的环境，我们承诺让每个人都能参与到我们的项目中来。

### 我们的标准

积极行为包括：
- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 专注于对社区最有利的事情
- 对其他社区成员表示同理心

不可接受的行为包括：
- 使用性别化语言或图像，以及不受欢迎的性关注或勾引
- 挑衅、侮辱/贬损的评论，以及人身或政治攻击
- 公开或私下骚扰
- 未经明确许可发布他人的私人信息
- 其他在专业场合可能被认为不合适的行为

---

## 如何贡献

### 报告 Bug

在创建 Bug 报告前，请检查现有问题是否已涵盖相同问题。

Bug 报告应包含：
- **清晰的标题** - 简洁描述问题
- **环境信息** - 操作系统、Python 版本、依赖版本
- **重现步骤** - 详细的问题重现步骤
- **预期行为** - 您期望发生什么
- **实际行为** - 实际发生了什么
- **截图/日志** - 如果适用，提供相关截图或日志

### 提出新功能

在提交功能请求前，请检查是否已有类似请求。

功能请求应包含：
- **用例描述** - 这个功能解决什么问题
- ** proposed solution** - 您建议的实现方案
- **替代方案** - 您考虑过的其他方案
- **附加信息** - 任何其他相关信息

### 提交代码

1. **Fork 仓库**
   ```bash
   git clone https://github.com/yourusername/telegram-mcp-complete.git
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **进行更改**
   - 遵循代码规范
   - 添加必要的测试
   - 更新相关文档

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add some amazing feature"
   ```

5. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**
   - 填写 PR 模板
   - 关联相关 Issue
   - 等待代码审查

---

## 开发流程

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/telegram-mcp-complete.git
cd telegram-mcp-complete

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 安装 pre-commit hooks
pre-commit install
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_account_manager.py

# 查看覆盖率
pytest --cov=. --cov-report=html
```

### 代码格式化

```bash
# 格式化代码
black .

# 检查代码风格
flake8

# 类型检查
mypy .
```

---

## 代码规范

### Python 代码风格

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 规范
- 使用 [Black](https://github.com/psf/black) 进行代码格式化
- 使用 [isort](https://github.com/PyCQA/isort) 排序导入
- 添加类型注解（使用 [typing](https://docs.python.org/3/library/typing.html)）
- 编写文档字符串（使用 [Google 风格](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)）

示例：

```python
from typing import Optional, List

def send_message(
    chat_id: int,
    text: str,
    parse_mode: Optional[str] = None
) -> dict:
    """发送消息到指定聊天。

    Args:
        chat_id: 聊天 ID
        text: 消息文本
        parse_mode: 解析模式 (HTML/Markdown)

    Returns:
        包含消息信息的字典

    Raises:
        ValueError: 如果文本为空
        TelegramError: 如果发送失败
    """
    if not text:
        raise ValueError("消息文本不能为空")

    # 实现代码...
```

### JavaScript/Vue 代码风格

- 使用 [ESLint](https://eslint.org/) 检查代码
- 使用 [Prettier](https://prettier.io/) 格式化代码
- 遵循 [Vue 风格指南](https://vuejs.org/style-guide/)

### 文档规范

- 使用清晰简洁的语言
- 提供代码示例
- 包含必要的截图
- 更新 README 和 API 文档

---

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

### 提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行的变动）
- `refactor`: 重构（既不是新增功能，也不是修改 bug 的代码变动）
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动
- `ci`: CI 配置文件和脚本的变动
- `revert`: 回退

### 示例

```bash
feat(account): add phone number login support

- Implement send_phone_code method
- Add verify_phone_code method
- Support 177 countries

Closes #123
```

---

## 问题反馈

### 在哪里提问

| 类型 | 位置 |
|------|------|
| Bug 报告 | [GitHub Issues](https://github.com/yourusername/telegram-mcp-complete/issues) |
| 功能请求 | [GitHub Issues](https://github.com/yourusername/telegram-mcp-complete/issues) |
| 使用问题 | [GitHub Discussions](https://github.com/yourusername/telegram-mcp-complete/discussions) |
| PR 相关 | 在 PR 中评论 |

### Issue 模板

创建 Issue 时，请使用相应的模板：

1. **Bug 报告** - 描述问题、环境、重现步骤
2. **功能请求** - 描述用例、期望行为、可能的实现
3. **文档问题** - 指出哪个文档需要改进

---

## 审查流程

### Pull Request 审查

1. 自动检查通过（CI/CD）
2. 至少一位维护者审查
3. 所有请求的更改已完成
4. PR 通过所有测试

### 合并策略

- 使用 "Squash and merge" 保持历史清洁
- 或使用 "Rebase and merge" 保持线性历史

---

## 发布流程

1. 更新版本号
2. 更新 CHANGELOG.md
3. 创建 Git tag
4. 推送到 GitHub
5. GitHub Actions 自动创建 Release

---

## 获取帮助

如果您有任何问题：

- 查看 [文档](README.md)
- 在 [Discussions](https://github.com/yourusername/telegram-mcp-complete/discussions) 中提问
- 联系维护者

---

再次感谢您的贡献！🎉
