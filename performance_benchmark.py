#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试
对比Playwright vs 直接CDP的性能差异
"""

import asyncio
import time
import statistics
import json
from typing import List, Dict
import websockets
from playwright.sync_api import sync_playwright
import aiohttp

class PerformanceBenchmark:
    """
    性能基准测试工具
    """
    
    def __init__(self):
        self.results = {
            'playwright': [],
            'cdp_direct': []
        }
        
    async def benchmark_playwright(self, iterations: int = 10) -> Dict:
        """测试Playwright性能"""
        print("\n测试Playwright性能...")
        times = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            for i in range(iterations):
                start = time.time()
                
                # 创建页面
                page = browser.new_page()
                
                # 导航
                page.goto('https://example.com')
                
                # 执行JavaScript
                result = page.evaluate('document.title')
                
                # 截图
                page.screenshot()
                
                # 关闭页面
                page.close()
                
                elapsed = time.time() - start
                times.append(elapsed)
                print(f"  迭代 {i+1}: {elapsed:.3f}秒")
            
            browser.close()
        
        return {
            'method': 'Playwright',
            'iterations': iterations,
            'times': times,
            'average': statistics.mean(times),
            'median': statistics.median(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'min': min(times),
            'max': max(times)
        }
        
    async def benchmark_cdp_direct(self, iterations: int = 10) -> Dict:
        """测试直接CDP性能"""
        print("\n测试CDP直连性能...")
        times = []
        
        # 连接到Chrome
        async with aiohttp.ClientSession() as session:
            # 获取调试端口信息
            async with session.get('http://localhost:9222/json/version') as resp:
                if resp.status != 200:
                    print("Chrome调试端口未开启")
                    return {}
                    
            for i in range(iterations):
                start = time.time()
                
                # 创建新标签页
                async with session.put('http://localhost:9222/json/new') as resp:
                    target = await resp.json()
                    ws_url = target['webSocketDebuggerUrl']
                
                # 连接WebSocket
                async with websockets.connect(ws_url) as ws:
                    # 发送导航命令
                    await ws.send(json.dumps({
                        'id': 1,
                        'method': 'Page.enable',
                        'params': {}
                    }))
                    
                    await ws.send(json.dumps({
                        'id': 2,
                        'method': 'Page.navigate',
                        'params': {'url': 'https://example.com'}
                    }))
                    
                    # 等待响应
                    while True:
                        response = await ws.recv()
                        data = json.loads(response)
                        if data.get('id') == 2:
                            break
                    
                    # 执行JavaScript
                    await ws.send(json.dumps({
                        'id': 3,
                        'method': 'Runtime.evaluate',
                        'params': {
                            'expression': 'document.title',
                            'returnByValue': True
                        }
                    }))
                    
                    # 截图
                    await ws.send(json.dumps({
                        'id': 4,
                        'method': 'Page.captureScreenshot',
                        'params': {}
                    }))
                
                # 关闭标签页
                async with session.delete(f'http://localhost:9222/json/close/{target["id"]}'):
                    pass
                    
                elapsed = time.time() - start
                times.append(elapsed)
                print(f"  迭代 {i+1}: {elapsed:.3f}秒")
        
        return {
            'method': 'CDP Direct',
            'iterations': iterations,
            'times': times,
            'average': statistics.mean(times),
            'median': statistics.median(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'min': min(times),
            'max': max(times)
        }
        
    def compare_results(self, results: List[Dict]) -> None:
        """对比结果"""
        print("\n" + "="*60)
        print("性能对比结果")
        print("="*60)
        
        for result in results:
            if not result:
                continue
                
            print(f"\n{result['method']}:")
            print(f"  平均耗时: {result['average']:.3f}秒")
            print(f"  中位数: {result['median']:.3f}秒")
            print(f"  标准差: {result['stdev']:.3f}秒")
            print(f"  最小值: {result['min']:.3f}秒")
            print(f"  最大值: {result['max']:.3f}秒")
        
        if len(results) == 2 and all(results):
            playwright_avg = results[0]['average']
            cdp_avg = results[1]['average']
            
            if cdp_avg < playwright_avg:
                improvement = ((playwright_avg - cdp_avg) / playwright_avg) * 100
                print(f"\n🚀 CDP直连比Playwright快 {improvement:.1f}%")
            else:
                slowdown = ((cdp_avg - playwright_avg) / cdp_avg) * 100
                print(f"\n⚠️ CDP直连比Playwright慢 {slowdown:.1f}%")
                
    async def benchmark_specific_operations(self):
        """测试特定操作的性能差异"""
        print("\n" + "="*60)
        print("特定操作性能测试")
        print("="*60)
        
        operations = [
            {
                'name': '页面导航',
                'playwright': self._playwright_navigate,
                'cdp': self._cdp_navigate
            },
            {
                'name': '元素查找',
                'playwright': self._playwright_find_element,
                'cdp': self._cdp_find_element
            },
            {
                'name': 'JavaScript执行',
                'playwright': self._playwright_execute_js,
                'cdp': self._cdp_execute_js
            }
        ]
        
        for op in operations:
            print(f"\n测试: {op['name']}")
            
            # Playwright
            start = time.time()
            await op['playwright']()
            playwright_time = time.time() - start
            
            # CDP
            start = time.time()
            await op['cdp']()
            cdp_time = time.time() - start
            
            print(f"  Playwright: {playwright_time:.3f}秒")
            print(f"  CDP直连: {cdp_time:.3f}秒")
            
            if cdp_time < playwright_time:
                improvement = ((playwright_time - cdp_time) / playwright_time) * 100
                print(f"  ✅ CDP快 {improvement:.1f}%")
            else:
                print(f"  ❌ Playwright更快")
                
    async def _playwright_navigate(self):
        """Playwright导航测试"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://docs.qq.com')
            browser.close()
            
    async def _cdp_navigate(self):
        """CDP导航测试"""
        async with aiohttp.ClientSession() as session:
            async with session.put('http://localhost:9222/json/new') as resp:
                target = await resp.json()
                
            async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
                await ws.send(json.dumps({
                    'id': 1,
                    'method': 'Page.navigate',
                    'params': {'url': 'https://docs.qq.com'}
                }))
                await ws.recv()
                
            async with session.delete(f'http://localhost:9222/json/close/{target["id"]}'):
                pass
                
    async def _playwright_find_element(self):
        """Playwright元素查找测试"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://example.com')
            
            # 查找100次
            for _ in range(100):
                page.locator('h1').is_visible()
                
            browser.close()
            
    async def _cdp_find_element(self):
        """CDP元素查找测试"""
        async with aiohttp.ClientSession() as session:
            async with session.put('http://localhost:9222/json/new') as resp:
                target = await resp.json()
                
            async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
                await ws.send(json.dumps({
                    'id': 1,
                    'method': 'Page.navigate',
                    'params': {'url': 'https://example.com'}
                }))
                
                # 查找100次
                for i in range(100):
                    await ws.send(json.dumps({
                        'id': i + 2,
                        'method': 'Runtime.evaluate',
                        'params': {
                            'expression': 'document.querySelector("h1")',
                            'returnByValue': False
                        }
                    }))
                    
            async with session.delete(f'http://localhost:9222/json/close/{target["id"]}'):
                pass
                
    async def _playwright_execute_js(self):
        """Playwright JavaScript执行测试"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 执行1000次
            for _ in range(1000):
                page.evaluate('1 + 1')
                
            browser.close()
            
    async def _cdp_execute_js(self):
        """CDP JavaScript执行测试"""
        async with aiohttp.ClientSession() as session:
            async with session.put('http://localhost:9222/json/new') as resp:
                target = await resp.json()
                
            async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
                # 执行1000次
                for i in range(1000):
                    await ws.send(json.dumps({
                        'id': i + 1,
                        'method': 'Runtime.evaluate',
                        'params': {
                            'expression': '1 + 1',
                            'returnByValue': True
                        }
                    }))
                    
            async with session.delete(f'http://localhost:9222/json/close/{target["id"]}'):
                pass

async def main():
    """主函数"""
    print("="*60)
    print("Playwright vs CDP直连 性能基准测试")
    print("基于Browser-Use的实践经验")
    print("="*60)
    
    print("\n⚠️ 请先启动Chrome调试模式:")
    print("chrome --remote-debugging-port=9222 --headless")
    
    input("\n按Enter开始测试...")
    
    benchmark = PerformanceBenchmark()
    
    # 基础性能测试
    print("\n" + "="*60)
    print("基础性能测试（10次迭代）")
    print("="*60)
    
    results = []
    
    # Playwright测试
    playwright_result = await benchmark.benchmark_playwright(10)
    results.append(playwright_result)
    
    # CDP测试
    cdp_result = await benchmark.benchmark_cdp_direct(10)
    results.append(cdp_result)
    
    # 对比结果
    benchmark.compare_results(results)
    
    # 特定操作测试
    await benchmark.benchmark_specific_operations()
    
    # 结论
    print("\n" + "="*60)
    print("测试结论")
    print("="*60)
    print("\n根据Browser-Use的实践:")
    print("1. CDP直连在大量DOM操作时性能提升显著")
    print("2. 减少了Node.js中间层的网络延迟")
    print("3. 支持更细粒度的浏览器控制")
    print("4. 但增加了代码复杂度")
    print("\n建议:")
    print("- 简单任务: 使用Playwright（开发效率高）")
    print("- 性能敏感: 使用CDP直连（速度快）")
    print("- 生产环境: 混合使用（按需优化）")

if __name__ == "__main__":
    asyncio.run(main())