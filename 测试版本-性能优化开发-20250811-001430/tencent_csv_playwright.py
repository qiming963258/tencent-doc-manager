#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档CSV导出工具 - Playwright版本
使用浏览器自动化获取真实的表格数据
"""

import asyncio
import csv
import argparse
from playwright.async_api import async_playwright
import re


class TencentDocPlaywrightExporter:
    """使用Playwright的腾讯文档CSV导出工具"""
    
    def __init__(self):
        self.browser = None
        self.page = None
    
    async def start_browser(self, headless=True):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.page = await self.browser.new_page()
        
        # 设置用户代理
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    async def login_with_cookies(self, cookies):
        """使用cookies登录"""
        if cookies:
            cookie_list = []
            for cookie_str in cookies.split(';'):
                if '=' in cookie_str:
                    name, value = cookie_str.strip().split('=', 1)
                    cookie_list.append({
                        'name': name,
                        'value': value,
                        'domain': '.qq.com',
                        'path': '/'
                    })
            await self.page.context.add_cookies(cookie_list)
    
    async def extract_table_data(self, doc_url):
        """提取表格数据"""
        print(f"正在访问文档: {doc_url}")
        
        try:
            # 访问页面，等待网络空闲
            await self.page.goto(doc_url, wait_until='networkidle', timeout=90000)
            print("页面基本加载完成")
            
            # 等待关键元素出现
            try:
                # 等待表格容器或加载完成的标志
                await self.page.wait_for_selector('.dui-table, [class*="table"], [class*="grid"], .edit-area, #app', timeout=30000)
                print("检测到表格容器")
            except:
                print("未检测到明确的表格容器，继续尝试...")
            
            # 长时间等待确保所有内容渲染完成
            await self.page.wait_for_timeout(8000)
            print("等待渲染完成")
            
            # 尝试滚动页面确保懒加载的内容都显示出来
            await self.page.evaluate('''
                window.scrollTo(0, document.body.scrollHeight);
                setTimeout(() => window.scrollTo(0, 0), 1000);
            ''')
            await self.page.wait_for_timeout(3000)
            print("完成页面滚动")
            
            table_data = []
            
            # 方法1: 尝试寻找腾讯文档特定的表格结构
            print("方法1: 寻找腾讯文档表格结构...")
            
            # 腾讯文档可能的选择器
            selectors_to_try = [
                '.dui-table-cell',
                '[class*="cell"]',
                '[class*="table-cell"]', 
                '[data-sheet-cell]',
                '.edit-area [class*="cell"]',
                '.spreadsheet [class*="cell"]',
                '[class*="grid-cell"]',
                '.table-container td',
                '.sheet-container [class*="cell"]'
            ]
            
            for selector in selectors_to_try:
                cells = await self.page.query_selector_all(selector)
                if cells:
                    print(f"使用选择器 {selector} 找到 {len(cells)} 个单元格")
                    cell_texts = []
                    for cell in cells[:100]:  # 限制数量避免过多
                        text = await cell.text_content()
                        if text and text.strip():
                            cell_texts.append(text.strip())
                    
                    if cell_texts and not all('script' in text.lower() or 'function' in text.lower() for text in cell_texts):
                        table_data = cell_texts
                        break
            
            # 方法2: 使用剪贴板方法（改进版）
            if not table_data:
                print("方法2: 尝试剪贴板方法...")
                
                # 先点击表格区域确保焦点正确
                try:
                    table_area = await self.page.query_selector('.edit-area, [class*="table"], .sheet-container, #app')
                    if table_area:
                        await table_area.click()
                        await self.page.wait_for_timeout(1000)
                except:
                    pass
                
                # 全选并复制
                await self.page.keyboard.press('Control+A')
                await self.page.wait_for_timeout(2000)
                await self.page.keyboard.press('Control+C')
                await self.page.wait_for_timeout(2000)
                
                # 获取剪贴板内容
                clipboard_text = await self.page.evaluate('''
                    async () => {
                        try {
                            const text = await navigator.clipboard.readText();
                            return text;
                        } catch (e) {
                            console.error('剪贴板访问失败:', e);
                            return null;
                        }
                    }
                ''')
                
                if clipboard_text and len(clipboard_text.strip()) > 100:  # 确保不是空内容
                    print(f"获取到剪贴板内容，长度: {len(clipboard_text)}")
                    # 检查是否是表格数据而不是JavaScript代码
                    if not ('function' in clipboard_text.lower() and 'var' in clipboard_text.lower()):
                        lines = clipboard_text.strip().split('\n')
                        # 过滤掉明显的非表格行
                        filtered_lines = []
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('//') and not line.startswith('/*') and 'function' not in line.lower():
                                filtered_lines.append(line.split('\t'))
                        
                        if filtered_lines:
                            table_data = filtered_lines
            
            # 方法3: 尝试寻找导出按钮并使用
            if not table_data:
                print("方法3: 寻找导出功能...")
                try:
                    # 查找可能的导出或下载按钮
                    export_selectors = [
                        '[class*="export"]',
                        '[class*="download"]', 
                        'button:has-text("导出")',
                        'button:has-text("下载")',
                        '.toolbar [class*="more"]'
                    ]
                    
                    for selector in export_selectors:
                        export_btn = await self.page.query_selector(selector)
                        if export_btn:
                            print(f"找到导出按钮: {selector}")
                            await export_btn.click()
                            await self.page.wait_for_timeout(3000)
                            # 这里需要处理导出对话框...
                            break
                except Exception as e:
                    print(f"导出按钮方法失败: {e}")
            
            # 方法4: 直接从页面提取所有可见文本并智能解析
            if not table_data:
                print("方法4: 智能文本提取...")
                
                # 移除脚本和样式标签
                await self.page.evaluate('''
                    document.querySelectorAll('script, style, noscript').forEach(el => el.remove());
                ''')
                
                page_text = await self.page.text_content('body')
                if page_text:
                    lines = page_text.split('\n')
                    # 过滤和清理
                    cleaned_lines = []
                    for line in lines:
                        line = line.strip()
                        # 跳过明显的UI文本和代码
                        if (line and 
                            len(line) < 200 and  # 避免长代码行
                            not line.startswith('function') and
                            not line.startswith('var ') and
                            not line.startswith('//') and
                            not line.lower().startswith('<!doctype') and
                            '腾讯文档' not in line and
                            'loading' not in line.lower()):
                            cleaned_lines.append([line])
                    
                    if cleaned_lines and len(cleaned_lines) > 5:  # 确保有足够数据
                        table_data = cleaned_lines[:1000]  # 限制行数
            
            # 数据验证和清理
            if table_data:
                print(f"提取到 {len(table_data)} 行数据")
                # 显示前几行以供验证
                print("数据预览:")
                for i, row in enumerate(table_data[:5]):
                    if isinstance(row, list):
                        print(f"行 {i+1}: {row[:3]}...")  # 只显示前3列
                    else:
                        print(f"行 {i+1}: {str(row)[:50]}...")
                        
                return table_data
            else:
                print("未能提取到有效的表格数据")
                return []
            
        except Exception as e:
            print(f"提取数据时出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def save_to_csv(self, data, output_file):
        """保存数据到CSV文件"""
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                if isinstance(data[0], list):
                    # 如果数据已经是二维数组
                    for row in data:
                        writer.writerow(row)
                else:
                    # 如果是一维数组，每个元素作为一行
                    for item in data:
                        writer.writerow([item])
            
            print(f"[SUCCESS] 数据已保存到: {output_file}")
            return True
        except Exception as e:
            print(f"[ERROR] 保存CSV失败: {e}")
            return False
    
    async def export_to_csv(self, doc_url, output_path=None, cookies=None, headless=True):
        """导出文档为CSV"""
        try:
            await self.start_browser(headless=headless)
            
            if cookies:
                await self.login_with_cookies(cookies)
            
            # 生成输出文件名
            if not output_path:
                doc_id = re.search(r'/(?:sheet|doc)/([A-Za-z0-9]+)', doc_url)
                if doc_id:
                    output_path = f"tencent_doc_{doc_id.group(1)}_playwright.csv"
                else:
                    output_path = "tencent_doc_export.csv"
            
            # 提取数据
            data = await self.extract_table_data(doc_url)
            
            if data:
                success = await self.save_to_csv(data, output_path)
                return output_path if success else None
            else:
                print("[ERROR] 未能提取到表格数据")
                return None
                
        except Exception as e:
            print(f"[ERROR] 导出失败: {e}")
            return None
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()


async def main():
    parser = argparse.ArgumentParser(description='腾讯文档CSV导出工具 (Playwright版本)')
    parser.add_argument('url', help='腾讯文档URL')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-c', '--cookies', help='登录Cookie')
    parser.add_argument('--visible', action='store_true', help='显示浏览器窗口')
    
    args = parser.parse_args()
    
    exporter = TencentDocPlaywrightExporter()
    result = await exporter.export_to_csv(
        args.url, 
        args.output, 
        args.cookies,
        headless=not args.visible
    )
    
    if result:
        print(f"[SUCCESS] 导出完成: {result}")
    else:
        print("[ERROR] 导出失败")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序出错: {e}")