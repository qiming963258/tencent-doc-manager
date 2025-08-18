#!/usr/bin/env python3
"""
自定义MCP Fetch服务器 - 无视robots.txt
支持绕过robots.txt和自定义User-Agent
"""

import asyncio
import json
import aiohttp
import sys
from typing import Dict, Any, Optional

class UnrestrictedFetchServer:
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.ignore_robots = True
        
    async def fetch_url(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """获取URL内容，无视robots.txt"""
        
        default_headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        if headers:
            default_headers.update(headers)
            
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers=default_headers
            ) as session:
                async with session.get(url) as response:
                    content = await response.text()
                    
                    return {
                        "url": url,
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "content": content,
                        "success": True,
                        "robots_ignored": self.ignore_robots
                    }
                    
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "success": False,
                "robots_ignored": self.ignore_robots
            }

async def main():
    """MCP服务器主函数"""
    print("自定义无限制Fetch服务器启动")
    server = UnrestrictedFetchServer()
    
    # 简单的测试
    test_url = "https://httpbin.org/get"
    result = await server.fetch_url(test_url)
    print(f"测试结果: {result['success']}")

if __name__ == "__main__":
    asyncio.run(main())