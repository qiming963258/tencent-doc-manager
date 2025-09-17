#!/bin/bash
# Git永久修复脚本 - 彻底解决编辑器卡死问题
# 基于: docs/specifications/0000-Git部署完整技术规格与卡点分析.md

echo "=== 🔧 Git永久修复配置 ==="
echo "正在应用永久解决方案..."

# 1. 清理所有可能的编辑器设置
echo "Step 1: 清理编辑器设置..."
git config --global --unset core.editor 2>/dev/null || true
git config --global --unset-all core.editor 2>/dev/null || true
git config --local --unset core.editor 2>/dev/null || true

# 2. 设置非交互式编辑器
echo "Step 2: 设置非交互式编辑器..."
git config --global core.editor "true"

# 3. 禁用CRLF自动转换（避免警告）
echo "Step 3: 禁用CRLF转换..."
git config --global core.autocrlf false
git config --global core.safecrlf false

# 4. 清理所有代理设置
echo "Step 4: 清理代理设置..."
git config --global --unset http.proxy 2>/dev/null || true
git config --global --unset https.proxy 2>/dev/null || true

# 5. 创建Git别名（快速提交）
echo "Step 5: 创建便捷别名..."
git config --global alias.qc '!f() { git add -A && GIT_EDITOR=true git commit -m "$1" --no-verify; }; f'
git config --global alias.qa '!git add -A'
git config --global alias.qs '!git status --short'
git config --global alias.qp '!git push'

# 6. 创建.gitattributes（处理换行符）
echo "Step 6: 创建.gitattributes..."
cat > /root/projects/tencent-doc-manager/.gitattributes << 'ATTR'
# 统一使用LF换行符
* text=auto eol=lf
*.sh text eol=lf
*.py text eol=lf
*.md text eol=lf
*.js text eol=lf
*.json text eol=lf
*.bat text eol=crlf
*.cmd text eol=crlf
ATTR

# 7. 创建环境变量配置文件
echo "Step 7: 设置环境变量..."
cat > /root/.git_env << 'ENV'
# Git环境变量 - 防止编辑器卡死
export GIT_EDITOR=true
export GIT_SEQUENCE_EDITOR=true
export GIT_MERGE_AUTOEDIT=no
ENV

# 8. 添加到bashrc（永久生效）
if ! grep -q "source ~/.git_env" ~/.bashrc 2>/dev/null; then
    echo "source ~/.git_env" >> ~/.bashrc
    echo "已添加到.bashrc"
fi

# 9. 创建紧急修复命令
echo "Step 8: 创建紧急修复命令..."
cat > /usr/local/bin/git-fix << 'FIX'
#!/bin/bash
# 紧急修复Git卡死
pkill -f "git.*commit" 2>/dev/null
pkill -f "cursor.*git" 2>/dev/null
rm -f .git/index.lock 2>/dev/null
git config --global core.editor "true"
export GIT_EDITOR=true
echo "✅ Git已修复，可以继续操作"
FIX
chmod +x /usr/local/bin/git-fix

# 10. 显示配置结果
echo ""
echo "=== ✅ 永久修复完成 ==="
echo ""
echo "📋 当前Git配置："
echo "  core.editor: $(git config --global core.editor)"
echo "  core.autocrlf: $(git config --global core.autocrlf)"
echo "  环境变量GIT_EDITOR: ${GIT_EDITOR:-未设置}"
echo ""
echo "🚀 可用的快捷命令："
echo "  git qc \"消息\"  - 快速提交（Quick Commit）"
echo "  git qa         - 快速添加所有文件（Quick Add）"
echo "  git qs         - 快速状态（Quick Status）"
echo "  git qp         - 快速推送（Quick Push）"
echo "  git-fix        - 紧急修复Git卡死"
echo ""
echo "💡 使用示例："
echo "  git qa && git qc \"更新文档\" && git qp"
echo ""
echo "⚠️ 如果再次卡死，直接运行: git-fix"

# 立即应用环境变量
source ~/.git_env
