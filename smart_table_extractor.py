#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能表格提取器 - 从渲染后的页面直接提取数据
基于media下载项目的核心思路：获取渲染后的数据而非原始数据
"""

import json
import time
import pandas as pd
from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartTableExtractor:
    """智能表格提取器 - 绕过加密直接获取渲染数据"""
    
    def __init__(self):
        self.cookie_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
        
    def extract_rendered_table(self, doc_id: str):
        """从渲染后的页面提取表格数据"""
        
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
        
        with sync_playwright() as p:
            # 使用stealth配置
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            # 添加反检测脚本
            context.add_init_script("""
                // 移除webdriver痕迹
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
                
                // 伪装chrome对象
                window.chrome = {
                    runtime: {}
                };
                
                // 伪装权限查询
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            # 添加cookies
            context.add_cookies(cookies)
            
            page = context.new_page()
            
            try:
                doc_url = f"https://docs.qq.com/sheet/{doc_id}"
                logger.info(f"访问文档: {doc_url}")
                
                # 访问页面
                page.goto(doc_url, wait_until='domcontentloaded', timeout=30000)
                
                # 等待表格渲染
                logger.info("等待表格渲染...")
                time.sleep(5)
                
                # 方法1: 直接从DOM提取表格数据
                logger.info("尝试方法1: DOM提取")
                table_data = page.evaluate("""
                    () => {
                        // 查找所有可能的表格容器
                        const selectors = [
                            'table',
                            '[class*="table"]',
                            '[class*="grid"]',
                            '[class*="sheet"]',
                            '[role="table"]',
                            '[role="grid"]',
                            '.alloy-editor',
                            '.excel-container'
                        ];
                        
                        let data = [];
                        
                        for (const selector of selectors) {
                            const elements = document.querySelectorAll(selector);
                            
                            for (const element of elements) {
                                // 尝试提取表格数据
                                const rows = element.querySelectorAll('tr, [role="row"]');
                                
                                if (rows.length > 0) {
                                    const tableData = [];
                                    
                                    for (const row of rows) {
                                        const cells = row.querySelectorAll('td, th, [role="cell"], [role="gridcell"]');
                                        const rowData = [];
                                        
                                        for (const cell of cells) {
                                            // 获取单元格文本
                                            let text = cell.textContent || cell.innerText || '';
                                            text = text.trim();
                                            rowData.push(text);
                                        }
                                        
                                        if (rowData.length > 0) {
                                            tableData.push(rowData);
                                        }
                                    }
                                    
                                    if (tableData.length > 0) {
                                        data.push({
                                            selector: selector,
                                            rows: tableData.length,
                                            cols: tableData[0].length,
                                            data: tableData
                                        });
                                    }
                                }
                            }
                        }
                        
                        return data;
                    }
                """)
                
                if table_data and len(table_data) > 0:
                    logger.info(f"✅ DOM提取成功！找到{len(table_data)}个表格")
                    return table_data
                
                # 方法2: 使用Canvas渲染捕获
                logger.info("尝试方法2: Canvas捕获")
                canvas_data = page.evaluate("""
                    () => {
                        const canvases = document.querySelectorAll('canvas');
                        const data = [];
                        
                        for (const canvas of canvases) {
                            // 检查是否是表格渲染canvas
                            if (canvas.width > 100 && canvas.height > 100) {
                                data.push({
                                    width: canvas.width,
                                    height: canvas.height,
                                    hasContent: true
                                });
                            }
                        }
                        
                        return data;
                    }
                """)
                
                if canvas_data and len(canvas_data) > 0:
                    logger.info(f"发现{len(canvas_data)}个Canvas元素（可能使用Canvas渲染）")
                    
                # 方法3: 拦截虚拟滚动数据
                logger.info("尝试方法3: 虚拟滚动数据提取")
                virtual_data = page.evaluate("""
                    () => {
                        // 查找虚拟滚动容器
                        const virtualContainers = document.querySelectorAll('[class*="virtual"], [class*="viewport"]');
                        const data = [];
                        
                        for (const container of virtualContainers) {
                            // 获取所有可见的单元格
                            const cells = container.querySelectorAll('[class*="cell"]');
                            
                            if (cells.length > 0) {
                                const cellData = [];
                                
                                for (const cell of cells) {
                                    cellData.push({
                                        text: cell.textContent.trim(),
                                        position: cell.getBoundingClientRect()
                                    });
                                }
                                
                                data.push({
                                    cellCount: cells.length,
                                    cells: cellData.slice(0, 100)  // 限制数量
                                });
                            }
                        }
                        
                        return data;
                    }
                """)
                
                if virtual_data and len(virtual_data) > 0:
                    logger.info(f"虚拟滚动数据: {virtual_data[0].get('cellCount', 0)}个单元格")
                    
                # 方法4: 获取页面文本快照
                logger.info("尝试方法4: 页面文本快照")
                text_content = page.evaluate("""
                    () => {
                        // 获取主要内容区域的文本
                        const mainContent = document.querySelector('main, [role="main"], .main-content, #content');
                        
                        if (mainContent) {
                            return mainContent.innerText;
                        }
                        
                        return document.body.innerText;
                    }
                """)
                
                if text_content:
                    lines = text_content.split('\n')
                    logger.info(f"获取到{len(lines)}行文本")
                    
                    # 尝试解析为表格格式
                    table_lines = []
                    for line in lines:
                        if '\t' in line or '|' in line:
                            table_lines.append(line)
                    
                    if table_lines:
                        logger.info(f"发现{len(table_lines)}行可能的表格数据")
                        return {'text_table': table_lines}
                
                # 如果都失败了，保存截图用于分析
                screenshot_path = f"/root/projects/tencent-doc-manager/debug_screenshot_{int(time.time())}.png"
                page.screenshot(path=screenshot_path)
                logger.info(f"截图已保存: {screenshot_path}")
                
                return None
                
            except Exception as e:
                logger.error(f"提取失败: {e}")
                return None
                
            finally:
                browser.close()
    
    def save_to_excel(self, data, output_file):
        """将提取的数据保存为Excel"""
        
        if not data:
            logger.warning("没有数据可保存")
            return
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for i, table in enumerate(data):
                if isinstance(table, dict) and 'data' in table:
                    df = pd.DataFrame(table['data'])
                    sheet_name = f"Sheet{i+1}"
                    df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                    logger.info(f"保存表格到 {sheet_name}: {len(df)} 行")
        
        logger.info(f"✅ Excel文件已保存: {output_file}")

def main():
    """主函数"""
    extractor = SmartTableExtractor()
    
    # 测试文档
    test_doc_id = "DWEVjZndkR2xVSWJN"
    
    logger.info("=" * 60)
    logger.info("智能表格提取测试")
    logger.info("=" * 60)
    
    # 提取数据
    data = extractor.extract_rendered_table(test_doc_id)
    
    if data:
        # 保存结果
        json_file = f"/root/projects/tencent-doc-manager/extracted_data_{int(time.time())}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"数据已保存到: {json_file}")
        
        # 尝试转换为Excel
        if isinstance(data, list) and len(data) > 0:
            excel_file = f"/root/projects/tencent-doc-manager/extracted_table_{int(time.time())}.xlsx"
            extractor.save_to_excel(data, excel_file)
    else:
        logger.warning("未能提取到数据")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()