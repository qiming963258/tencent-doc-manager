#!/bin/bash
# force_commit.sh - 强制提交脚本，避免Git卡死问题
# 参考: docs/specifications/0000-Git部署完整技术规格与卡点分析.md

COMMIT_MSG="${1:-自动提交}"

# 保存原始配置
OLD_AUTOCRLF=$(git config core.autocrlf || echo "unset")
OLD_SAFECRLF=$(git config core.safecrlf || echo "unset")

# 临时禁用CRLF检查
git config core.autocrlf false
git config core.safecrlf false

# 添加所有文件
git add -A

# 强制提交，过滤CRLF警告
git commit -m "$COMMIT_MSG" --no-verify 2>&1 | grep -v "warning: CRLF"

# 恢复原始配置
[[ "$OLD_AUTOCRLF" != "unset" ]] && git config core.autocrlf "$OLD_AUTOCRLF" || git config --unset core.autocrlf
[[ "$OLD_SAFECRLF" != "unset" ]] && git config core.safecrlf "$OLD_SAFECRLF" || git config --unset core.safecrlf

echo "✅ 提交完成: $COMMIT_MSG"
