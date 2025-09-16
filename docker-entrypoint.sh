#!/bin/bash

# Docker启动脚本
echo "启动腾讯文档自动化系统..."

# 启动Xvfb（虚拟显示）
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# 等待Xvfb启动
sleep 2

echo "虚拟显示已启动: $DISPLAY"

# 检查Chrome
if command -v google-chrome &> /dev/null; then
    echo "✅ Chrome已安装: $(google-chrome --version)"
else
    echo "❌ Chrome未找到"
    exit 1
fi

# 检查Playwright
if python3 -c "import playwright" &> /dev/null; then
    echo "✅ Playwright已安装"
else
    echo "❌ Playwright未找到"
    exit 1
fi

# 创建日志目录
mkdir -p /app/logs

# 启动主程序
echo "启动自动化程序..."
exec "$@"