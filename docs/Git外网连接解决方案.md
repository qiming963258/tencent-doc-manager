# Git外网连接解决方案

**创建日期**: 2025-09-17
**状态**: ✅ 已解决

## 问题诊断

### 症状
- git push/pull失败
- 提示连接超时或无法访问

### 根本原因
Git配置了无效的本地代理：
```bash
http.proxy=http://127.0.0.1:7890
https.proxy=http://127.0.0.1:7890
```

## 解决方案

### 方法1：清除代理配置（推荐）
```bash
# 清除HTTP代理
git config --global --unset http.proxy
git config --global --unset https.proxy

# 验证清除成功
git config --list | grep proxy
```

### 方法2：使用SSH连接
```bash
# 测试SSH连接
ssh -T git@github.com

# 成功提示：
# Hi username! You've successfully authenticated...
```

### 方法3：模仿Claude Code连接方式

Claude Code使用以下方式访问外网：

1. **WebFetch工具**：直接HTTP/HTTPS访问
   ```python
   # Claude Code内部使用
   fetch_result = WebFetch(url="https://api.github.com", prompt="获取数据")
   ```

2. **WebSearch工具**：搜索引擎访问
   ```python
   # Claude Code内部使用
   search_result = WebSearch(query="github connection")
   ```

3. **直连模式**：无需代理，直接访问外网

## 代码备份策略

### 1. 本地备份
```bash
# 创建备份目录
mkdir -p /root/backups/tencent-doc-manager-$(date +%Y%m%d)

# 打包项目
tar -czf /root/backups/tencent-doc-manager-$(date +%Y%m%d).tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  /root/projects/tencent-doc-manager/
```

### 2. 推送到GitHub
```bash
# 添加所有更改
git add .

# 提交
git commit -m "备份配置管理设计方案"

# 推送
git push origin main
```

### 3. 创建分支备份
```bash
# 创建备份分支
git checkout -b backup/config-management-$(date +%Y%m%d)

# 推送分支
git push origin backup/config-management-$(date +%Y%m%d)

# 切回主分支
git checkout main
```

## 网络状态检查

### 检查网络连通性
```bash
# Ping测试
ping -c 3 github.com

# HTTP测试
curl -I https://github.com

# DNS测试
nslookup github.com
```

### 检查Git配置
```bash
# 查看所有Git配置
git config --list

# 查看远程仓库
git remote -v

# 测试fetch
git fetch --dry-run
```

## 常见问题

### Q1: 为什么Claude Code能访问外网？
Claude Code内置了WebFetch和WebSearch工具，这些工具直接通过服务器的网络连接访问外网，不依赖Git配置。

### Q2: 如果需要使用代理怎么办？
```bash
# 设置有效的代理
git config --global http.proxy http://proxy.example.com:8080
git config --global https.proxy http://proxy.example.com:8080

# 仅对GitHub使用代理
git config --global http.https://github.com.proxy http://proxy.example.com:8080
```

### Q3: SSH key配置
```bash
# 生成SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# 查看公钥
cat ~/.ssh/id_ed25519.pub

# 添加到GitHub：Settings > SSH and GPG keys > New SSH key
```

## 监控脚本

创建监控脚本确保连接正常：
```bash
#!/bin/bash
# /root/scripts/check_git_connection.sh

echo "=== Git连接状态检查 ==="

# 检查网络
if ping -c 1 github.com &> /dev/null; then
  echo "✅ 网络连接：正常"
else
  echo "❌ 网络连接：失败"
fi

# 检查SSH
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
  echo "✅ SSH认证：成功"
else
  echo "❌ SSH认证：失败"
fi

# 检查代理
if git config --get http.proxy &> /dev/null; then
  echo "⚠️ HTTP代理：$(git config --get http.proxy)"
else
  echo "✅ HTTP代理：未配置（直连）"
fi

# 测试fetch
if git fetch --dry-run 2>&1 | grep -q "fatal"; then
  echo "❌ Git fetch：失败"
else
  echo "✅ Git fetch：正常"
fi
```

## 总结

1. **问题已解决**：清除无效代理配置后，Git连接恢复正常
2. **最佳实践**：使用SSH连接，不配置不必要的代理
3. **备份策略**：本地备份 + GitHub推送 + 分支管理
4. **监控建议**：定期运行连接检查脚本

---

**维护说明**: 本文档记录了Git外网连接问题的完整解决方案，供后续参考。