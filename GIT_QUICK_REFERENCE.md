# 🚀 Git问题快速解决手册

## 🔥 紧急修复命令（复制即用）

### 提交卡住了？
```bash
# 1. 查找并终止卡住的进程
ps aux | grep git | grep commit
kill $(ps aux | grep "git.*commit" | grep -v grep | awk '{print $2}')

# 2. 使用强制提交
./scripts/force_commit.sh "您的提交信息"
```

### 网络连接失败？
```bash
# 清除所有代理
git config --global --unset http.proxy
git config --global --unset https.proxy
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy

# 测试连接
ssh -T git@github.com
```

### CRLF警告？
```bash
# 永久禁用
git config --global core.autocrlf false
git config --global core.safecrlf false

# 修复现有文件
find . -name "*.sh" -exec sed -i 's/\r$//' {} \;
```

### 脚本无法执行？
```bash
# bad interpreter错误
sed -i 's/\r$//' script.sh
chmod +x script.sh
```

### 嵌套仓库错误？
```bash
# 查找嵌套.git
find . -name ".git" -type d | grep -v "^./.git$"

# 删除嵌套.git
rm -rf path/to/nested/.git
```

## ⚡ 一键解决方案

### 创建别名（一次配置，永久使用）
```bash
# 快速提交
git config --global alias.qc '!sh -c "git add -A && git commit -m \"$1\" --no-verify && git push"' -

# 使用：git qc "提交信息"
```

### 万能修复脚本
```bash
cat > fix_all.sh << 'EOF'
#!/bin/bash
pkill -f git
rm -f .git/index.lock
git config --global core.autocrlf false
git config --global core.safecrlf false
git config --global --unset http.proxy
git config --global --unset https.proxy
echo "✅ 修复完成"
EOF
chmod +x fix_all.sh
```

## 📋 诊断清单（10秒检查）

```bash
# 一键诊断
echo "代理:" $(git config --get http.proxy || echo "✅无")
echo "CRLF:" $(git config --get core.autocrlf || echo "✅已禁用")
echo "编辑器:" $(git config --get core.editor || echo "⚠️未设置")
echo "SSH:" $(ssh -T git@github.com 2>&1 | grep -q "success" && echo "✅正常" || echo "❌失败")
echo "嵌套:" $(find . -name ".git" -type d | grep -v "^./.git$" | wc -l) "个"
```

## 🎯 黄金法则

1. **永远使用** `./scripts/force_commit.sh` 提交
2. **永远禁用** CRLF自动转换
3. **永远检查** 代理配置
4. **永远避免** IDE中的Git操作
5. **永远备份** 重要更改

## 🔗 深度文档

- 完整规格: `/docs/specifications/0001-Git部署完整技术规格与卡点分析.md`
- 详细指南: `/scripts/git_commit_guide.md`
- 项目状态: `/PROJECT_STATUS_REPORT.md`

---
记住：90%的Git问题都是配置问题，不是真正的故障！