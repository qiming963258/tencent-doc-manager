# 腾讯文档下载系统 - 部署指南

## 架构说明

本系统采用**浏览器桥接架构**，解决了网页无法直接控制本地浏览器的安全限制问题。

```
[Web控制面板] <--WebSocket--> [本地桥接服务] <--CDP--> [用户Chrome浏览器]
     ↑                              ↑                         ↑
  服务器部署                    用户本地运行              用户真实浏览器
```

## 🚀 部署方案

### 方案1：本地桥接服务（推荐）

#### 服务器端部署
1. 将`web_control_panel.html`部署到Web服务器
2. 可以使用nginx或简单的Python HTTP服务器

```bash
# 方式1：使用Python快速部署
python3 -m http.server 8080

# 方式2：使用nginx配置
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/tencent-doc-manager;
    
    location / {
        try_files $uri /web_control_panel.html;
    }
}
```

#### 用户端安装
1. 安装依赖
```bash
pip install playwright websockets
playwright install chromium
```

2. 运行本地桥接服务
```bash
python3 local_browser_bridge.py
```

3. 访问Web控制面板
```
http://your-server.com/web_control_panel.html
```

### 方案2：一键安装包

创建用户友好的安装程序：

#### Windows安装包
```batch
@echo off
echo 安装腾讯文档下载助手...
pip install playwright websockets
playwright install chromium
echo 安装完成！
echo.
echo 启动本地服务...
python local_browser_bridge.py
pause
```

#### macOS/Linux安装脚本
```bash
#!/bin/bash
echo "安装腾讯文档下载助手..."
pip3 install playwright websockets
playwright install chromium
echo "安装完成！"
echo ""
echo "启动本地服务..."
python3 local_browser_bridge.py
```

## 📦 Docker部署（可选）

创建Docker镜像供用户本地运行：

```dockerfile
FROM python:3.9-slim

# 安装依赖
RUN pip install playwright websockets
RUN playwright install chromium
RUN playwright install-deps

# 复制代码
COPY local_browser_bridge.py /app/

WORKDIR /app

# 暴露WebSocket端口
EXPOSE 8765

# 启动服务
CMD ["python", "local_browser_bridge.py"]
```

用户运行：
```bash
docker run -p 8765:8765 --rm tencent-doc-bridge
```

## 🔐 安全考虑

### 1. WebSocket安全
- 本地桥接服务只监听`localhost:8765`
- 不接受外部连接，防止远程控制

### 2. CORS策略
如果Web控制面板部署在远程服务器，需要配置CORS：

```javascript
// 在local_browser_bridge.py中添加CORS头
async def handle_websocket(self, websocket, path):
    # 检查Origin
    origin = websocket.request_headers.get('Origin', '')
    allowed_origins = ['https://your-domain.com', 'http://localhost']
    
    if origin not in allowed_origins:
        await websocket.close(1008, 'Origin not allowed')
        return
```

### 3. 认证机制（可选）
添加简单的Token认证：

```python
# 生成Token
import secrets
token = secrets.token_urlsafe(32)

# 验证Token
if command.get('token') != self.auth_token:
    return {'status': 'error', 'message': '认证失败'}
```

## 🌐 高级部署：浏览器扩展方案

如果需要更透明的用户体验，可以开发浏览器扩展：

### Chrome扩展结构
```
tencent-doc-extension/
├── manifest.json
├── background.js
├── content.js
├── popup.html
└── icons/
```

### 关键代码
```javascript
// manifest.json
{
  "manifest_version": 3,
  "name": "腾讯文档下载助手",
  "version": "1.0",
  "permissions": [
    "downloads",
    "cookies",
    "tabs"
  ],
  "host_permissions": [
    "https://docs.qq.com/*"
  ],
  "action": {
    "default_popup": "popup.html"
  }
}
```

## 📱 移动端支持

对于移动设备，可以使用：

1. **远程桌面方案**
   - 用户通过远程桌面连接到配置好的云服务器
   - 服务器上运行完整的浏览器环境

2. **云函数方案**
   - 使用腾讯云/阿里云的无头浏览器服务
   - 通过API调用实现下载

## 🚨 故障排查

### 常见问题

1. **WebSocket连接失败**
   - 检查本地服务是否运行：`netstat -an | grep 8765`
   - 检查防火墙设置
   - 确认浏览器允许localhost连接

2. **浏览器启动失败**
   - 安装Chrome：`sudo apt install google-chrome-stable`
   - 检查Playwright安装：`playwright install chromium`

3. **下载失败**
   - 确认已登录腾讯文档
   - 检查Cookie是否有效
   - 查看浏览器控制台错误

### 日志位置
```
~/Downloads/TencentDocs/logs/
├── bridge.log      # 桥接服务日志
├── download.log    # 下载记录
└── error.log       # 错误日志
```

## 📈 性能优化

1. **连接池管理**
   - 复用浏览器实例
   - 定期清理缓存

2. **并发控制**
   - 限制同时下载数量
   - 实现下载队列

3. **断点续传**
   - 保存下载进度
   - 支持重试机制

## 🔄 更新维护

### 自动更新机制
```python
import requests

def check_update():
    """检查版本更新"""
    latest = requests.get('https://api.github.com/repos/your/repo/releases/latest')
    if latest.json()['tag_name'] > current_version:
        # 提示用户更新
        pass
```

## 📞 技术支持

- GitHub Issues: https://github.com/your/repo/issues
- 文档: https://docs.your-domain.com
- Email: support@your-domain.com

## 许可证

MIT License - 自由使用和修改