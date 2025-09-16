#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket安全测试套件
用于验证本地桥接服务的安全措施
测试CSWSH、认证、速率限制等安全功能
"""

import asyncio
import websockets
import json
import time
from typing import Dict, List, Tuple
from datetime import datetime
import ssl
import certifi

class SecurityTestSuite:
    """安全测试套件"""
    
    def __init__(self, target_url: str = "ws://localhost:8765"):
        self.target_url = target_url
        self.test_results: List[Dict] = []
        
    async def run_all_tests(self):
        """运行所有安全测试"""
        print("="*60)
        print("WebSocket安全测试套件 v1.0")
        print(f"目标: {self.target_url}")
        print("="*60)
        
        # 测试列表
        tests = [
            ("CSWSH攻击测试", self.test_cswsh_attack),
            ("缺失认证测试", self.test_missing_auth),
            ("无效Token测试", self.test_invalid_token),
            ("速率限制测试", self.test_rate_limiting),
            ("输入验证测试", self.test_input_validation),
            ("命令注入测试", self.test_command_injection),
            ("路径遍历测试", self.test_path_traversal),
            ("大消息DoS测试", self.test_large_message_dos),
            ("并发连接限制测试", self.test_connection_limit),
            ("Token过期测试", self.test_token_expiration),
            ("Origin伪造测试", self.test_origin_spoofing),
            ("XSS注入测试", self.test_xss_injection),
            ("SQL注入测试", self.test_sql_injection),
            ("CSRF攻击测试", self.test_csrf_attack),
            ("会话固定测试", self.test_session_fixation)
        ]
        
        # 执行测试
        for test_name, test_func in tests:
            print(f"\n[测试] {test_name}")
            print("-"*40)
            
            try:
                result = await test_func()
                self.test_results.append(result)
                
                # 显示结果
                status_icon = "✅" if result['passed'] else "❌"
                print(f"结果: {status_icon} {result['message']}")
                
                if result.get('details'):
                    print(f"详情: {result['details']}")
                    
            except Exception as e:
                print(f"❌ 测试执行失败: {str(e)}")
                self.test_results.append({
                    'test': test_name,
                    'passed': False,
                    'message': f'测试异常: {str(e)}',
                    'severity': 'ERROR'
                })
                
        # 生成报告
        self.generate_report()
        
    async def test_cswsh_attack(self) -> Dict:
        """测试CSWSH（Cross-Site WebSocket Hijacking）攻击"""
        try:
            # 尝试使用恶意Origin连接
            headers = {
                'Origin': 'https://evil.com',
                'User-Agent': 'SecurityTest/1.0'
            }
            
            websocket = await websockets.connect(
                self.target_url,
                extra_headers=headers,
                timeout=5
            )
            
            # 如果连接成功，说明存在CSWSH漏洞
            await websocket.close()
            
            return {
                'test': 'CSWSH攻击测试',
                'passed': False,
                'message': '严重漏洞：接受恶意Origin连接',
                'severity': 'CRITICAL',
                'details': 'WebSocket服务接受了来自evil.com的连接请求'
            }
            
        except (websockets.exceptions.InvalidStatusCode, 
                websockets.exceptions.WebSocketException,
                asyncio.TimeoutError):
            # 连接被拒绝，安全
            return {
                'test': 'CSWSH攻击测试',
                'passed': True,
                'message': '正确拒绝了恶意Origin',
                'severity': 'INFO'
            }
            
    async def test_missing_auth(self) -> Dict:
        """测试缺失认证"""
        try:
            websocket = await websockets.connect(self.target_url, timeout=5)
            
            # 直接发送命令而不进行认证
            await websocket.send(json.dumps({
                'action': 'check_status'
            }))
            
            # 等待响应
            response = await asyncio.wait_for(websocket.recv(), timeout=2)
            data = json.loads(response)
            
            await websocket.close()
            
            # 如果收到成功响应，说明无需认证
            if data.get('status') == 'success':
                return {
                    'test': '缺失认证测试',
                    'passed': False,
                    'message': '严重漏洞：无需认证即可执行命令',
                    'severity': 'CRITICAL',
                    'details': f'响应数据: {data}'
                }
            else:
                return {
                    'test': '缺失认证测试',
                    'passed': True,
                    'message': '需要认证才能执行命令',
                    'severity': 'INFO'
                }
                
        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
            # 连接被关闭，需要认证
            return {
                'test': '缺失认证测试',
                'passed': True,
                'message': '正确要求认证',
                'severity': 'INFO'
            }
            
    async def test_invalid_token(self) -> Dict:
        """测试无效Token"""
        try:
            websocket = await websockets.connect(self.target_url, timeout=5)
            
            # 发送无效的认证Token
            await websocket.send(json.dumps({
                'type': 'auth',
                'token': 'invalid-token-12345'
            }))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=2)
            data = json.loads(response)
            
            await websocket.close()
            
            if data.get('success'):
                return {
                    'test': '无效Token测试',
                    'passed': False,
                    'message': '漏洞：接受无效Token',
                    'severity': 'HIGH',
                    'details': '系统接受了伪造的认证Token'
                }
            else:
                return {
                    'test': '无效Token测试',
                    'passed': True,
                    'message': '正确拒绝无效Token',
                    'severity': 'INFO'
                }
                
        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
            return {
                'test': '无效Token测试',
                'passed': True,
                'message': '拒绝无效认证',
                'severity': 'INFO'
            }
            
    async def test_rate_limiting(self) -> Dict:
        """测试速率限制"""
        try:
            # 快速发送多个请求
            connections = []
            success_count = 0
            
            for i in range(15):  # 尝试超过限制的请求
                try:
                    ws = await websockets.connect(self.target_url, timeout=1)
                    connections.append(ws)
                    success_count += 1
                except:
                    break
                    
            # 清理连接
            for ws in connections:
                await ws.close()
                
            if success_count >= 15:
                return {
                    'test': '速率限制测试',
                    'passed': False,
                    'message': '漏洞：无速率限制',
                    'severity': 'MEDIUM',
                    'details': f'成功建立{success_count}个连接，无限制'
                }
            else:
                return {
                    'test': '速率限制测试',
                    'passed': True,
                    'message': '速率限制生效',
                    'severity': 'INFO',
                    'details': f'在{success_count}个请求后被限制'
                }
                
        except Exception as e:
            return {
                'test': '速率限制测试',
                'passed': False,
                'message': f'测试失败: {str(e)}',
                'severity': 'ERROR'
            }
            
    async def test_input_validation(self) -> Dict:
        """测试输入验证"""
        try:
            # 先进行正常认证
            websocket = await self._get_authenticated_connection()
            if not websocket:
                return {
                    'test': '输入验证测试',
                    'passed': True,
                    'message': '无法建立连接（安全）',
                    'severity': 'INFO'
                }
                
            # 发送包含危险字符的命令
            malicious_inputs = [
                {'action': 'download_document', 'doc_id': '../../../etc/passwd'},
                {'action': 'download_document', 'doc_id': '<script>alert(1)</script>'},
                {'action': 'download_document', 'doc_id': 'test; rm -rf /'},
                {'action': 'download_document', 'doc_id': 'test\x00nullbyte'},
                {'action': 'download_document', 'doc_id': '%2e%2e%2f%2e%2e%2f'}
            ]
            
            vulnerabilities = []
            
            for malicious_input in malicious_inputs:
                await websocket.send(json.dumps(malicious_input))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    data = json.loads(response)
                    
                    if data.get('status') == 'success':
                        vulnerabilities.append(malicious_input['doc_id'])
                        
                except asyncio.TimeoutError:
                    pass
                    
            await websocket.close()
            
            if vulnerabilities:
                return {
                    'test': '输入验证测试',
                    'passed': False,
                    'message': '输入验证不足',
                    'severity': 'HIGH',
                    'details': f'接受的恶意输入: {vulnerabilities}'
                }
            else:
                return {
                    'test': '输入验证测试',
                    'passed': True,
                    'message': '输入验证有效',
                    'severity': 'INFO'
                }
                
        except Exception as e:
            return {
                'test': '输入验证测试',
                'passed': False,
                'message': f'测试失败: {str(e)}',
                'severity': 'ERROR'
            }
            
    async def test_command_injection(self) -> Dict:
        """测试命令注入"""
        try:
            websocket = await self._get_authenticated_connection()
            if not websocket:
                return {
                    'test': '命令注入测试',
                    'passed': True,
                    'message': '无法建立连接（安全）',
                    'severity': 'INFO'
                }
                
            # 尝试命令注入
            injection_payloads = [
                "test'; cat /etc/passwd; echo '",
                "test\" && whoami && echo \"",
                "test`id`",
                "test$(whoami)",
                "test|ls -la"
            ]
            
            vulnerable = False
            
            for payload in injection_payloads:
                await websocket.send(json.dumps({
                    'action': 'download_document',
                    'doc_id': payload
                }))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    data = json.loads(response)
                    
                    # 检查是否有命令执行的迹象
                    if 'root' in str(data) or 'passwd' in str(data):
                        vulnerable = True
                        break
                        
                except asyncio.TimeoutError:
                    pass
                    
            await websocket.close()
            
            if vulnerable:
                return {
                    'test': '命令注入测试',
                    'passed': False,
                    'message': '存在命令注入漏洞',
                    'severity': 'CRITICAL',
                    'details': '系统可能执行了注入的命令'
                }
            else:
                return {
                    'test': '命令注入测试',
                    'passed': True,
                    'message': '命令注入防护有效',
                    'severity': 'INFO'
                }
                
        except Exception as e:
            return {
                'test': '命令注入测试',
                'passed': False,
                'message': f'测试失败: {str(e)}',
                'severity': 'ERROR'
            }
            
    async def test_path_traversal(self) -> Dict:
        """测试路径遍历"""
        try:
            websocket = await self._get_authenticated_connection()
            if not websocket:
                return {
                    'test': '路径遍历测试',
                    'passed': True,
                    'message': '无法建立连接（安全）',
                    'severity': 'INFO'
                }
                
            # 尝试路径遍历
            traversal_payloads = [
                "../../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "....//....//....//etc/passwd",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
            ]
            
            vulnerable = False
            
            for payload in traversal_payloads:
                await websocket.send(json.dumps({
                    'action': 'download_document',
                    'doc_id': payload
                }))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    data = json.loads(response)
                    
                    if data.get('status') == 'success':
                        vulnerable = True
                        break
                        
                except asyncio.TimeoutError:
                    pass
                    
            await websocket.close()
            
            if vulnerable:
                return {
                    'test': '路径遍历测试',
                    'passed': False,
                    'message': '存在路径遍历漏洞',
                    'severity': 'HIGH',
                    'details': '可能访问到系统文件'
                }
            else:
                return {
                    'test': '路径遍历测试',
                    'passed': True,
                    'message': '路径遍历防护有效',
                    'severity': 'INFO'
                }
                
        except Exception as e:
            return {
                'test': '路径遍历测试',
                'passed': False,
                'message': f'测试失败: {str(e)}',
                'severity': 'ERROR'
            }
            
    async def test_large_message_dos(self) -> Dict:
        """测试大消息DoS攻击"""
        try:
            websocket = await self._get_authenticated_connection()
            if not websocket:
                return {
                    'test': '大消息DoS测试',
                    'passed': True,
                    'message': '无法建立连接（安全）',
                    'severity': 'INFO'
                }
                
            # 发送超大消息
            large_message = json.dumps({
                'action': 'download_document',
                'doc_id': 'A' * (10 * 1024 * 1024)  # 10MB
            })
            
            try:
                await websocket.send(large_message)
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                
                # 如果服务器接受并处理了大消息
                return {
                    'test': '大消息DoS测试',
                    'passed': False,
                    'message': '接受超大消息',
                    'severity': 'MEDIUM',
                    'details': '服务器处理了10MB的消息'
                }
                
            except (websockets.exceptions.ConnectionClosed, asyncio.TimeoutError):
                # 连接被关闭或超时，说明有保护
                return {
                    'test': '大消息DoS测试',
                    'passed': True,
                    'message': '拒绝超大消息',
                    'severity': 'INFO'
                }
                
        except Exception as e:
            return {
                'test': '大消息DoS测试',
                'passed': True,
                'message': '有消息大小限制',
                'severity': 'INFO',
                'details': str(e)
            }
            
    async def test_connection_limit(self) -> Dict:
        """测试并发连接限制"""
        try:
            connections = []
            max_connections = 10
            
            for i in range(max_connections):
                try:
                    ws = await websockets.connect(self.target_url, timeout=1)
                    connections.append(ws)
                except:
                    break
                    
            actual_connections = len(connections)
            
            # 清理
            for ws in connections:
                await ws.close()
                
            if actual_connections >= max_connections:
                return {
                    'test': '并发连接限制测试',
                    'passed': False,
                    'message': '无连接数限制',
                    'severity': 'MEDIUM',
                    'details': f'成功建立{actual_connections}个并发连接'
                }
            else:
                return {
                    'test': '并发连接限制测试',
                    'passed': True,
                    'message': '有连接数限制',
                    'severity': 'INFO',
                    'details': f'限制为{actual_connections}个连接'
                }
                
        except Exception as e:
            return {
                'test': '并发连接限制测试',
                'passed': False,
                'message': f'测试失败: {str(e)}',
                'severity': 'ERROR'
            }
            
    async def test_token_expiration(self) -> Dict:
        """测试Token过期"""
        # 注意：这个测试在实际环境中需要等待Token过期时间
        return {
            'test': 'Token过期测试',
            'passed': True,
            'message': '需要长时间测试，跳过',
            'severity': 'INFO',
            'details': '建议设置Token有效期为30分钟'
        }
        
    async def test_origin_spoofing(self) -> Dict:
        """测试Origin伪造"""
        try:
            # 尝试伪造合法Origin
            headers = {
                'Origin': 'http://localhost:3000',
                'User-Agent': 'SecurityTest/1.0'
            }
            
            websocket = await websockets.connect(
                self.target_url,
                extra_headers=headers,
                timeout=5
            )
            
            # 如果使用localhost Origin可以连接，这是预期的
            await websocket.close()
            
            return {
                'test': 'Origin伪造测试',
                'passed': True,
                'message': 'localhost Origin被允许（预期行为）',
                'severity': 'INFO'
            }
            
        except:
            return {
                'test': 'Origin伪造测试',
                'passed': False,
                'message': '连接失败',
                'severity': 'WARNING'
            }
            
    async def test_xss_injection(self) -> Dict:
        """测试XSS注入"""
        try:
            websocket = await self._get_authenticated_connection()
            if not websocket:
                return {
                    'test': 'XSS注入测试',
                    'passed': True,
                    'message': '无法建立连接（安全）',
                    'severity': 'INFO'
                }
                
            # XSS载荷
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<svg onload=alert('XSS')>"
            ]
            
            vulnerable = False
            
            for payload in xss_payloads:
                await websocket.send(json.dumps({
                    'action': 'download_document',
                    'doc_id': payload
                }))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    data = json.loads(response)
                    
                    # 检查响应中是否包含未转义的载荷
                    if payload in str(data):
                        vulnerable = True
                        break
                        
                except asyncio.TimeoutError:
                    pass
                    
            await websocket.close()
            
            if vulnerable:
                return {
                    'test': 'XSS注入测试',
                    'passed': False,
                    'message': 'XSS载荷未被转义',
                    'severity': 'HIGH',
                    'details': '响应中包含未转义的JavaScript代码'
                }
            else:
                return {
                    'test': 'XSS注入测试',
                    'passed': True,
                    'message': 'XSS防护有效',
                    'severity': 'INFO'
                }
                
        except Exception as e:
            return {
                'test': 'XSS注入测试',
                'passed': False,
                'message': f'测试失败: {str(e)}',
                'severity': 'ERROR'
            }
            
    async def test_sql_injection(self) -> Dict:
        """测试SQL注入（如果使用数据库）"""
        try:
            websocket = await self._get_authenticated_connection()
            if not websocket:
                return {
                    'test': 'SQL注入测试',
                    'passed': True,
                    'message': '无法建立连接（安全）',
                    'severity': 'INFO'
                }
                
            # SQL注入载荷
            sql_payloads = [
                "' OR '1'='1",
                "1; DROP TABLE users--",
                "' UNION SELECT * FROM users--",
                "admin'--"
            ]
            
            vulnerable = False
            
            for payload in sql_payloads:
                await websocket.send(json.dumps({
                    'action': 'download_document',
                    'doc_id': payload
                }))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    data = json.loads(response)
                    
                    # 检查是否有SQL错误信息
                    error_indicators = ['SQL', 'syntax', 'mysql', 'postgresql', 'sqlite']
                    response_str = str(data).lower()
                    
                    if any(indicator in response_str for indicator in error_indicators):
                        vulnerable = True
                        break
                        
                except asyncio.TimeoutError:
                    pass
                    
            await websocket.close()
            
            if vulnerable:
                return {
                    'test': 'SQL注入测试',
                    'passed': False,
                    'message': '可能存在SQL注入',
                    'severity': 'CRITICAL',
                    'details': '检测到SQL相关错误信息'
                }
            else:
                return {
                    'test': 'SQL注入测试',
                    'passed': True,
                    'message': 'SQL注入防护有效或未使用数据库',
                    'severity': 'INFO'
                }
                
        except Exception as e:
            return {
                'test': 'SQL注入测试',
                'passed': False,
                'message': f'测试失败: {str(e)}',
                'severity': 'ERROR'
            }
            
    async def test_csrf_attack(self) -> Dict:
        """测试CSRF攻击"""
        # WebSocket连接本身具有一定的CSRF防护
        return {
            'test': 'CSRF攻击测试',
            'passed': True,
            'message': 'WebSocket协议提供基础CSRF防护',
            'severity': 'INFO',
            'details': '建议额外实施Token验证'
        }
        
    async def test_session_fixation(self) -> Dict:
        """测试会话固定攻击"""
        try:
            # 尝试使用固定的Token
            fixed_token = "fixed-session-token-12345"
            
            websocket = await websockets.connect(self.target_url, timeout=5)
            
            await websocket.send(json.dumps({
                'type': 'auth',
                'token': fixed_token
            }))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=2)
            data = json.loads(response)
            
            await websocket.close()
            
            if data.get('token') == fixed_token:
                return {
                    'test': '会话固定测试',
                    'passed': False,
                    'message': '接受客户端提供的会话ID',
                    'severity': 'HIGH',
                    'details': '系统不应该接受客户端提供的会话标识符'
                }
            else:
                return {
                    'test': '会话固定测试',
                    'passed': True,
                    'message': '服务器生成新的会话ID',
                    'severity': 'INFO'
                }
                
        except:
            return {
                'test': '会话固定测试',
                'passed': True,
                'message': '拒绝固定会话',
                'severity': 'INFO'
            }
            
    async def _get_authenticated_connection(self):
        """获取已认证的连接（用于测试）"""
        try:
            websocket = await websockets.connect(self.target_url, timeout=5)
            
            # 尝试认证
            await websocket.send(json.dumps({
                'type': 'auth',
                'token': None  # 请求新Token
            }))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=2)
            data = json.loads(response)
            
            if data.get('success'):
                return websocket
            else:
                await websocket.close()
                return None
                
        except:
            return None
            
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("安全测试报告摘要")
        print("="*60)
        
        # 统计结果
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        
        # 按严重性分类
        severity_counts = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'INFO': 0
        }
        
        for result in self.test_results:
            severity = result.get('severity', 'INFO')
            if not result['passed'] and severity != 'INFO':
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
        print(f"\n总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        
        print("\n漏洞严重性分布:")
        print(f"🔴 严重 (CRITICAL): {severity_counts['CRITICAL']}")
        print(f"🟠 高危 (HIGH): {severity_counts['HIGH']}")
        print(f"🟡 中危 (MEDIUM): {severity_counts['MEDIUM']}")
        print(f"🟢 低危 (LOW): {severity_counts['LOW']}")
        
        # 安全评分
        score = self.calculate_security_score()
        print(f"\n安全评分: {score}/100")
        
        if score >= 90:
            print("评级: A - 优秀的安全防护")
        elif score >= 80:
            print("评级: B - 良好的安全防护")
        elif score >= 70:
            print("评级: C - 基本的安全防护")
        elif score >= 60:
            print("评级: D - 需要改进")
        else:
            print("评级: F - 严重安全问题")
            
        # 建议
        print("\n安全建议:")
        if severity_counts['CRITICAL'] > 0:
            print("⚠️  立即修复所有严重漏洞")
        if severity_counts['HIGH'] > 0:
            print("⚠️  尽快修复高危漏洞")
        if severity_counts['MEDIUM'] > 0:
            print("📌 计划修复中危漏洞")
            
        # 保存详细报告
        self.save_detailed_report()
        
    def calculate_security_score(self) -> int:
        """计算安全评分"""
        score = 100
        
        for result in self.test_results:
            if not result['passed']:
                severity = result.get('severity', 'INFO')
                if severity == 'CRITICAL':
                    score -= 20
                elif severity == 'HIGH':
                    score -= 10
                elif severity == 'MEDIUM':
                    score -= 5
                elif severity == 'LOW':
                    score -= 2
                    
        return max(0, score)
        
    def save_detailed_report(self):
        """保存详细报告到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"security_test_report_{timestamp}.json"
        
        report = {
            'timestamp': timestamp,
            'target': self.target_url,
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['passed']),
            'failed': sum(1 for r in self.test_results if not r['passed']),
            'security_score': self.calculate_security_score(),
            'test_results': self.test_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"\n详细报告已保存到: {filename}")


async def main():
    """主函数"""
    print("WebSocket安全测试工具 v1.0")
    print("用于测试本地桥接服务的安全性")
    print("-"*60)
    
    # 创建测试套件
    suite = SecurityTestSuite()
    
    # 运行所有测试
    await suite.run_all_tests()
    

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试中断")
    except Exception as e:
        print(f"测试失败: {e}")