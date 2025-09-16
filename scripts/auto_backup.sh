#!/bin/bash

# 自动备份脚本 - 模仿Claude Code网络连接方式
# 创建时间: 2025-09-17
# 作者: Claude Code

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_DIR="/root/projects/tencent-doc-manager"
BACKUP_DIR="/root/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${GREEN}=== 腾讯文档管理系统自动备份脚本 ===${NC}"
echo "时间: $(date)"

# 1. 检查网络连接
echo -e "\n${YELLOW}[1/5] 检查网络连接...${NC}"
check_network() {
    if ping -c 1 github.com &> /dev/null; then
        echo -e "${GREEN}✅ 网络连接正常${NC}"
        return 0
    else
        echo -e "${RED}❌ 网络连接失败${NC}"
        return 1
    fi
}

# 2. 检查并修复Git配置
echo -e "\n${YELLOW}[2/5] 检查Git配置...${NC}"
fix_git_config() {
    # 检查是否有代理配置
    if git config --get http.proxy &> /dev/null; then
        echo -e "${YELLOW}检测到代理配置，正在清除...${NC}"
        git config --global --unset http.proxy
        git config --global --unset https.proxy 2>/dev/null || true
        echo -e "${GREEN}✅ 代理已清除${NC}"
    else
        echo -e "${GREEN}✅ Git配置正常（直连模式）${NC}"
    fi

    # 测试SSH连接
    if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        echo -e "${GREEN}✅ SSH认证成功${NC}"
        return 0
    else
        echo -e "${RED}❌ SSH认证失败${NC}"
        return 1
    fi
}

# 3. 本地备份
echo -e "\n${YELLOW}[3/5] 创建本地备份...${NC}"
local_backup() {
    mkdir -p "$BACKUP_DIR"

    BACKUP_FILE="$BACKUP_DIR/tencent-doc-manager-$TIMESTAMP.tar.gz"

    tar -czf "$BACKUP_FILE" \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='node_modules' \
        --exclude='downloads' \
        --exclude='uploads' \
        -C "$(dirname $PROJECT_DIR)" \
        "$(basename $PROJECT_DIR)"

    if [ -f "$BACKUP_FILE" ]; then
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo -e "${GREEN}✅ 本地备份成功: $BACKUP_FILE ($SIZE)${NC}"
        return 0
    else
        echo -e "${RED}❌ 本地备份失败${NC}"
        return 1
    fi
}

# 4. Git提交和推送
echo -e "\n${YELLOW}[4/5] 提交到Git仓库...${NC}"
git_backup() {
    cd "$PROJECT_DIR"

    # 检查是否有更改
    if git diff --quiet && git diff --staged --quiet; then
        echo -e "${YELLOW}没有新的更改需要提交${NC}"
        return 0
    fi

    # 添加所有更改
    git add -A

    # 生成提交信息
    COMMIT_MSG="自动备份 - $(date '+%Y-%m-%d %H:%M:%S')

自动备份包含:
$(git diff --staged --stat | head -5)

由自动备份脚本生成"

    # 提交
    git commit -m "$COMMIT_MSG"
    echo -e "${GREEN}✅ 已创建新提交${NC}"

    # 推送到远程仓库
    echo "正在推送到GitHub..."
    if git push origin main; then
        echo -e "${GREEN}✅ 推送成功${NC}"
        return 0
    else
        echo -e "${RED}❌ 推送失败，尝试修复...${NC}"

        # 尝试拉取并合并
        git pull origin main --rebase
        git push origin main
    fi
}

# 5. 创建备份分支（可选）
echo -e "\n${YELLOW}[5/5] 创建备份分支...${NC}"
create_backup_branch() {
    BRANCH_NAME="backup/auto-$TIMESTAMP"

    git checkout -b "$BRANCH_NAME"

    if git push origin "$BRANCH_NAME"; then
        echo -e "${GREEN}✅ 备份分支创建成功: $BRANCH_NAME${NC}"
    else
        echo -e "${YELLOW}⚠️ 备份分支创建失败（非关键错误）${NC}"
    fi

    # 切回主分支
    git checkout main
}

# 主函数
main() {
    echo -e "\n${GREEN}开始执行备份流程...${NC}\n"

    # 执行检查和修复
    if ! check_network; then
        echo -e "${RED}网络连接失败，无法继续${NC}"
        exit 1
    fi

    if ! fix_git_config; then
        echo -e "${RED}Git配置修复失败${NC}"
        exit 1
    fi

    # 执行备份
    local_backup

    # Git备份
    if git_backup; then
        # 可选：创建备份分支
        read -t 5 -p "是否创建备份分支？(5秒后自动跳过) [y/N]: " -n 1 -r || true
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            create_backup_branch
        fi
    fi

    echo -e "\n${GREEN}=== 备份完成 ===${NC}"
    echo "本地备份: $BACKUP_FILE"
    echo "GitHub仓库: https://github.com/qiming963258/tencent-doc-manager"

    # 清理旧备份（保留最近7个）
    echo -e "\n清理旧备份文件..."
    ls -t "$BACKUP_DIR"/tencent-doc-manager-*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm -v
}

# 错误处理
trap 'echo -e "\n${RED}备份过程中发生错误${NC}"; exit 1' ERR

# 执行主函数
main

# 定时任务配置提示
echo -e "\n${YELLOW}提示: 要设置定时自动备份，请添加到crontab:${NC}"
echo "# 每天凌晨2点自动备份"
echo "0 2 * * * $0 >> /var/log/auto_backup.log 2>&1"