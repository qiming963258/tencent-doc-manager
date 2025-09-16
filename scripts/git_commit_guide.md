# Git提交指南 - 避免卡住问题

## 问题原因
Cursor/VSCode作为Git的默认编辑器，会在提交时打开编辑器窗口等待输入，导致命令行提交卡住。

## 解决方案

### 方法1：使用强制提交脚本（推荐）
```bash
./scripts/force_commit.sh "提交信息"
```
该脚本会：
- 自动禁用CRLF检查
- 绕过编辑器交互
- 完成提交后恢复配置

### 方法2：直接使用git commit -m
```bash
git add .
git commit -m "提交信息" --no-verify
```

### 方法3：设置非交互式编辑器
```bash
# 永久设置
git config --global core.editor "cat"

# 或临时使用
GIT_EDITOR=cat git commit
```

## 如果提交卡住了

1. 查找卡住的Git进程：
```bash
ps aux | grep git | grep commit
```

2. 终止进程：
```bash
kill <进程ID>
```

3. 使用强制提交脚本重新提交：
```bash
./scripts/force_commit.sh "提交信息"
```

## 预防措施

1. **使用命令行提交**：避免在IDE中点击提交按钮
2. **使用-m参数**：直接在命令中指定提交信息
3. **使用脚本**：使用force_commit.sh脚本自动处理

## 已配置的优化

- `.gitattributes`：统一换行符处理
- `.editorconfig`：编辑器配置
- `core.autocrlf=false`：禁用自动CRLF转换
- `core.safecrlf=false`：禁用CRLF警告

## 快速命令参考

```bash
# 查看状态
git status

# 添加所有文件
git add .

# 强制提交（推荐）
./scripts/force_commit.sh "提交信息"

# 推送到远程
git push origin main

# 检查嵌套仓库
./scripts/check_nested_git.sh
```