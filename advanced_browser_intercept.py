#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级浏览器拦截技术 - 基于CDP和JavaScript Hook
受yt-dlp和undetected-chromedriver启发的解决方案
"""

import os
import json
import base64
import asyncio
import logging
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Page, CDPSession
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedTencentDocInterceptor:
    """高级腾讯文档拦截器 - 使用CDP和JS注入技术"""
    
    def __init__(self):
        self.intercepted_data = {}
        self.protobuf_responses = []
        self.download_blob = None
        
    async def inject_hooks(self, page: Page):
        """注入JavaScript钩子来拦截关键函数"""
        
        # 1. Hook XMLHttpRequest来捕获所有请求
        await page.evaluate("""
            // 保存原始的XMLHttpRequest
            const originalXHR = window.XMLHttpRequest;
            const xhrData = [];
            
            window.XMLHttpRequest = function() {
                const xhr = new originalXHR();
                const originalOpen = xhr.open;
                const originalSend = xhr.send;
                
                xhr.open = function(method, url, ...args) {
                    xhr._interceptedURL = url;
                    xhr._interceptedMethod = method;
                    return originalOpen.apply(this, [method, url, ...args]);
                };
                
                xhr.send = function(data) {
                    xhr.addEventListener('load', function() {
                        // 捕获响应
                        window.__interceptedResponses = window.__interceptedResponses || [];
                        window.__interceptedResponses.push({
                            url: xhr._interceptedURL,
                            method: xhr._interceptedMethod,
                            status: xhr.status,
                            response: xhr.response,
                            responseText: xhr.responseText,
                            responseType: xhr.responseType,
                            timestamp: Date.now()
                        });
                        
                        // 特别关注包含表格数据的响应
                        if (xhr._interceptedURL && xhr._interceptedURL.includes('opendoc')) {
                            console.log('Intercepted opendoc response:', xhr.response);
                            window.__lastOpendocResponse = xhr.response;
                        }
                    });
                    
                    return originalSend.apply(this, [data]);
                };
                
                return xhr;
            };
        """)
        
        # 2. Hook fetch API
        await page.evaluate("""
            const originalFetch = window.fetch;
            
            window.fetch = async function(...args) {
                const response = await originalFetch.apply(this, args);
                
                // 克隆响应以便读取
                const clonedResponse = response.clone();
                
                try {
                    // 尝试获取响应内容
                    const contentType = response.headers.get('content-type');
                    let responseData;
                    
                    if (contentType && contentType.includes('json')) {
                        responseData = await clonedResponse.json();
                    } else if (contentType && contentType.includes('text')) {
                        responseData = await clonedResponse.text();
                    } else {
                        responseData = await clonedResponse.arrayBuffer();
                    }
                    
                    // 存储拦截的数据
                    window.__fetchResponses = window.__fetchResponses || [];
                    window.__fetchResponses.push({
                        url: args[0],
                        data: responseData,
                        contentType: contentType,
                        timestamp: Date.now()
                    });
                    
                } catch (e) {
                    console.error('Failed to intercept fetch response:', e);
                }
                
                return response;
            };
        """)
        
        # 3. Hook Blob创建来捕获下载
        await page.evaluate("""
            const originalBlob = window.Blob;
            
            window.Blob = function(parts, options) {
                const blob = new originalBlob(parts, options);
                
                // 存储Blob数据
                window.__capturedBlobs = window.__capturedBlobs || [];
                window.__capturedBlobs.push({
                    parts: parts,
                    type: options ? options.type : undefined,
                    size: blob.size,
                    timestamp: Date.now()
                });
                
                // 如果是Excel文件类型，特别标记
                if (options && options.type && 
                    (options.type.includes('excel') || 
                     options.type.includes('spreadsheet'))) {
                    window.__lastExcelBlob = {
                        parts: parts,
                        type: options.type,
                        blob: blob
                    };
                    console.log('Captured Excel Blob!', options.type);
                }
                
                return blob;
            };
        """)
        
        # 4. Hook下载函数
        await page.evaluate("""
            // 拦截createElement来捕获下载链接
            const originalCreateElement = document.createElement;
            
            document.createElement = function(tagName) {
                const element = originalCreateElement.call(document, tagName);
                
                if (tagName.toLowerCase() === 'a') {
                    // 监听下载链接的点击
                    const originalClick = element.click;
                    element.click = function() {
                        if (element.download || element.href.startsWith('blob:')) {
                            window.__lastDownloadAttempt = {
                                href: element.href,
                                download: element.download,
                                timestamp: Date.now()
                            };
                            console.log('Download intercepted:', element.href);
                        }
                        return originalClick.apply(this, arguments);
                    };
                }
                
                return element;
            };
        """)
        
        # 5. Hook WebSocket用于实时数据
        await page.evaluate("""
            const originalWebSocket = window.WebSocket;
            
            window.WebSocket = function(url, protocols) {
                const ws = new originalWebSocket(url, protocols);
                
                window.__websocketMessages = window.__websocketMessages || [];
                
                ws.addEventListener('message', function(event) {
                    window.__websocketMessages.push({
                        url: url,
                        data: event.data,
                        timestamp: Date.now()
                    });
                    
                    // 检查是否是Protobuf数据
                    if (event.data instanceof ArrayBuffer || event.data instanceof Blob) {
                        console.log('Received binary WebSocket data');
                        window.__lastBinaryWSData = event.data;
                    }
                });
                
                return ws;
            };
        """)
        
        logger.info("JavaScript hooks 注入完成")
        
    async def setup_cdp_interception(self, page: Page):
        """设置CDP级别的网络拦截"""
        
        # 获取CDP session
        client = await page.context.new_cdp_session(page)
        
        # 启用网络域
        await client.send("Network.enable")
        await client.send("Fetch.enable", {
            "patterns": [
                {"urlPattern": "*", "requestStage": "Response"}
            ]
        })
        
        # 监听网络响应
        async def on_response(params):
            request_id = params.get('requestId')
            response = params.get('response', {})
            url = response.get('url', '')
            
            # 特别关注腾讯文档相关的响应
            if 'docs.qq.com' in url and ('opendoc' in url or 'export' in url):
                logger.info(f"CDP拦截到关键响应: {url}")
                
                try:
                    # 获取响应体
                    body_response = await client.send("Network.getResponseBody", {
                        "requestId": request_id
                    })
                    
                    body = body_response.get('body', '')
                    base64_encoded = body_response.get('base64Encoded', False)
                    
                    if base64_encoded:
                        # 解码base64数据
                        body = base64.b64decode(body)
                        logger.info(f"获取到二进制数据，大小: {len(body)} bytes")
                        
                        # 检查是否是Excel文件
                        if body[:4] == b'PK\x03\x04':
                            logger.info("✅ 拦截到真正的Excel文件！")
                            self.download_blob = body
                            return body
                    else:
                        logger.info(f"获取到文本数据，长度: {len(body)}")
                        
                    self.intercepted_data[url] = {
                        'body': body,
                        'headers': response.get('headers', {}),
                        'status': response.get('status')
                    }
                    
                except Exception as e:
                    logger.error(f"获取响应体失败: {e}")
        
        # 注册响应监听器
        client.on("Network.responseReceived", on_response)
        
        # 监听Fetch请求用于修改
        async def on_fetch_request(params):
            request_id = params.get('requestId')
            request = params.get('request', {})
            url = request.get('url', '')
            
            # 可以在这里修改请求
            if 'docs.qq.com' in url:
                logger.info(f"Fetch拦截: {url}")
                
                # 继续请求但可以修改headers
                await client.send("Fetch.continueRequest", {
                    "requestId": request_id,
                    "headers": request.get('headers', [])
                })
        
        client.on("Fetch.requestPaused", on_fetch_request)
        
        logger.info("CDP网络拦截设置完成")
        return client
        
    async def extract_table_data(self, page: Page) -> Optional[Dict]:
        """从页面提取表格数据"""
        
        # 尝试多种方法提取数据
        
        # 方法1: 从拦截的XHR响应中提取
        xhr_data = await page.evaluate("window.__interceptedResponses || []")
        for response in xhr_data:
            if 'opendoc' in response.get('url', ''):
                logger.info(f"找到opendoc响应: {response['url']}")
                return response
        
        # 方法2: 从拦截的Blob中提取
        blobs = await page.evaluate("window.__capturedBlobs || []")
        if blobs:
            logger.info(f"捕获了{len(blobs)}个Blob")
            excel_blob = await page.evaluate("window.__lastExcelBlob")
            if excel_blob:
                logger.info("找到Excel Blob！")
                return excel_blob
        
        # 方法3: 从WebSocket消息中提取
        ws_messages = await page.evaluate("window.__websocketMessages || []")
        if ws_messages:
            logger.info(f"捕获了{len(ws_messages)}个WebSocket消息")
            
        # 方法4: 直接从DOM提取渲染后的数据
        table_data = await page.evaluate("""
            // 查找所有表格
            const tables = document.querySelectorAll('table');
            const data = [];
            
            for (const table of tables) {
                const rows = [];
                const tableRows = table.querySelectorAll('tr');
                
                for (const tr of tableRows) {
                    const cells = [];
                    const tableCells = tr.querySelectorAll('td, th');
                    
                    for (const cell of tableCells) {
                        cells.push(cell.textContent.trim());
                    }
                    
                    if (cells.length > 0) {
                        rows.push(cells);
                    }
                }
                
                if (rows.length > 0) {
                    data.push(rows);
                }
            }
            
            return data;
        """)
        
        if table_data and len(table_data) > 0:
            logger.info(f"从DOM提取到{len(table_data)}个表格")
            return {'tables': table_data}
        
        return None

async def test_advanced_interception():
    """测试高级拦截技术"""
    
    interceptor = AdvancedTencentDocInterceptor()
    
    # 加载Cookie
    with open('/root/projects/tencent-doc-manager/config/cookies_new.json', 'r') as f:
        cookie_data = json.load(f)
        cookie_str = cookie_data['current_cookies']
    
    # 解析Cookie
    cookies = []
    for item in cookie_str.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookies.append({
                'name': key,
                'value': value,
                'domain': '.docs.qq.com',
                'path': '/'
            })
    
    async with async_playwright() as p:
        # 使用更隐蔽的浏览器配置
        browser = await p.chromium.launch(
            headless=True,  # 在服务器环境使用headless模式
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-web-security',
                '--disable-features=BlockInsecurePrivateNetworkRequests',
                '--disable-features=OutOfBlinkCors',
                '--no-sandbox'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # 添加cookies
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 注入hooks
        await interceptor.inject_hooks(page)
        
        # 设置CDP拦截
        cdp_session = await interceptor.setup_cdp_interception(page)
        
        # 访问文档
        doc_id = "DWEVjZndkR2xVSWJN"
        doc_url = f"https://docs.qq.com/sheet/{doc_id}"
        
        logger.info(f"访问文档: {doc_url}")
        
        try:
            await page.goto(doc_url, wait_until='networkidle', timeout=30000)
            
            # 等待页面加载
            await page.wait_for_timeout(5000)
            
            # 提取数据
            data = await interceptor.extract_table_data(page)
            
            if data:
                logger.info("✅ 成功提取数据！")
                
                # 保存结果
                output_file = f"/root/projects/tencent-doc-manager/advanced_intercept_result_{int(time.time())}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"数据已保存到: {output_file}")
                
                # 如果拦截到了真正的Excel文件
                if interceptor.download_blob:
                    excel_file = f"/root/projects/tencent-doc-manager/intercepted_excel_{int(time.time())}.xlsx"
                    with open(excel_file, 'wb') as f:
                        f.write(interceptor.download_blob)
                    logger.info(f"✅ Excel文件已保存: {excel_file}")
            else:
                logger.warning("未能提取到数据")
                
        except Exception as e:
            logger.error(f"发生错误: {e}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_advanced_interception())