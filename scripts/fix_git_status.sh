#!/bin/bash

# Git状态修复脚本
# 解决提交卡在加载的问题

echo "=== Git状态修复脚本 ==="

# 1. 终止所有Git进程
echo "步骤1: 终止卡住的Git进程..."
pkill -f "git.*commit" 2>/dev/null
pkill -f "git-editor" 2>/dev/null
echo "✅ Git进程已清理"

# 2. 清理Git锁文件
echo "步骤2: 清理Git锁文件..."
rm -f .git/index.lock 2>/dev/null
rm -f .git/COMMIT_EDITMSG 2>/dev/null
rm -f .git/MERGE_HEAD 2>/dev/null
rm -f .git/CHERRY_PICK_HEAD 2>/dev/null
echo "✅ 锁文件已清理"

# 3. 重置Git索引
echo "步骤3: 刷新Git索引..."
git update-index --refresh
echo "✅ 索引已刷新"

# 4. 检查当前状态
echo "步骤4: 检查当前状态..."
echo "---本地状态---"
git status --short | head -5
echo "---"
echo "本地提交: $(git rev-parse --short HEAD)"
echo "远程提交: $(git rev-parse --short origin/main)"

# 5. 验证同步状态
if [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ]; then
    echo "✅ 本地和远程已同步"
else
    echo "⚠️ 本地和远程不同步"
    echo "需要执行: git pull 或 git push"
fi

# 6. 清理未跟踪文件（可选）
echo ""
echo "是否要查看未跟踪文件列表？[y/N]"
read -t 5 -n 1 -r answer || true
echo
if [[ $answer =~ ^[Yy]$ ]]; then
    echo "未跟踪文件："
    git status --untracked-files=all --porcelain | grep '^??' | cut -c4-
fi

echo ""
echo "=== 修复完成 ==="
echo "GitHub仓库: https://github.com/qiming963258/tencent-doc-manager"
echo "最新提交: $(git log --oneline -1)"

# 提示后续操作
echo ""
echo "建议后续操作："
echo "1. 如果要提交当前更改: git add . && git commit -m '描述' && git push"
echo "2. 如果要放弃当前更改: git checkout -- ."
echo "3. 如果要保存当前更改: git stash"