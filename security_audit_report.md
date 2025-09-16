# 腾讯文档下载系统WebSocket本地桥接架构安全评估报告

## 执行摘要

评估日期：2025-08-27
评估标准：OWASP Top 10 2024, CWE-1385, NIST Cybersecurity Framework 2.0
严重性等级：**高风险** ⚠️

### 关键发现
系统存在多个严重安全漏洞，最关键的是**完全缺失Origin验证**，使得任意恶意网站都可以连接并控制用户的本地浏览器。

---

## 1. 架构安全风险评估

### 1.1 CSWSH (Cross-Site WebSocket Hijacking) - **严重** 🔴

**漏洞详情：**
```python
# local_browser_bridge.py 第360行
async with websockets.serve(bridge.handle_websocket, "localhost", 8765):
```

- WebSocket服务器监听在 `localhost:8765` 上
- **完全没有实现Origin验证机制**
- 任何网站都可以通过JavaScript连接到该WebSocket服务

**攻击场景：**
1. 用户访问恶意网站 `evil.com`
2. 恶意网站JavaScript代码：
```javascript
const ws = new WebSocket('ws://localhost:8765');
ws.onopen = () => {
    // 窃取用户Cookie
    ws.send(JSON.stringify({
        action: 'init_browser',
        cookies: 'malicious_tracking_cookie'
    }));
    // 下载敏感文档
    ws.send(JSON.stringify({
        action: 'download_document',
        doc_id: 'sensitive_document_id'
    }));
};
```

**CWE-1385 合规性：** ❌ 违反
**OWASP参考：** A07:2021 – 身份验证和会话管理缺陷

### 1.2 缺失身份验证机制 - **严重** 🔴

**漏洞详情：**
```python
# local_browser_bridge.py 第35-39行
async def handle_websocket(self, websocket, path):
    client_ip = websocket.remote_address[0]
    logger.info(f"新连接来自: {client_ip}")
    # 无任何身份验证即接受连接
```

- 没有Token验证
- 没有API密钥
- 没有握手协议
- 仅记录IP地址，但不进行验证

### 1.3 敏感数据传输安全 - **高风险** 🟡

**Cookie处理漏洞：**
```python
# local_browser_bridge.py 第296-321行
async def set_cookies(self, cookie_str):
    # Cookie以明文形式传输和存储
    for item in cookie_str.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
```

- Cookie通过非加密WebSocket传输
- 无数据完整性验证
- 无防重放攻击机制

### 1.4 浏览器控制权限过大 - **高风险** 🟡

```python
# local_browser_bridge.py 第114-123行
self.browser = self.playwright.chromium.launch_persistent_context(
    user_data_dir=user_data_dir,
    headless=False,
    channel='chrome'
)
```

- 使用持久化用户配置文件
- 可访问所有已登录网站
- 无沙箱隔离
- 无权限最小化

---

## 2. 具体安全漏洞分析

### 2.1 命令注入风险 - **中风险** 🟠

```python
# local_browser_bridge.py 第207行
doc_url = f"https://docs.qq.com/sheet/{doc_id}"
```
- 缺少对 `doc_id` 的验证和清理
- 可能导致URL操纵攻击

### 2.2 路径遍历漏洞 - **中风险** 🟠

```python
# local_browser_bridge.py 第269-271行
filename = f"doc_{doc_id}_{timestamp}.{format_type}"
filepath = os.path.join(self.download_dir, filename)
download.save_as(filepath)
```
- 未验证文件名安全性
- 可能覆盖系统文件

### 2.3 拒绝服务(DoS)攻击 - **中风险** 🟠

- 无连接数限制
- 无请求频率限制
- 无资源消耗控制
- 恶意网站可发起大量下载请求耗尽系统资源

### 2.4 信息泄露 - **低风险** 🟢

```python
# local_browser_bridge.py 第71-78行
'data': {
    'bridge_version': '1.0.0',
    'browser_connected': self.browser is not None,
    'download_dir': self.download_dir
}
```
- 暴露系统路径信息
- 暴露软件版本信息

---

## 3. Web控制面板安全问题

### 3.1 前端安全缺陷

**web_control_panel.html 分析：**

1. **无CSP (Content Security Policy)头**
```html
<!-- 缺少CSP meta标签 -->
<head>
    <meta charset="UTF-8">
    <!-- 应添加: <meta http-equiv="Content-Security-Policy" content="..."> -->
```

2. **硬编码WebSocket地址**
```javascript
// 第449行
ws = new WebSocket('ws://localhost:8765');
```

3. **无输入验证**
```javascript
// 第543-548行
const cookieInput = document.getElementById('cookieInput').value.trim();
if (!cookieInput) {
    addLog('请输入Cookie字符串', 'error');
    return;
}
// 直接发送未验证的Cookie
```

---

## 4. 安全改进建议

### 4.1 立即修复 - Origin验证实现

```python
# 建议的安全WebSocket处理器
import hashlib
import secrets
import time
from urllib.parse import urlparse

class SecureLocalBrowserBridge:
    def __init__(self):
        # 生成会话Token
        self.session_token = secrets.token_hex(32)
        self.allowed_origins = [
            'https://your-trusted-domain.com',
            'http://localhost:3000'  # 开发环境
        ]
        self.rate_limiter = {}
        
    async def handle_websocket(self, websocket, path):
        # 1. 验证Origin
        origin = websocket.request_headers.get('Origin')
        if not self.verify_origin(origin):
            await websocket.close(code=1008, reason="Origin not allowed")
            logger.warning(f"拒绝连接 - 不允许的Origin: {origin}")
            return
            
        # 2. 验证Token
        try:
            first_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            auth_data = json.loads(first_message)
            
            if auth_data.get('type') != 'auth' or \
               not self.verify_token(auth_data.get('token')):
                await websocket.close(code=1008, reason="Authentication failed")
                return
                
        except (asyncio.TimeoutError, json.JSONDecodeError):
            await websocket.close(code=1002, reason="Invalid authentication")
            return
            
        # 3. 速率限制
        client_ip = websocket.remote_address[0]
        if not self.check_rate_limit(client_ip):
            await websocket.close(code=1008, reason="Rate limit exceeded")
            return
            
        # 继续处理已验证的连接
        await self.process_authenticated_connection(websocket)
        
    def verify_origin(self, origin):
        """验证Origin是否在白名单中"""
        if not origin:
            return False
        return origin in self.allowed_origins
        
    def verify_token(self, provided_token):
        """验证Token有效性"""
        if not provided_token:
            return False
        # 实现HMAC验证
        expected_token = hashlib.sha256(
            f"{self.session_token}:{int(time.time() // 300)}".encode()
        ).hexdigest()
        return secrets.compare_digest(provided_token, expected_token)
        
    def check_rate_limit(self, client_ip):
        """实现速率限制"""
        now = time.time()
        if client_ip not in self.rate_limiter:
            self.rate_limiter[client_ip] = []
        
        # 清理旧记录
        self.rate_limiter[client_ip] = [
            t for t in self.rate_limiter[client_ip] 
            if now - t < 60
        ]
        
        # 检查限制（每分钟最多10个请求）
        if len(self.rate_limiter[client_ip]) >= 10:
            return False
            
        self.rate_limiter[client_ip].append(now)
        return True
```

### 4.2 安全配置实现

```python
# secure_config.py
import os
from cryptography.fernet import Fernet

class SecurityConfig:
    def __init__(self):
        # 加密密钥管理
        self.encryption_key = self.load_or_generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # 安全配置
        self.config = {
            'websocket': {
                'host': '127.0.0.1',  # 仅本地
                'port': 8765,
                'ssl_enabled': False,  # 建议启用
                'max_connections': 5,
                'connection_timeout': 30,
                'message_size_limit': 1024 * 1024  # 1MB
            },
            'browser': {
                'sandbox_enabled': True,
                'persistent_context': False,
                'disable_images': True,
                'block_third_party_cookies': True,
                'user_agent_override': None
            },
            'security': {
                'csrf_protection': True,
                'xss_protection': True,
                'cors_enabled': True,
                'allowed_origins': ['https://trusted.com'],
                'session_timeout': 1800,  # 30分钟
                'max_download_size': 100 * 1024 * 1024  # 100MB
            }
        }
        
    def load_or_generate_key(self):
        """加载或生成加密密钥"""
        key_file = '.encryption.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # 仅所有者可读写
            return key
            
    def encrypt_sensitive_data(self, data):
        """加密敏感数据"""
        return self.cipher.encrypt(data.encode()).decode()
        
    def decrypt_sensitive_data(self, encrypted_data):
        """解密敏感数据"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

### 4.3 增强的浏览器隔离

```python
# browser_sandbox.py
import tempfile
import shutil
from contextlib import contextmanager

class BrowserSandbox:
    @contextmanager
    def isolated_browser_context(self, playwright):
        """创建隔离的浏览器上下文"""
        # 创建临时用户数据目录
        temp_dir = tempfile.mkdtemp(prefix='browser_sandbox_')
        
        try:
            # 启动隔离的浏览器实例
            browser = playwright.chromium.launch(
                headless=False,
                args=[
                    '--no-sandbox',  # 注意：生产环境应启用沙箱
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu',
                    '--disable-web-security',  # 仅测试环境
                    '--disable-features=VizDisplayCompositor',
                    '--disable-blink-features=AutomationControlled',
                    f'--user-data-dir={temp_dir}'
                ]
            )
            
            # 创建隔离上下文
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                java_script_enabled=True,
                bypass_csp=False,  # 遵守CSP
                ignore_https_errors=False,  # 不忽略HTTPS错误
                permissions=[],  # 无额外权限
                geolocation=None,
                locale='zh-CN'
            )
            
            yield context
            
        finally:
            # 清理
            context.close()
            browser.close()
            shutil.rmtree(temp_dir, ignore_errors=True)
```

### 4.4 安全的Cookie管理

```python
# secure_cookie_manager.py
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class SecureCookieManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
        self.cookie_storage = {}  # 应使用加密存储
        
    def validate_cookie_format(self, cookie_str: str) -> bool:
        """验证Cookie格式"""
        try:
            # 检查基本格式
            if not cookie_str or ';' not in cookie_str:
                return False
                
            # 检查恶意内容
            dangerous_patterns = [
                '<script', 'javascript:', 'onerror=', 'onclick=',
                '../', '..\\', '%2e%2e', '0x', '\\x'
            ]
            
            cookie_lower = cookie_str.lower()
            for pattern in dangerous_patterns:
                if pattern in cookie_lower:
                    return False
                    
            return True
            
        except Exception:
            return False
            
    def sign_cookie(self, cookie_data: Dict) -> str:
        """对Cookie进行签名"""
        # 添加时间戳
        cookie_data['timestamp'] = datetime.utcnow().isoformat()
        
        # 序列化数据
        data_str = json.dumps(cookie_data, sort_keys=True)
        
        # 生成签名
        signature = hmac.new(
            self.secret_key,
            data_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{data_str}|{signature}"
        
    def verify_cookie_signature(self, signed_cookie: str) -> Optional[Dict]:
        """验证Cookie签名"""
        try:
            data_str, signature = signed_cookie.split('|')
            
            # 验证签名
            expected_signature = hmac.new(
                self.secret_key,
                data_str.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
                
            # 解析数据
            cookie_data = json.loads(data_str)
            
            # 检查时间戳（30分钟有效期）
            timestamp = datetime.fromisoformat(cookie_data['timestamp'])
            if datetime.utcnow() - timestamp > timedelta(minutes=30):
                return None
                
            return cookie_data
            
        except Exception:
            return None
            
    def sanitize_cookies(self, cookies: List[Dict]) -> List[Dict]:
        """清理和验证Cookie"""
        sanitized = []
        
        for cookie in cookies:
            # 验证必需字段
            if not all(k in cookie for k in ['name', 'value', 'domain']):
                continue
                
            # 清理值
            sanitized_cookie = {
                'name': self.sanitize_string(cookie['name']),
                'value': self.sanitize_string(cookie['value']),
                'domain': self.validate_domain(cookie['domain']),
                'path': cookie.get('path', '/'),
                'secure': cookie.get('secure', True),
                'httpOnly': cookie.get('httpOnly', True),
                'sameSite': cookie.get('sameSite', 'Strict')
            }
            
            if sanitized_cookie['domain']:
                sanitized.append(sanitized_cookie)
                
        return sanitized
        
    @staticmethod
    def sanitize_string(value: str) -> str:
        """清理字符串值"""
        # 移除控制字符
        value = ''.join(char for char in value if ord(char) >= 32)
        # 限制长度
        return value[:4096]
        
    @staticmethod
    def validate_domain(domain: str) -> Optional[str]:
        """验证域名"""
        allowed_domains = ['.qq.com', '.tencent.com', 'localhost']
        
        for allowed in allowed_domains:
            if domain.endswith(allowed):
                return domain
                
        return None
```

### 4.5 前端安全增强

```html
<!-- secure_control_panel.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Content Security Policy -->
    <meta http-equiv="Content-Security-Policy" content="
        default-src 'self';
        script-src 'self' 'unsafe-inline';
        style-src 'self' 'unsafe-inline';
        img-src 'self' data: https:;
        connect-src 'self' ws://localhost:8765;
        font-src 'self';
        object-src 'none';
        media-src 'none';
        frame-src 'none';
        base-uri 'self';
        form-action 'self';
        frame-ancestors 'none';
        upgrade-insecure-requests;
    ">
    
    <!-- Security Headers -->
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-Frame-Options" content="DENY">
    <meta http-equiv="X-XSS-Protection" content="1; mode=block">
    <meta name="referrer" content="strict-origin-when-cross-origin">
    
    <title>安全的腾讯文档下载控制面板</title>
</head>
<body>
    <script>
    // 安全的WebSocket连接类
    class SecureWebSocketClient {
        constructor(url, token) {
            this.url = url;
            this.token = token;
            this.ws = null;
            this.reconnectAttempts = 0;
            this.maxReconnectAttempts = 3;
            this.messageQueue = [];
            this.isAuthenticated = false;
        }
        
        connect() {
            return new Promise((resolve, reject) => {
                try {
                    // 验证URL
                    if (!this.validateWebSocketURL(this.url)) {
                        reject(new Error('Invalid WebSocket URL'));
                        return;
                    }
                    
                    this.ws = new WebSocket(this.url);
                    
                    this.ws.onopen = async () => {
                        console.log('WebSocket连接已建立');
                        
                        // 发送认证信息
                        await this.authenticate();
                        
                        if (this.isAuthenticated) {
                            resolve(this);
                        } else {
                            reject(new Error('Authentication failed'));
                        }
                    };
                    
                    this.ws.onerror = (error) => {
                        console.error('WebSocket错误:', error);
                        reject(error);
                    };
                    
                    this.ws.onmessage = (event) => {
                        this.handleMessage(event);
                    };
                    
                    this.ws.onclose = () => {
                        console.log('WebSocket连接已关闭');
                        this.handleDisconnect();
                    };
                    
                } catch (error) {
                    reject(error);
                }
            });
        }
        
        validateWebSocketURL(url) {
            try {
                const wsUrl = new URL(url);
                // 仅允许本地连接
                return wsUrl.hostname === 'localhost' || 
                       wsUrl.hostname === '127.0.0.1';
            } catch {
                return false;
            }
        }
        
        async authenticate() {
            // 发送认证消息
            const authMessage = {
                type: 'auth',
                token: this.token,
                timestamp: Date.now()
            };
            
            this.ws.send(JSON.stringify(authMessage));
            
            // 等待认证响应
            return new Promise((resolve) => {
                const timeout = setTimeout(() => {
                    this.isAuthenticated = false;
                    resolve(false);
                }, 5000);
                
                const originalHandler = this.ws.onmessage;
                this.ws.onmessage = (event) => {
                    try {
                        const response = JSON.parse(event.data);
                        if (response.type === 'auth_response') {
                            clearTimeout(timeout);
                            this.isAuthenticated = response.success;
                            this.ws.onmessage = originalHandler;
                            resolve(response.success);
                        }
                    } catch (e) {
                        console.error('认证响应解析失败', e);
                    }
                };
            });
        }
        
        sendCommand(command) {
            if (!this.isAuthenticated) {
                throw new Error('Not authenticated');
            }
            
            // 输入验证
            if (!this.validateCommand(command)) {
                throw new Error('Invalid command format');
            }
            
            // 添加安全头
            const secureCommand = {
                ...command,
                timestamp: Date.now(),
                nonce: this.generateNonce()
            };
            
            this.ws.send(JSON.stringify(secureCommand));
        }
        
        validateCommand(command) {
            // 验证命令格式
            if (!command || typeof command !== 'object') {
                return false;
            }
            
            // 验证action字段
            const allowedActions = [
                'check_status', 
                'init_browser', 
                'login_check',
                'download_document',
                'close_browser'
            ];
            
            if (!allowedActions.includes(command.action)) {
                return false;
            }
            
            // 验证doc_id格式（如果存在）
            if (command.doc_id) {
                const docIdPattern = /^[A-Za-z0-9]{16,20}$/;
                if (!docIdPattern.test(command.doc_id)) {
                    return false;
                }
            }
            
            return true;
        }
        
        generateNonce() {
            // 生成随机数防止重放攻击
            return crypto.getRandomValues(new Uint8Array(16))
                .reduce((str, byte) => str + byte.toString(16).padStart(2, '0'), '');
        }
        
        handleMessage(event) {
            try {
                const response = JSON.parse(event.data);
                
                // 验证响应格式
                if (!this.validateResponse(response)) {
                    console.error('Invalid response format');
                    return;
                }
                
                // 处理响应
                this.processResponse(response);
                
            } catch (error) {
                console.error('消息处理失败:', error);
            }
        }
        
        validateResponse(response) {
            // 验证响应结构
            return response && 
                   typeof response === 'object' &&
                   'status' in response;
        }
        
        processResponse(response) {
            // 安全处理响应数据
            const sanitized = this.sanitizeResponse(response);
            
            // 触发自定义事件
            window.dispatchEvent(new CustomEvent('ws-response', {
                detail: sanitized
            }));
        }
        
        sanitizeResponse(response) {
            // 清理响应数据，防止XSS
            const sanitized = {};
            
            for (const [key, value] of Object.entries(response)) {
                if (typeof value === 'string') {
                    // 转义HTML特殊字符
                    sanitized[key] = this.escapeHtml(value);
                } else if (typeof value === 'object' && value !== null) {
                    sanitized[key] = this.sanitizeResponse(value);
                } else {
                    sanitized[key] = value;
                }
            }
            
            return sanitized;
        }
        
        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        handleDisconnect() {
            this.isAuthenticated = false;
            
            // 自动重连逻辑
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                
                setTimeout(() => {
                    this.connect().catch(console.error);
                }, 2000 * this.reconnectAttempts);
            }
        }
        
        close() {
            if (this.ws) {
                this.ws.close();
                this.ws = null;
            }
        }
    }
    
    // 使用示例
    async function initializeSecureConnection() {
        try {
            // 从安全存储获取Token
            const token = await getSecureToken();
            
            // 创建安全连接
            const client = new SecureWebSocketClient('ws://localhost:8765', token);
            await client.connect();
            
            console.log('安全连接已建立');
            
            // 绑定事件监听
            window.addEventListener('ws-response', (event) => {
                console.log('收到响应:', event.detail);
                updateUI(event.detail);
            });
            
            return client;
            
        } catch (error) {
            console.error('连接失败:', error);
            showError('无法建立安全连接，请检查本地服务是否运行');
        }
    }
    
    async function getSecureToken() {
        // 实现安全的Token获取逻辑
        // 可以从服务器获取或使用本地生成的Token
        return 'secure-token-here';
    }
    </script>
</body>
</html>
```

---

## 5. 安全测试清单

### 5.1 渗透测试项目

| 测试项 | 当前状态 | 建议措施 |
|--------|----------|----------|
| CSWSH攻击测试 | ❌ 易受攻击 | 实施Origin验证 |
| XSS注入测试 | ⚠️ 部分防护 | 增强输入验证 |
| CSRF攻击测试 | ❌ 无防护 | 添加CSRF Token |
| 命令注入测试 | ⚠️ 风险存在 | 参数化命令 |
| 路径遍历测试 | ⚠️ 风险存在 | 路径验证 |
| DoS攻击测试 | ❌ 无防护 | 速率限制 |
| 会话劫持测试 | ❌ 易受攻击 | Token机制 |
| 中间人攻击 | ⚠️ HTTP传输 | 启用TLS |

### 5.2 合规性检查

| 标准 | 合规状态 | 缺失项 |
|------|----------|--------|
| OWASP Top 10 | ❌ 不合规 | A01, A03, A05, A07 |
| CWE-1385 | ❌ 违反 | Origin验证缺失 |
| GDPR | ⚠️ 部分合规 | 数据加密、审计日志 |
| ISO 27001 | ❌ 不合规 | 访问控制、加密 |

---

## 6. 修复优先级和时间线

### 紧急修复 (24小时内)
1. **实施Origin验证** - 防止CSWSH攻击
2. **添加认证机制** - Token验证
3. **输入验证** - 防止注入攻击

### 高优先级 (1周内)
1. **实施速率限制**
2. **Cookie加密传输**
3. **CSP头部配置**
4. **浏览器沙箱隔离**

### 中优先级 (1月内)
1. **完整的TLS/SSL实施**
2. **审计日志系统**
3. **自动化安全测试**
4. **安全配置管理**

---

## 7. 结论

当前系统存在**严重安全风险**，特别是完全缺失的Origin验证使得系统极易受到CSWSH攻击。建议：

1. **立即停止生产环境使用**，直到关键漏洞修复
2. **实施提供的安全改进代码**
3. **进行完整的安全审计和渗透测试**
4. **建立安全开发生命周期(SDL)**
5. **定期安全更新和漏洞扫描**

## 8. 参考资料

- [OWASP WebSocket Security](https://owasp.org/www-project-web-security-testing-guide/)
- [CWE-1385: Missing Origin Validation](https://cwe.mitre.org/data/definitions/1385.html)
- [RFC 6455: The WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
- [Chrome DevTools Protocol Security](https://chromedevtools.github.io/devtools-protocol/)
- [NIST Cybersecurity Framework 2.0](https://www.nist.gov/cyberframework)

---

*报告生成时间: 2025-08-27*
*安全评估工具版本: 1.0.0*
*评估人员: Security Auditor (AI)*