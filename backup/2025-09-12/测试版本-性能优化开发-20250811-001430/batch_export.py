#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档批量导出脚本 - 简单实用版
基于现有工具的批量处理包装
"""

import subprocess
import time
import sys
import os
from pathlib import Path
import argparse
import json
from datetime import datetime


class BatchExporter:
    """批量导出管理器"""
    
    def __init__(self, cookies=None, retry_count=3, delay=2):
        self.cookies = cookies
        self.retry_count = retry_count
        self.delay = delay
        self.results = []
        
    def export_single(self, url, output_dir="exports", prefer_playwright=True):
        """导出单个文档，自动降级策略"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 确保输出目录存在
        Path(output_dir).mkdir(exist_ok=True)
        
        # 提取文档ID作为文件名
        import re
        doc_id_match = re.search(r'/(?:sheet|doc)/([A-Za-z0-9]+)', url)
        doc_id = doc_id_match.group(1) if doc_id_match else f"doc_{timestamp}"
        
        strategies = [
            ('Playwright', 'tencent_csv_playwright.py'),
            ('API', 'simple_csv_exporter.py')
        ] if prefer_playwright else [
            ('API', 'simple_csv_exporter.py'),
            ('Playwright', 'tencent_csv_playwright.py')
        ]
        
        for attempt in range(self.retry_count):
            for strategy_name, script_name in strategies:
                try:
                    print(f"[{doc_id}] 尝试 {strategy_name} 方法 (第{attempt+1}次)")
                    
                    cmd = [sys.executable, script_name, url]
                    if self.cookies:
                        cmd.extend(['-c', self.cookies])
                    
                    # 设置输出文件
                    output_file = Path(output_dir) / f"{doc_id}_{strategy_name.lower()}_{timestamp}.csv"
                    cmd.extend(['-o', str(output_file)])
                    
                    # 运行命令
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0 and output_file.exists():
                        print(f"[SUCCESS] {doc_id} 导出成功: {output_file}")
                        self.results.append({
                            'url': url,
                            'doc_id': doc_id,
                            'output_file': str(output_file),
                            'method': strategy_name,
                            'timestamp': timestamp,
                            'status': 'success'
                        })
                        return str(output_file)
                    else:
                        print(f"[FAILED] {strategy_name} 失败: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    print(f"[TIMEOUT] {strategy_name} 超时")
                except Exception as e:
                    print(f"[ERROR] {strategy_name} 出错: {e}")
                
                # 策略间等待
                time.sleep(self.delay)
            
            # 重试间等待
            if attempt < self.retry_count - 1:
                print(f"[{doc_id}] 所有方法失败，{self.delay * 2}秒后重试...")
                time.sleep(self.delay * 2)
        
        # 记录失败
        self.results.append({
            'url': url,
            'doc_id': doc_id,
            'output_file': None,
            'method': 'failed',
            'timestamp': timestamp,
            'status': 'failed'
        })
        print(f"[FAILED] {doc_id} 所有尝试均失败")
        return None
    
    def export_batch(self, urls, output_dir="exports"):
        """批量导出文档列表"""
        print(f"开始批量导出 {len(urls)} 个文档...")
        
        success_count = 0
        for i, url in enumerate(urls, 1):
            print(f"\n=== 处理第 {i}/{len(urls)} 个文档 ===")
            result = self.export_single(url, output_dir)
            if result:
                success_count += 1
            
            # 避免请求过快
            if i < len(urls):
                time.sleep(self.delay)
        
        # 生成结果报告
        self.save_report(output_dir)
        print(f"\n批量导出完成: {success_count}/{len(urls)} 成功")
        return self.results
    
    def save_report(self, output_dir):
        """保存导出报告"""
        report_file = Path(output_dir) / f"export_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"导出报告已保存: {report_file}")


def main():
    parser = argparse.ArgumentParser(description='腾讯文档批量导出工具')
    parser.add_argument('input', help='文档URL或包含URLs的文件路径')
    parser.add_argument('-o', '--output', default='exports', help='输出目录')
    parser.add_argument('-c', '--cookies', help='登录Cookie')
    parser.add_argument('-r', '--retry', type=int, default=3, help='重试次数')
    parser.add_argument('-d', '--delay', type=int, default=2, help='请求间延迟(秒)')
    parser.add_argument('--api-first', action='store_true', help='优先使用API方法')
    
    args = parser.parse_args()
    
    # 解析输入
    if args.input.startswith('http'):
        # 单个URL
        urls = [args.input]
    else:
        # 从文件读取URLs
        with open(args.input, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and line.startswith('http')]
    
    if not urls:
        print("错误: 没有找到有效的URL")
        return
    
    # 创建批量导出器
    exporter = BatchExporter(
        cookies=args.cookies,
        retry_count=args.retry,
        delay=args.delay
    )
    
    # 执行导出
    results = exporter.export_batch(urls, args.output)
    
    # 显示最终统计
    success = sum(1 for r in results if r['status'] == 'success')
    failed = len(results) - success
    print(f"\n最终统计: 成功 {success} 个, 失败 {failed} 个")


if __name__ == "__main__":
    main()