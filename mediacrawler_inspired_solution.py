#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MediaCrawler启发的解决方案
核心思想：不破解加密，而是调用腾讯自己的解密函数
"""

import json
import time
import base64
import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TencentDocSmartCrawler:
    """
    基于MediaCrawler思路的腾讯文档爬虫
    核心：找到并调用腾讯文档自己的解密函数
    """
    
    def __init__(self):
        self.cookie_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
        self.page = None
        self.context = None
        
    async def init_browser(self):
        """初始化浏览器，保持登录状态"""
        
        # 加载Cookie
        with open(self.cookie_file, 'r') as f:
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
        
        playwright = await async_playwright().start()
        
        # MediaCrawler的关键：使用真实的浏览器环境
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox'
            ]
        )
        
        self.context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        # 注入stealth.js（MediaCrawler的反检测技术）
        await self.context.add_init_script("""
            // 移除webdriver检测
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 添加chrome对象
            window.chrome = {
                runtime: {},
            };
            
            // 修复权限查询
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        await self.context.add_cookies(cookies)
        self.page = await self.context.new_page()
        
        logger.info("浏览器环境初始化完成")
        
    async def find_decrypt_functions(self):
        """
        MediaCrawler的核心技术：找到平台自己的加密/解密函数
        不逆向，直接调用
        """
        
        # 访问文档页面
        doc_id = "DWEVjZndkR2xVSWJN"
        await self.page.goto(f"https://docs.qq.com/sheet/{doc_id}", 
                             wait_until='domcontentloaded')
        
        # 等待JS加载
        await self.page.wait_for_timeout(3000)
        
        # 步骤1：找到腾讯文档的解密函数
        decrypt_functions = await self.page.evaluate("""
            () => {
                const functions = {};
                
                // 查找全局对象中的解密相关函数
                for (const key in window) {
                    if (typeof window[key] === 'function') {
                        const funcStr = window[key].toString();
                        // 寻找可能的解密函数
                        if (funcStr.includes('protobuf') || 
                            funcStr.includes('decode') || 
                            funcStr.includes('decrypt') ||
                            funcStr.includes('parse') ||
                            funcStr.includes('workbook')) {
                            functions[key] = true;
                        }
                    }
                }
                
                // 查找可能的腾讯文档API对象
                const possibleAPIs = [
                    'TencentDoc',
                    'QQDoc',
                    'DocAPI',
                    'SheetAPI',
                    'alloy',
                    'AlloyEditor',
                    'TTI',
                    'DOC'
                ];
                
                for (const api of possibleAPIs) {
                    if (window[api]) {
                        functions[api] = typeof window[api];
                    }
                }
                
                return functions;
            }
        """)
        
        logger.info(f"找到可能的API对象: {list(decrypt_functions.keys())}")
        
        # 步骤2：查找Protobuf解码器
        protobuf_decoder = await self.page.evaluate("""
            () => {
                // 查找protobuf相关对象
                const proto = window.protobuf || window.Proto || window.pb;
                if (proto) {
                    return {
                        found: true,
                        methods: Object.keys(proto)
                    };
                }
                
                // 查找require或import的protobuf
                if (typeof require !== 'undefined') {
                    try {
                        const pb = require('protobufjs');
                        return {
                            found: true,
                            type: 'require'
                        };
                    } catch (e) {}
                }
                
                return {found: false};
            }
        """)
        
        logger.info(f"Protobuf解码器: {protobuf_decoder}")
        
        return decrypt_functions
        
    async def intercept_and_decode(self):
        """
        MediaCrawler的精髓：拦截API调用，使用官方函数解码
        """
        
        # 注入拦截代码
        await self.page.evaluate("""
            // MediaCrawler技术：拦截关键API调用
            (() => {
                // 保存原始的fetch
                const originalFetch = window.fetch;
                
                window.fetch = async function(...args) {
                    const response = await originalFetch.apply(this, args);
                    
                    // 克隆响应
                    const cloned = response.clone();
                    
                    // 如果是opendoc接口
                    if (args[0].includes('opendoc')) {
                        try {
                            const text = await cloned.text();
                            
                            // 尝试解析EJS格式
                            if (text.startsWith('text\\ntext\\n')) {
                                const lines = text.split('\\n');
                                const jsonStr = decodeURIComponent(lines[3]);
                                const data = JSON.parse(jsonStr);
                                
                                // 关键：使用腾讯自己的函数解码workbook
                                if (data.workbook) {
                                    window.__capturedWorkbook = data.workbook;
                                    console.log('捕获到workbook数据');
                                    
                                    // 尝试找到解码函数
                                    if (window.decodeWorkbook) {
                                        window.__decodedData = window.decodeWorkbook(data.workbook);
                                    } else {
                                        // 尝试Base64解码
                                        try {
                                            const decoded = atob(data.workbook);
                                            window.__base64Decoded = decoded;
                                        } catch (e) {}
                                    }
                                }
                            }
                        } catch (e) {
                            console.error('解析失败:', e);
                        }
                    }
                    
                    return response;
                };
                
                // 拦截WebSocket用于实时数据
                const originalWS = window.WebSocket;
                window.WebSocket = function(url) {
                    const ws = new originalWS(url);
                    
                    ws.addEventListener('message', (event) => {
                        // 如果收到二进制数据
                        if (event.data instanceof ArrayBuffer) {
                            window.__wsBuffer = event.data;
                            console.log('捕获WebSocket二进制数据');
                            
                            // 尝试使用腾讯的解码函数
                            if (window.TTI && window.TTI.decode) {
                                try {
                                    window.__wsDecoded = window.TTI.decode(event.data);
                                } catch (e) {}
                            }
                        }
                    });
                    
                    return ws;
                };
            })();
        """)
        
        logger.info("API拦截注入完成")
        
    async def call_native_export(self):
        """
        最聪明的方法：直接调用腾讯文档的原生导出函数
        就像MediaCrawler直接调用小红书的sign函数
        """
        
        # 尝试触发原生导出
        export_result = await self.page.evaluate("""
            async () => {
                // 方法1：查找导出按钮并模拟点击
                const exportBtn = document.querySelector('[class*="export"], [title*="导出"], button:has-text("导出")');
                if (exportBtn) {
                    exportBtn.click();
                    return {method: 'button_click', success: true};
                }
                
                // 方法2：直接调用导出API（如果存在）
                if (window.AlloyEditor && window.AlloyEditor.export) {
                    const result = await window.AlloyEditor.export('xlsx');
                    return {method: 'api_call', result: result};
                }
                
                // 方法3：触发键盘快捷键
                document.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'e',
                    code: 'KeyE',
                    ctrlKey: true,
                    shiftKey: true
                }));
                
                return {method: 'keyboard', triggered: true};
            }
        """)
        
        logger.info(f"原生导出触发结果: {export_result}")
        
    async def extract_from_memory(self):
        """
        从内存中提取已解码的数据
        这是MediaCrawler的核心技术之一
        """
        
        # 获取所有可能包含数据的全局变量
        memory_data = await self.page.evaluate("""
            () => {
                const data = {};
                
                // 收集所有可能的数据
                if (window.__capturedWorkbook) {
                    data.workbook = window.__capturedWorkbook;
                }
                
                if (window.__base64Decoded) {
                    data.base64Decoded = window.__base64Decoded;
                }
                
                if (window.__wsBuffer) {
                    data.wsBuffer = Array.from(new Uint8Array(window.__wsBuffer));
                }
                
                if (window.__wsDecoded) {
                    data.wsDecoded = window.__wsDecoded;
                }
                
                // 查找内存中的表格数据
                for (const key in window) {
                    if (key.includes('sheet') || key.includes('table') || key.includes('grid')) {
                        const value = window[key];
                        if (value && typeof value === 'object' && 
                            (Array.isArray(value) || value.data || value.rows)) {
                            data[key] = value;
                        }
                    }
                }
                
                return data;
            }
        """)
        
        return memory_data
        
    async def find_mobile_api(self):
        """
        MediaCrawler的另一个技巧：寻找移动端/小程序API
        这些API通常更简单，返回明文数据
        """
        
        # 模拟移动端User-Agent
        mobile_page = await self.context.new_page()
        await mobile_page.set_user_agent(
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) '
            'AppleWebKit/605.1.15 (KHTML, like Gecko) '
            'Mobile/15E148 MicroMessenger/8.0.0'
        )
        
        # 访问移动版或小程序版
        doc_id = "DWEVjZndkR2xVSWJN"
        
        # 尝试不同的移动端URL
        mobile_urls = [
            f"https://docs.qq.com/mobile/sheet/{doc_id}",
            f"https://docs.qq.com/m/sheet/{doc_id}",
            f"https://docs.qq.com/wxmini/sheet/{doc_id}",
            f"https://m.docs.qq.com/sheet/{doc_id}"
        ]
        
        for url in mobile_urls:
            try:
                response = await mobile_page.goto(url, wait_until='domcontentloaded')
                if response.status == 200:
                    logger.info(f"✅ 找到移动端URL: {url}")
                    
                    # 检查是否有不同的API
                    apis = await mobile_page.evaluate("""
                        () => {
                            // 移动端可能使用不同的API
                            return {
                                hasMobileAPI: typeof window.MobileAPI !== 'undefined',
                                hasWxAPI: typeof window.wx !== 'undefined',
                                hasJsBridge: typeof window.WebViewJavascriptBridge !== 'undefined'
                            };
                        }
                    """)
                    
                    logger.info(f"移动端API: {apis}")
                    break
            except Exception as e:
                logger.debug(f"尝试 {url} 失败: {e}")
                
        await mobile_page.close()

async def main():
    """主函数"""
    crawler = TencentDocSmartCrawler()
    
    logger.info("=" * 60)
    logger.info("MediaCrawler启发的腾讯文档爬虫")
    logger.info("核心：不破解，而是调用官方函数")
    logger.info("=" * 60)
    
    try:
        # 初始化浏览器
        await crawler.init_browser()
        
        # 找到解密函数
        logger.info("\n步骤1: 寻找腾讯的解密函数")
        functions = await crawler.find_decrypt_functions()
        
        # 注入拦截
        logger.info("\n步骤2: 注入API拦截")
        await crawler.intercept_and_decode()
        
        # 触发导出
        logger.info("\n步骤3: 尝试触发原生导出")
        await crawler.call_native_export()
        
        # 等待处理
        await crawler.page.wait_for_timeout(3000)
        
        # 提取数据
        logger.info("\n步骤4: 从内存提取数据")
        memory_data = await crawler.extract_from_memory()
        
        if memory_data:
            output_file = f"/root/projects/tencent-doc-manager/mediacrawler_result_{int(time.time())}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"✅ 数据已保存: {output_file}")
        
        # 尝试移动端API
        logger.info("\n步骤5: 探索移动端API")
        await crawler.find_mobile_api()
        
    except Exception as e:
        logger.error(f"发生错误: {e}")
        
    finally:
        if crawler.page:
            await crawler.page.close()
        if crawler.context:
            await crawler.context.close()

if __name__ == "__main__":
    asyncio.run(main())