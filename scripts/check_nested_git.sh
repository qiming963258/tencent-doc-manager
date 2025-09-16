#!/bin/bash

# 检查嵌套Git仓库脚本
# 防止子模块错误

echo "=== 检查嵌套Git仓库 ==="

# 查找所有.git目录（排除主仓库的.git）
NESTED_REPOS=$(find . -name ".git" -type d 2>/dev/null | grep -v "^./.git$")

if [ -z "$NESTED_REPOS" ]; then
    echo "✅ 没有发现嵌套的Git仓库"
else
    echo "⚠️ 发现以下嵌套的Git仓库："
    echo "$NESTED_REPOS"
    echo ""
    echo "建议处理方式："
    echo "1. 如果要作为子模块管理："
    echo "   git submodule add <repository-url> <path>"
    echo ""
    echo "2. 如果要合并到主仓库："
    echo "   rm -rf <path>/.git"
    echo "   git add <path>"
    echo "   git commit -m '整合子项目'"
fi

# 检查.gitmodules文件
if [ -f ".gitmodules" ]; then
    echo ""
    echo "📋 已配置的子模块："
    cat .gitmodules
fi

echo ""
echo "=== 检查完成 ==="