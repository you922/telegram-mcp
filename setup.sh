#!/bin/bash
# Telegram MCP - 安装脚本

set -e

echo "=========================================="
echo "  Telegram MCP - 安装向导"
echo "=========================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ 检测到 Python $PYTHON_VERSION"

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "📦 正在安装 Python 依赖..."
pip3 install -r requirements.txt

echo ""
echo "🌐 正在安装 Playwright 浏览器..."
playwright install chromium

echo ""
echo "✅ 安装完成!"
echo ""
echo "📝 下一步："
echo "   1. 登录 Telegram: python3 login.py"
echo "   2. 配置 Claude Code（见 README.md）"
echo ""
