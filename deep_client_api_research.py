#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度研究腾讯文档的各种客户端API
灵感来源：MediaCrawler通过研究不同客户端找到最简单的API
"""

import json
import time
import hashlib
import hmac
import requests
from urllib.parse import urlencode
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TencentDocClientAPIResearch:
    """
    研究腾讯文档的各种客户端API
    目标：找到返回明文数据的API
    """
    
    def __init__(self):
        self.cookie_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
        self.load_cookies()
        
    def load_cookies(self):
        """加载Cookie"""
        with open(self.cookie_file, 'r') as f:
            cookie_data = json.load(f)
            self.cookie_str = cookie_data['current_cookies']
            
    def research_pc_client_api(self):
        """
        研究PC客户端API
        PC客户端可能使用不同的API端点
        """
        logger.info("\n" + "="*60)
        logger.info("研究1: PC客户端API")
        logger.info("="*60)
        
        doc_id = "DWEVjZndkR2xVSWJN"
        
        # PC客户端可能的API端点
        pc_endpoints = [
            # 客户端专用API
            f"https://docs.qq.com/client/api/sheet/export?docId={doc_id}",
            f"https://docs.qq.com/desktop/api/export?id={doc_id}",
            f"https://docs.qq.com/win32/api/sheet/{doc_id}/export",
            
            # 内部API
            f"https://docs.qq.com/internal/sheet/{doc_id}/data",
            f"https://docs.qq.com/private/api/sheet/content?id={doc_id}",
            
            # RPC风格API
            f"https://docs.qq.com/rpc/sheet.getContent?docId={doc_id}",
            f"https://docs.qq.com/service/sheet/download?id={doc_id}"
        ]
        
        headers = {
            'Cookie': self.cookie_str,
            # 伪装成PC客户端
            'User-Agent': 'TencentDocs/2.4.20 (Windows NT 10.0) QQ/9.6.7',
            'X-Client-Type': 'desktop',
            'X-Client-Version': '2.4.20',
            'X-Platform': 'windows'
        }
        
        for endpoint in pc_endpoints:
            try:
                response = requests.get(endpoint, headers=headers, timeout=5)
                logger.info(f"\n尝试: {endpoint}")
                logger.info(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    content = response.content
                    # 检查是否是明文数据
                    if b'<' in content[:100] or b'{' in content[:100]:
                        logger.info("✅ 可能找到有效的PC客户端API！")
                        return content
                        
            except Exception as e:
                logger.debug(f"失败: {e}")
                
    def research_mobile_app_api(self):
        """
        研究移动端App API
        移动端通常有更简单的API
        """
        logger.info("\n" + "="*60)
        logger.info("研究2: 移动端App API")
        logger.info("="*60)
        
        doc_id = "DWEVjZndkR2xVSWJN"
        
        # 移动端API端点
        mobile_endpoints = [
            # iOS/Android API
            f"https://docs.qq.com/mobile/api/v1/sheet/{doc_id}",
            f"https://docs.qq.com/app/sheet/content?id={doc_id}",
            f"https://api.docs.qq.com/mobile/sheet/{doc_id}/export",
            
            # 移动端专用域名
            f"https://m.docs.qq.com/api/sheet/{doc_id}",
            f"https://mobile.docs.qq.com/sheet/api/content/{doc_id}",
            
            # REST风格API
            f"https://docs.qq.com/api/v2/sheets/{doc_id}",
            f"https://docs.qq.com/rest/sheet/{doc_id}/content"
        ]
        
        # 模拟移动端请求头
        mobile_headers = {
            'Cookie': self.cookie_str,
            # iOS App
            'User-Agent': 'TencentDocs/3.2.1 (iPhone; iOS 14.0; Scale/3.00)',
            'X-Client-Type': 'ios',
            'X-App-Version': '3.2.1',
            'X-Device-Id': 'A1B2C3D4-E5F6-7890-ABCD-EF1234567890',
            'X-Platform': 'ios',
            'Accept': 'application/json'
        }
        
        for endpoint in mobile_endpoints:
            try:
                response = requests.get(endpoint, headers=mobile_headers, timeout=5)
                logger.info(f"\n尝试: {endpoint}")
                logger.info(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    # 检查响应类型
                    content_type = response.headers.get('Content-Type', '')
                    if 'json' in content_type:
                        logger.info("✅ 找到JSON API！")
                        data = response.json()
                        logger.info(f"JSON keys: {list(data.keys())[:5]}")
                        return data
                        
            except Exception as e:
                logger.debug(f"失败: {e}")
                
    def research_wechat_miniprogram_api(self):
        """
        研究微信小程序API
        小程序通常有独立的、更简单的API
        """
        logger.info("\n" + "="*60)
        logger.info("研究3: 微信小程序API")
        logger.info("="*60)
        
        doc_id = "DWEVjZndkR2xVSWJN"
        
        # 微信小程序API
        wechat_endpoints = [
            # 小程序专用API
            f"https://docs.qq.com/wxmini/api/sheet/{doc_id}",
            f"https://docs.qq.com/miniprogram/sheet/get?id={doc_id}",
            f"https://docs.qq.com/mp/api/document/{doc_id}",
            
            # 微信域名
            f"https://wx.docs.qq.com/sheet/{doc_id}/content",
            f"https://weixin.docs.qq.com/api/sheet/{doc_id}",
            
            # 小程序云函数API
            f"https://docs.qq.com/cloud/function/getSheet?docId={doc_id}",
            f"https://docs.qq.com/tcb/api/sheet/{doc_id}"
        ]
        
        # 模拟微信小程序请求
        wechat_headers = {
            'Cookie': self.cookie_str,
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.0',
            'X-Requested-With': 'com.tencent.mm',
            'Referer': 'https://servicewechat.com/',
            'X-Wechat-Application': 'TencentDocs',
            'Accept': 'application/json, text/plain, */*'
        }
        
        for endpoint in wechat_endpoints:
            try:
                response = requests.get(endpoint, headers=wechat_headers, timeout=5)
                logger.info(f"\n尝试: {endpoint}")
                logger.info(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    content = response.content
                    try:
                        data = response.json()
                        logger.info("✅ 找到微信小程序JSON API！")
                        return data
                    except:
                        pass
                        
            except Exception as e:
                logger.debug(f"失败: {e}")
                
    def research_enterprise_wechat_api(self):
        """
        研究企业微信API
        企业微信的文档功能可能有独立API
        """
        logger.info("\n" + "="*60)
        logger.info("研究4: 企业微信API")
        logger.info("="*60)
        
        doc_id = "DWEVjZndkR2xVSWJN"
        
        # 企业微信API
        work_endpoints = [
            # 企业微信文档API
            f"https://docs.qq.com/work/api/sheet/{doc_id}",
            f"https://work.docs.qq.com/api/document/{doc_id}",
            f"https://docs.qq.com/enterprise/sheet/content?id={doc_id}",
            
            # 企业微信域名
            f"https://work.weixin.qq.com/docs/api/sheet/{doc_id}",
            f"https://qywx.docs.qq.com/sheet/{doc_id}/data"
        ]
        
        work_headers = {
            'Cookie': self.cookie_str,
            'User-Agent': 'WeChatWork/3.1.10',
            'X-Enterprise-Id': '1000000',
            'X-Work-Client': 'true',
            'Accept': 'application/json'
        }
        
        for endpoint in work_endpoints:
            try:
                response = requests.get(endpoint, headers=work_headers, timeout=5)
                logger.info(f"\n尝试: {endpoint}")
                logger.info(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info("✅ 找到企业微信API！")
                    
            except Exception as e:
                logger.debug(f"失败: {e}")
                
    def research_grpc_websocket_api(self):
        """
        研究gRPC/WebSocket等二进制协议
        某些客户端可能使用更高效的二进制协议
        """
        logger.info("\n" + "="*60)
        logger.info("研究5: gRPC/WebSocket API")
        logger.info("="*60)
        
        # WebSocket端点
        ws_endpoints = [
            "wss://docs.qq.com/ws/sheet",
            "wss://docs.qq.com/socket/v1",
            "wss://stream.docs.qq.com/sheet"
        ]
        
        # gRPC端点（HTTP/2）
        grpc_endpoints = [
            "https://docs.qq.com/grpc/SheetService/GetContent",
            "https://api.docs.qq.com/v1.Sheet/Export"
        ]
        
        logger.info("WebSocket和gRPC需要特殊的客户端实现")
        logger.info("这些协议可能返回二进制的Protobuf数据")
        
    def generate_sign(self, params, secret_key=""):
        """
        生成签名（如果需要）
        模仿MediaCrawler的签名生成
        """
        # 排序参数
        sorted_params = sorted(params.items())
        param_str = urlencode(sorted_params)
        
        # 生成签名
        if secret_key:
            sign = hmac.new(
                secret_key.encode(),
                param_str.encode(),
                hashlib.sha256
            ).hexdigest()
        else:
            sign = hashlib.md5(param_str.encode()).hexdigest()
            
        return sign
        
    def research_internal_api(self):
        """
        研究内部API（需要特殊认证）
        """
        logger.info("\n" + "="*60)
        logger.info("研究6: 内部/调试API")
        logger.info("="*60)
        
        doc_id = "DWEVjZndkR2xVSWJN"
        
        # 可能的内部API
        internal_endpoints = [
            # 调试API
            f"https://docs.qq.com/debug/sheet/{doc_id}",
            f"https://docs.qq.com/admin/api/sheet/{doc_id}",
            
            # 开发者API
            f"https://docs.qq.com/developer/v1/sheets/{doc_id}",
            f"https://api.docs.qq.com/internal/sheet/{doc_id}",
            
            # GraphQL API
            f"https://docs.qq.com/graphql",
        ]
        
        # GraphQL查询
        graphql_query = {
            "query": f"""
                query GetSheet {{
                    sheet(id: "{doc_id}") {{
                        id
                        title
                        content
                        cells {{
                            row
                            col
                            value
                        }}
                    }}
                }}
            """
        }
        
        headers = {
            'Cookie': self.cookie_str,
            'X-Debug-Mode': 'true',
            'X-Internal-Request': 'true'
        }
        
        # 尝试GraphQL
        try:
            response = requests.post(
                "https://docs.qq.com/graphql",
                json=graphql_query,
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                logger.info("✅ GraphQL API响应！")
                logger.info(f"响应: {response.text[:200]}")
        except Exception as e:
            logger.debug(f"GraphQL失败: {e}")

def main():
    """主函数"""
    researcher = TencentDocClientAPIResearch()
    
    logger.info("="*60)
    logger.info("腾讯文档客户端API深度研究")
    logger.info("灵感：MediaCrawler通过研究不同客户端找到最简单的API")
    logger.info("="*60)
    
    # 研究各种客户端API
    results = {
        'pc_client': researcher.research_pc_client_api(),
        'mobile_app': researcher.research_mobile_app_api(),
        'wechat_miniprogram': researcher.research_wechat_miniprogram_api(),
        'enterprise_wechat': researcher.research_enterprise_wechat_api(),
        'internal': researcher.research_internal_api()
    }
    
    # 其他协议
    researcher.research_grpc_websocket_api()
    
    # 总结
    logger.info("\n" + "="*60)
    logger.info("研究总结")
    logger.info("="*60)
    
    found_apis = [k for k, v in results.items() if v is not None]
    if found_apis:
        logger.info(f"✅ 找到可能有效的API: {found_apis}")
    else:
        logger.info("❌ 暂未找到返回明文数据的API")
        logger.info("\n可能的原因：")
        logger.info("1. 所有API都需要特殊的签名验证")
        logger.info("2. 腾讯统一了所有客户端的API")
        logger.info("3. 需要更深入的抓包分析")
        
    logger.info("\n下一步建议：")
    logger.info("1. 使用抓包工具分析真实的App请求")
    logger.info("2. 反编译移动端App查看API调用")
    logger.info("3. 研究腾讯文档的开放平台API")

if __name__ == "__main__":
    main()