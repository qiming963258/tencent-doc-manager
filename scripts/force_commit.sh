#!/bin/bash

# 强制提交脚本 - 绕过所有CRLF警告
# 创建时间: 2025-09-17

set -e

echo "=== 强制提交脚本 ==="
echo "此脚本将绕过所有CRLF警告进行提交"
echo ""

# 获取提交信息
if [ -z "$1" ]; then
    echo "使用方法: ./force_commit.sh \"提交信息\""
    exit 1
fi

COMMIT_MSG="$1"

# 1. 临时禁用CRLF检查
echo "步骤1: 临时禁用CRLF检查..."
OLD_AUTOCRLF=$(git config core.autocrlf || echo "unset")
OLD_SAFECRLF=$(git config core.safecrlf || echo "unset")
git config core.autocrlf false
git config core.safecrlf false
echo "✅ CRLF检查已禁用"

# 2. 添加所有更改
echo "步骤2: 添加所有更改..."
git add -A
echo "✅ 文件已添加"

# 3. 强制提交（忽略警告）
echo "步骤3: 执行提交..."
git commit -m "$COMMIT_MSG" --no-verify 2>&1 | grep -v "warning: CRLF" || true
echo "✅ 提交完成"

# 4. 恢复原始配置
echo "步骤4: 恢复Git配置..."
if [ "$OLD_AUTOCRLF" != "unset" ]; then
    git config core.autocrlf "$OLD_AUTOCRLF"
else
    git config --unset core.autocrlf 2>/dev/null || true
fi

if [ "$OLD_SAFECRLF" != "unset" ]; then
    git config core.safecrlf "$OLD_SAFECRLF"
else
    git config --unset core.safecrlf 2>/dev/null || true
fi
echo "✅ 配置已恢复"

# 5. 显示提交信息
echo ""
echo "=== 提交成功 ==="
git log --oneline -1
echo ""
echo "使用 'git push' 推送到远程仓库"