#!/bin/bash
# =====================================================
# Git永久修复脚本 - 彻底解决提交消息为空的问题
# 创建时间：2025-09-21
# =====================================================

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     🔧 Git永久修复脚本 - 彻底解决提交消息问题              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 1. 强制设置环境变量
echo "✅ 步骤1: 设置环境变量..."
export GIT_EDITOR=true
export EDITOR=true
unset VISUAL

# 2. 设置Git全局配置
echo "✅ 步骤2: 配置Git全局设置..."
git config --global core.editor true

# 3. 更新bashrc（如果还没有）
echo "✅ 步骤3: 更新.bashrc配置..."
if ! grep -q "GIT_EDITOR=true" ~/.bashrc; then
    cat >> ~/.bashrc << 'EOF'

# === Git永久修复（自动生成） ===
export GIT_EDITOR=true
export EDITOR=true
unset VISUAL 2>/dev/null
unset VSCODE_GIT_ASKPASS_NODE 2>/dev/null
unset VSCODE_GIT_ASKPASS_MAIN 2>/dev/null
unset VSCODE_GIT_IPC_HANDLE 2>/dev/null
EOF
    echo "   已添加到.bashrc"
else
    echo "   .bashrc已包含配置"
fi

# 4. 创建Git快捷别名
echo "✅ 步骤4: 创建Git快捷别名..."

# gc - Git Commit (快速提交)
git config --global alias.gc '!f() {
    if [ -z "$1" ]; then
        echo "❌ 错误: 请提供提交消息";
        echo "用法: git gc \"你的提交消息\"";
        return 1;
    fi;
    GIT_EDITOR=true git add -A && GIT_EDITOR=true git commit -m "$1" --no-edit;
}; f'

# gcp - Git Commit and Push
git config --global alias.gcp '!f() {
    if [ -z "$1" ]; then
        echo "❌ 错误: 请提供提交消息";
        echo "用法: git gcp \"你的提交消息\"";
        return 1;
    fi;
    GIT_EDITOR=true git add -A && GIT_EDITOR=true git commit -m "$1" --no-edit && git push;
}; f'

# safe-commit - 安全提交（带验证）
git config --global alias.safe-commit '!f() {
    if [ -z "$1" ]; then
        echo "❌ 错误: 请提供提交消息";
        return 1;
    fi;
    echo "📋 准备提交: $1";
    GIT_EDITOR=true git add -A;
    GIT_EDITOR=true git commit -m "$1" --no-edit;
    if [ $? -eq 0 ]; then
        echo "✅ 提交成功!";
    else
        echo "❌ 提交失败";
    fi;
}; f'

# 5. 创建提交辅助脚本
echo "✅ 步骤5: 创建提交辅助脚本..."
cat > /usr/local/bin/gitc << 'SCRIPT_EOF'
#!/bin/bash
# Git提交辅助脚本

if [ -z "$1" ]; then
    echo "❌ 错误: 请提供提交消息"
    echo ""
    echo "用法: gitc \"你的提交消息\""
    echo ""
    echo "示例:"
    echo "  gitc \"修复配置问题\""
    echo "  gitc \"添加新功能：用户登录\""
    exit 1
fi

# 强制设置编辑器
export GIT_EDITOR=true
export EDITOR=true

# 显示状态
echo "📊 Git状态:"
git status --short

# 添加所有更改
git add -A

# 提交
echo ""
echo "📝 提交消息: $1"
git commit -m "$1" --no-edit

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 提交成功!"
    echo ""
    echo "提示: 使用 'git push' 推送到远程仓库"
else
    echo ""
    echo "❌ 提交失败，请检查错误信息"
fi
SCRIPT_EOF

chmod +x /usr/local/bin/gitc

# 6. 创建紧急修复命令
echo "✅ 步骤6: 创建紧急修复命令..."
cat > /usr/local/bin/fix-git << 'FIX_EOF'
#!/bin/bash
# Git紧急修复命令

echo "🚨 执行Git紧急修复..."

# 杀死所有Git进程
pkill -f "git.*commit" 2>/dev/null

# 强制设置环境
export GIT_EDITOR=true
export EDITOR=true
unset VISUAL
unset VSCODE_GIT_ASKPASS_NODE
unset VSCODE_GIT_ASKPASS_MAIN
unset VSCODE_GIT_IPC_HANDLE

# 设置Git配置
git config --global core.editor true

echo "✅ Git修复完成!"
echo ""
echo "现在你可以使用以下命令提交:"
echo "  gitc \"你的提交消息\""
echo "  git gc \"你的提交消息\""
echo "  git safe-commit \"你的提交消息\""
FIX_EOF

chmod +x /usr/local/bin/fix-git

# 7. 显示使用说明
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                  ✅ 修复完成！                            ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║ 🎯 推荐使用方法:                                          ║"
echo "║                                                           ║"
echo "║ 1. 使用新命令 gitc:                                      ║"
echo "║    gitc \"你的提交消息\"                                   ║"
echo "║                                                           ║"
echo "║ 2. 使用Git别名:                                          ║"
echo "║    git gc \"你的提交消息\"      # 提交                    ║"
echo "║    git gcp \"你的提交消息\"     # 提交并推送              ║"
echo "║    git safe-commit \"你的提交消息\"                       ║"
echo "║                                                           ║"
echo "║ 3. 如果还有问题，运行:                                   ║"
echo "║    fix-git                     # 紧急修复                ║"
echo "║                                                           ║"
echo "║ 📝 当前有文件待提交，建议使用:                           ║"
echo "║    gitc \"完成全流程唯一性传递机制\"                      ║"
echo "╚══════════════════════════════════════════════════════════╝"