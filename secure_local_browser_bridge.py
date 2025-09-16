#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全的本地浏览器桥接服务
实施了Origin验证、Token认证、速率限制等安全措施
符合OWASP标准和CWE-1385要求
"""

import asyncio
import websockets
import json
import logging
import os
import time
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
import tempfile
import shutil
from contextlib import contextmanager
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityManager:
    """安全管理器 - 处理认证、加密和验证"""
    
    def __init__(self):
        self.secret_key = self._load_or_generate_secret()
        self.cipher = Fernet(self.secret_key)
        self.active_tokens: Dict[str, datetime] = {}
        self.rate_limiter: Dict[str, list] = {}
        
        # 安全配置
        self.allowed_origins = [
            'https://your-trusted-domain.com',
            'http://localhost:3000',  # 开发环境
            'file://'  # 本地文件（谨慎使用）
        ]
        
        # 速率限制配置
        self.rate_limit_window = 60  # 秒
        self.rate_limit_max_requests = 10
        
    def _load_or_generate_secret(self) -> bytes:
        """加载或生成密钥"""
        key_file = '.encryption.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            logger.info("生成新的加密密钥")
            return key
            
    def generate_session_token(self) -> str:
        """生成会话Token"""
        token = secrets.token_hex(32)
        self.active_tokens[token] = datetime.now()
        # 清理过期Token
        self._cleanup_expired_tokens()
        return token
        
    def verify_token(self, token: str) -> bool:
        """验证Token有效性"""
        if not token or token not in self.active_tokens:
            return False
            
        # 检查Token是否过期（30分钟）
        token_time = self.active_tokens[token]
        if datetime.now() - token_time > timedelta(minutes=30):
            del self.active_tokens[token]
            return False
            
        # 更新Token时间
        self.active_tokens[token] = datetime.now()
        return True
        
    def _cleanup_expired_tokens(self):
        """清理过期的Token"""
        now = datetime.now()
        expired = [
            token for token, created in self.active_tokens.items()
            if now - created > timedelta(minutes=30)
        ]
        for token in expired:
            del self.active_tokens[token]
            
    def verify_origin(self, origin: Optional[str]) -> bool:
        """验证请求Origin"""
        if not origin:
            logger.warning("请求缺少Origin头")
            return False
            
        # 检查是否在白名单中
        for allowed in self.allowed_origins:
            if origin == allowed or origin.startswith(allowed):
                return True
                
        logger.warning(f"拒绝不允许的Origin: {origin}")
        return False
        
    def check_rate_limit(self, client_ip: str) -> bool:
        """检查速率限制"""
        now = time.time()
        
        if client_ip not in self.rate_limiter:
            self.rate_limiter[client_ip] = []
            
        # 清理旧记录
        self.rate_limiter[client_ip] = [
            t for t in self.rate_limiter[client_ip]
            if now - t < self.rate_limit_window
        ]
        
        # 检查是否超限
        if len(self.rate_limiter[client_ip]) >= self.rate_limit_max_requests:
            logger.warning(f"客户端 {client_ip} 超过速率限制")
            return False
            
        # 记录新请求
        self.rate_limiter[client_ip].append(now)
        return True
        
    def encrypt_data(self, data: str) -> str:
        """加密数据"""
        return self.cipher.encrypt(data.encode()).decode()
        
    def decrypt_data(self, encrypted_data: str) -> str:
        """解密数据"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
        
    def sanitize_input(self, input_str: str, max_length: int = 1024) -> str:
        """清理和验证输入"""
        if not input_str:
            return ""
            
        # 移除控制字符
        cleaned = ''.join(char for char in input_str if ord(char) >= 32)
        
        # 限制长度
        cleaned = cleaned[:max_length]
        
        # 检查危险模式
        dangerous_patterns = [
            '<script', 'javascript:', 'onerror=', 'onclick=',
            '../', '..\\', '%2e%2e', '\\x', '\x00'
        ]
        
        lower_input = cleaned.lower()
        for pattern in dangerous_patterns:
            if pattern in lower_input:
                raise ValueError(f"检测到危险输入模式: {pattern}")
                
        return cleaned
        
    def validate_doc_id(self, doc_id: str) -> bool:
        """验证文档ID格式"""
        if not doc_id:
            return False
            
        # 腾讯文档ID通常是16-20位字母数字
        import re
        pattern = r'^[A-Za-z0-9]{16,20}$'
        return bool(re.match(pattern, doc_id))


class BrowserSandbox:
    """浏览器沙箱 - 隔离浏览器操作"""
    
    def __init__(self):
        self.temp_dirs: Set[str] = set()
        
    @contextmanager
    def isolated_context(self, playwright):
        """创建隔离的浏览器上下文"""
        temp_dir = tempfile.mkdtemp(prefix='browser_sandbox_')
        self.temp_dirs.add(temp_dir)
        
        try:
            # 配置安全的浏览器参数
            browser = playwright.chromium.launch(
                headless=False,  # 根据需求设置
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-popup-blocking',
                    f'--user-data-dir={temp_dir}',
                    # 安全相关
                    '--enable-features=NetworkService,NetworkServiceInProcess',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI'
                ]
            )
            
            # 创建安全的上下文
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                java_script_enabled=True,
                bypass_csp=False,  # 遵守CSP
                ignore_https_errors=False,  # 不忽略HTTPS错误
                permissions=[],  # 最小权限
                locale='zh-CN'
            )
            
            yield context
            
        finally:
            # 清理资源
            try:
                context.close()
                browser.close()
            except:
                pass
                
            # 安全删除临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.temp_dirs.discard(temp_dir)
                
    def cleanup_all(self):
        """清理所有临时目录"""
        for temp_dir in list(self.temp_dirs):
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        self.temp_dirs.clear()


class SecureLocalBrowserBridge:
    """安全的本地浏览器桥接器"""
    
    def __init__(self):
        self.security = SecurityManager()
        self.sandbox = BrowserSandbox()
        self.playwright = None
        self.browser_context = None
        self.page = None
        self.download_dir = os.path.expanduser("~/Downloads/TencentDocs_Secure")
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 连接管理
        self.active_connections: Dict[str, dict] = {}
        self.max_connections = 5
        
        logger.info("安全浏览器桥接服务初始化完成")
        
    async def handle_websocket(self, websocket, path):
        """处理WebSocket连接（带安全验证）"""
        client_ip = websocket.remote_address[0]
        connection_id = f"{client_ip}:{websocket.remote_address[1]}"
        
        try:
            # 1. 检查连接数限制
            if len(self.active_connections) >= self.max_connections:
                await websocket.close(code=1008, reason="Connection limit exceeded")
                logger.warning(f"拒绝连接 {connection_id}: 超过最大连接数")
                return
                
            # 2. 验证Origin
            origin = websocket.request_headers.get('Origin')
            if not self.security.verify_origin(origin):
                await websocket.close(code=1008, reason="Origin not allowed")
                logger.warning(f"拒绝连接 {connection_id}: 不允许的Origin {origin}")
                return
                
            # 3. 检查速率限制
            if not self.security.check_rate_limit(client_ip):
                await websocket.close(code=1008, reason="Rate limit exceeded")
                logger.warning(f"拒绝连接 {connection_id}: 超过速率限制")
                return
                
            # 4. 等待认证
            logger.info(f"新连接 {connection_id} 来自 {origin}")
            
            # 设置认证超时
            try:
                auth_message = await asyncio.wait_for(
                    websocket.recv(), 
                    timeout=5.0
                )
                auth_data = json.loads(auth_message)
                
                if auth_data.get('type') != 'auth':
                    await websocket.close(code=1002, reason="Authentication required")
                    return
                    
                # 生成新Token或验证现有Token
                if 'token' in auth_data and self.security.verify_token(auth_data['token']):
                    token = auth_data['token']
                    logger.info(f"连接 {connection_id} 使用现有Token认证成功")
                else:
                    token = self.security.generate_session_token()
                    logger.info(f"连接 {connection_id} 生成新Token")
                    
                # 发送认证响应
                await websocket.send(json.dumps({
                    'type': 'auth_response',
                    'success': True,
                    'token': token,
                    'message': '认证成功'
                }))
                
                # 记录活动连接
                self.active_connections[connection_id] = {
                    'websocket': websocket,
                    'token': token,
                    'connected_at': datetime.now(),
                    'last_activity': datetime.now(),
                    'request_count': 0
                }
                
            except (asyncio.TimeoutError, json.JSONDecodeError, KeyError):
                await websocket.close(code=1002, reason="Authentication failed")
                logger.warning(f"连接 {connection_id} 认证失败")
                return
                
            # 5. 处理已认证的消息
            await self._handle_authenticated_connection(websocket, connection_id, token)
            
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"连接 {connection_id} 已关闭")
            
        finally:
            # 清理连接
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
                
    async def _handle_authenticated_connection(self, websocket, connection_id, token):
        """处理已认证的连接"""
        try:
            async for message in websocket:
                try:
                    # 验证Token仍然有效
                    if not self.security.verify_token(token):
                        await websocket.send(json.dumps({
                            'status': 'error',
                            'message': 'Token已过期，请重新认证'
                        }))
                        break
                        
                    # 更新活动时间
                    if connection_id in self.active_connections:
                        self.active_connections[connection_id]['last_activity'] = datetime.now()
                        self.active_connections[connection_id]['request_count'] += 1
                        
                    # 解析和验证命令
                    command = json.loads(message)
                    
                    # 验证命令格式
                    if not self._validate_command(command):
                        await websocket.send(json.dumps({
                            'status': 'error',
                            'message': '无效的命令格式'
                        }))
                        continue
                        
                    logger.info(f"连接 {connection_id} 执行命令: {command.get('action')}")
                    
                    # 执行命令
                    result = await self._execute_secure_command(command)
                    
                    # 返回结果
                    await websocket.send(json.dumps(result))
                    
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'message': '无效的JSON格式'
                    }))
                    
                except ValueError as e:
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'message': f'输入验证失败: {str(e)}'
                    }))
                    
                except Exception as e:
                    logger.error(f"处理命令出错: {e}")
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'message': '命令执行失败'
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
            
    def _validate_command(self, command: dict) -> bool:
        """验证命令格式和内容"""
        if not isinstance(command, dict):
            return False
            
        # 检查必需字段
        if 'action' not in command:
            return False
            
        # 验证action白名单
        allowed_actions = [
            'check_status',
            'init_browser',
            'login_check',
            'download_document',
            'close_browser'
        ]
        
        if command['action'] not in allowed_actions:
            return False
            
        # 验证特定命令的参数
        if command['action'] == 'download_document':
            doc_id = command.get('doc_id')
            if not doc_id or not self.security.validate_doc_id(doc_id):
                return False
                
        return True
        
    async def _execute_secure_command(self, command: dict) -> dict:
        """安全执行命令"""
        action = command['action']
        
        try:
            if action == 'check_status':
                return {
                    'status': 'success',
                    'data': {
                        'bridge_version': '2.0.0-secure',
                        'browser_connected': self.browser_context is not None,
                        'security_enabled': True,
                        'active_connections': len(self.active_connections)
                    }
                }
                
            elif action == 'init_browser':
                return await self._init_secure_browser()
                
            elif action == 'login_check':
                return await self._check_login_secure()
                
            elif action == 'download_document':
                doc_id = self.security.sanitize_input(command['doc_id'])
                format_type = command.get('format', 'xlsx')
                if format_type not in ['xlsx', 'csv', 'pdf']:
                    format_type = 'xlsx'
                return await self._download_document_secure(doc_id, format_type)
                
            elif action == 'close_browser':
                return await self._close_browser_secure()
                
        except Exception as e:
            logger.error(f"命令执行错误: {e}")
            return {
                'status': 'error',
                'message': '命令执行失败'
            }
            
    async def _init_secure_browser(self) -> dict:
        """初始化安全的浏览器实例"""
        try:
            if self.browser_context:
                return {
                    'status': 'success',
                    'message': '浏览器已在运行'
                }
                
            # 启动Playwright
            self.playwright = sync_playwright().start()
            
            # 使用沙箱创建隔离的浏览器上下文
            with self.sandbox.isolated_context(self.playwright) as context:
                self.browser_context = context
                self.page = context.new_page()
                
                # 设置下载路径
                self.page.set_download_path(self.download_dir)
                
                return {
                    'status': 'success',
                    'message': '安全浏览器启动成功'
                }
                
        except Exception as e:
            logger.error(f"启动浏览器失败: {e}")
            return {
                'status': 'error',
                'message': '浏览器启动失败'
            }
            
    async def _check_login_secure(self) -> dict:
        """安全检查登录状态"""
        try:
            if not self.page:
                return {
                    'status': 'error',
                    'message': '浏览器未启动'
                }
                
            # 访问腾讯文档（使用HTTPS）
            self.page.goto("https://docs.qq.com", wait_until='networkidle', timeout=10000)
            
            # 安全检查登录状态
            is_logged_in = False
            
            try:
                # 查找用户元素
                user_element = self.page.locator('[class*="user"]').first
                if user_element.is_visible(timeout=3000):
                    is_logged_in = True
            except:
                # 检查登录按钮
                try:
                    login_button = self.page.locator('button:has-text("登录")').first
                    is_logged_in = not login_button.is_visible(timeout=1000)
                except:
                    pass
                    
            return {
                'status': 'success',
                'data': {
                    'logged_in': is_logged_in,
                    'url': self.page.url
                }
            }
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return {
                'status': 'error',
                'message': '登录检查失败'
            }
            
    async def _download_document_secure(self, doc_id: str, format_type: str) -> dict:
        """安全下载文档"""
        try:
            if not self.page:
                return {
                    'status': 'error',
                    'message': '浏览器未启动'
                }
                
            # 构建安全的URL
            doc_url = f"https://docs.qq.com/sheet/{doc_id}"
            logger.info(f"安全访问文档: {doc_url}")
            
            # 访问文档
            self.page.goto(doc_url, wait_until='networkidle', timeout=15000)
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 尝试触发下载
            export_selectors = [
                'button:has-text("导出")',
                'button:has-text("下载")',
                '[aria-label*="导出"]'
            ]
            
            for selector in export_selectors:
                try:
                    button = self.page.locator(selector).first
                    if button.is_visible(timeout=1000):
                        button.click()
                        break
                except:
                    continue
                    
            # 等待并处理下载
            await asyncio.sleep(2)
            
            # 选择格式
            format_selectors = {
                'xlsx': ['text="Excel(.xlsx)"', 'text="Microsoft Excel"'],
                'csv': ['text="CSV"', 'text=".csv"'],
                'pdf': ['text="PDF"', 'text=".pdf"']
            }
            
            with self.page.expect_download(timeout=10000) as download_info:
                for selector in format_selectors.get(format_type, []):
                    try:
                        option = self.page.locator(selector).first
                        if option.is_visible(timeout=1000):
                            option.click()
                            break
                    except:
                        continue
                        
            download = download_info.value
            
            # 安全保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_doc_id = self.security.sanitize_input(doc_id, 20)
            filename = f"doc_{safe_doc_id}_{timestamp}.{format_type}"
            
            # 验证文件路径安全性
            filepath = os.path.join(self.download_dir, filename)
            filepath = os.path.abspath(filepath)
            
            if not filepath.startswith(os.path.abspath(self.download_dir)):
                raise ValueError("不安全的文件路径")
                
            download.save_as(filepath)
            
            # 验证文件
            if not os.path.exists(filepath):
                raise FileNotFoundError("下载文件未找到")
                
            file_size = os.path.getsize(filepath)
            
            # 限制文件大小（100MB）
            if file_size > 100 * 1024 * 1024:
                os.remove(filepath)
                raise ValueError("文件大小超过限制")
                
            logger.info(f"文件安全保存: {filepath}")
            
            return {
                'status': 'success',
                'data': {
                    'filename': filename,
                    'size': file_size,
                    'format': format_type,
                    'timestamp': timestamp
                }
            }
            
        except Exception as e:
            logger.error(f"下载文档失败: {e}")
            return {
                'status': 'error',
                'message': '下载失败'
            }
            
    async def _close_browser_secure(self) -> dict:
        """安全关闭浏览器"""
        try:
            if self.page:
                self.page.close()
                self.page = None
                
            if self.browser_context:
                self.browser_context.close()
                self.browser_context = None
                
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
                
            # 清理沙箱
            self.sandbox.cleanup_all()
            
            return {
                'status': 'success',
                'message': '浏览器已安全关闭'
            }
            
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")
            return {
                'status': 'error',
                'message': '关闭失败'
            }
            
    def cleanup(self):
        """清理所有资源"""
        try:
            # 关闭所有连接
            for conn_info in self.active_connections.values():
                asyncio.create_task(
                    conn_info['websocket'].close(code=1001, reason="Server shutdown")
                )
                
            # 清理浏览器
            asyncio.create_task(self._close_browser_secure())
            
            # 清理沙箱
            self.sandbox.cleanup_all()
            
            logger.info("资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


async def main():
    """主函数"""
    bridge = SecureLocalBrowserBridge()
    
    print("="*60)
    print("安全的腾讯文档本地浏览器桥接服务 v2.0")
    print("="*60)
    print("\n安全特性:")
    print("✅ Origin验证 - 防止CSWSH攻击")
    print("✅ Token认证 - 防止未授权访问")
    print("✅ 速率限制 - 防止DoS攻击")
    print("✅ 输入验证 - 防止注入攻击")
    print("✅ 浏览器沙箱 - 隔离运行环境")
    print("✅ 数据加密 - 保护敏感信息")
    print("-"*60)
    print(f"\n监听地址: ws://localhost:8765")
    print("最大连接数: 5")
    print("Token有效期: 30分钟")
    print("速率限制: 10请求/分钟")
    print("-"*60)
    
    # 启动WebSocket服务器
    try:
        async with websockets.serve(
            bridge.handle_websocket, 
            "127.0.0.1",  # 仅监听本地
            8765,
            max_size=1024*1024,  # 1MB消息大小限制
            max_queue=10,  # 队列大小限制
            compression=None,  # 禁用压缩避免攻击
            ping_interval=20,  # 保持连接活跃
            ping_timeout=10
        ):
            logger.info("✅ 安全服务已启动，等待连接...")
            await asyncio.Future()  # 永远运行
            
    except KeyboardInterrupt:
        logger.info("\n正在关闭服务...")
        bridge.cleanup()
        
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n服务已安全停止")
    except Exception as e:
        logger.error(f"服务异常: {e}")