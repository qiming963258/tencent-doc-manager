#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档浏览器自动化 - 真实现场测试
使用实际的业务文档进行全面测试
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
import time

# 添加成功方案的路径
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

class RealFieldTester:
    """真实现场测试器"""
    
    def __init__(self):
        self.test_results = []
        self.success_count = 0
        self.total_tests = 0
        
    def load_cookies(self):
        """加载Cookie"""
        cookie_file = "/root/projects/tencent-doc-manager/config/cookies_new.json"
        with open(cookie_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("current_cookies", "")
    
    async def test_document(self, doc_info, exporter_class):
        """测试单个文档"""
        doc_id = doc_info['id']
        doc_name = doc_info['name']
        export_format = doc_info.get('format', 'csv')
        
        print(f"\n{'='*80}")
        print(f"📄 现场测试文档: {doc_name}")
        print(f"🆔 文档ID: {doc_id}")
        print(f"📊 导出格式: {export_format}")
        print(f"{'='*80}")
        
        test_result = {
            'doc_id': doc_id,
            'doc_name': doc_name,
            'format': export_format,
            'start_time': datetime.now(),
            'success': False,
            'file_path': None,
            'file_size': 0,
            'content_preview': [],
            'error': None,
            'duration': 0
        }
        
        try:
            # 创建下载目录
            download_dir = f"/root/projects/tencent-doc-manager/real_test_results/field_test_{datetime.now().strftime('%m%d_%H%M%S')}"
            os.makedirs(download_dir, exist_ok=True)
            
            # 创建导出器
            exporter = exporter_class(download_dir=download_dir)
            
            print("🚀 启动浏览器...")
            start_time = time.time()
            await exporter.start_browser(headless=True)
            
            # 加载Cookie
            print("🔐 加载认证信息...")
            cookies = self.load_cookies()
            await exporter.login_with_cookies(cookies)
            
            # 构建文档URL
            doc_url = f"https://docs.qq.com/sheet/{doc_id}"
            print(f"🌐 访问文档: {doc_url}")
            
            # 执行下载
            print(f"📥 开始下载 ({export_format} 格式)...")
            result = await exporter.auto_export_document(doc_url, export_format=export_format)
            
            end_time = time.time()
            test_result['duration'] = round(end_time - start_time, 2)
            
            if result and len(result) > 0:
                file_path = result[0]
                test_result['success'] = True
                test_result['file_path'] = file_path
                
                # 检查文件
                if os.path.exists(file_path):
                    test_result['file_size'] = os.path.getsize(file_path)
                    
                    # 读取内容预览
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for i in range(5):  # 读取前5行
                                line = f.readline().strip()
                                if line:
                                    test_result['content_preview'].append(line[:100])  # 限制每行100字符
                    except Exception as e:
                        print(f"⚠️ 内容预览失败: {e}")
                
                print(f"✅ 下载成功!")
                print(f"📁 文件路径: {file_path}")
                print(f"📏 文件大小: {test_result['file_size']} bytes")
                print(f"⏱️ 用时: {test_result['duration']} 秒")
                
                # 显示内容预览
                if test_result['content_preview']:
                    print("📝 内容预览:")
                    for i, line in enumerate(test_result['content_preview'], 1):
                        if line:
                            print(f"  {i}. {line}")
                
                self.success_count += 1
            else:
                print("❌ 下载失败")
                test_result['error'] = "下载返回空结果"
            
            # 清理资源
            if exporter.browser:
                await exporter.browser.close()
            if exporter.playwright:
                await exporter.playwright.stop()
                
        except Exception as e:
            end_time = time.time()
            test_result['duration'] = round(end_time - start_time, 2)
            test_result['error'] = str(e)
            print(f"❌ 测试失败: {e}")
            
            # 确保清理
            try:
                if 'exporter' in locals():
                    if hasattr(exporter, 'browser') and exporter.browser:
                        await exporter.browser.close()
                    if hasattr(exporter, 'playwright') and exporter.playwright:
                        await exporter.playwright.stop()
            except:
                pass
        
        test_result['end_time'] = datetime.now()
        self.test_results.append(test_result)
        self.total_tests += 1
        
        return test_result
    
    async def run_field_tests(self):
        """执行现场测试"""
        print("🎯 腾讯文档浏览器自动化 - 真实现场测试")
        print("="*80)
        print(f"⏰ 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # 导入成功的自动化工具
        try:
            from tencent_export_automation import TencentDocAutoExporter
            print("✅ 成功导入自动化工具")
        except Exception as e:
            print(f"❌ 无法导入自动化工具: {e}")
            return
        
        # 定义真实测试文档
        test_documents = [
            {
                'id': 'DWEVjZndkR2xVSWJN',
                'name': '测试版本-小红书部门',
                'format': 'csv'
            },
            {
                'id': 'DWEVjZndkR2xVSWJN',
                'name': '测试版本-小红书部门',
                'format': 'excel'
            },
            {
                'id': 'DRFppYm15RGZ2WExN',
                'name': '测试版本-回国销售计划表',
                'format': 'csv'
            },
            {
                'id': 'DRHZrS1hOS3pwRGZB',
                'name': '测试版本-出国销售计划表',
                'format': 'csv'
            }
        ]
        
        # 执行每个测试
        for i, doc_info in enumerate(test_documents, 1):
            print(f"\n🔄 测试 {i}/{len(test_documents)}")
            
            await self.test_document(doc_info, TencentDocAutoExporter)
            
            # 测试间隔，避免过于频繁
            if i < len(test_documents):
                print("⏳ 等待5秒后进行下一个测试...")
                await asyncio.sleep(5)
        
        # 生成测试报告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成测试报告"""
        print(f"\n{'='*80}")
        print("📊 真实现场测试报告")
        print(f"{'='*80}")
        
        print(f"📈 总体统计:")
        print(f"  测试总数: {self.total_tests}")
        print(f"  成功数量: {self.success_count}")
        print(f"  失败数量: {self.total_tests - self.success_count}")
        print(f"  成功率: {(self.success_count/self.total_tests*100):.1f}%" if self.total_tests > 0 else "0%")
        
        print(f"\n📋 详细结果:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ 成功" if result['success'] else "❌ 失败"
            print(f"  {i}. {result['doc_name']} ({result['format']}) - {status}")
            if result['success']:
                print(f"     📁 大小: {result['file_size']} bytes, ⏱️ 用时: {result['duration']}s")
                if result['content_preview']:
                    print(f"     📝 首行: {result['content_preview'][0][:50]}...")
            else:
                print(f"     ❌ 错误: {result['error']}")
        
        # 保存详细报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"/root/projects/tencent-doc-manager/real_test_results/field_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_summary': {
                    'total_tests': self.total_tests,
                    'successful_tests': self.success_count,
                    'failed_tests': self.total_tests - self.success_count,
                    'success_rate': round(self.success_count/self.total_tests*100, 1) if self.total_tests > 0 else 0,
                    'test_time': datetime.now().isoformat()
                },
                'test_results': [
                    {
                        **result,
                        'start_time': result['start_time'].isoformat(),
                        'end_time': result['end_time'].isoformat()
                    }
                    for result in self.test_results
                ]
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 详细报告已保存: {report_file}")
        
        # 最终结论
        if self.success_count == self.total_tests:
            print(f"\n🎉 现场测试完全成功！")
            print("✅ 浏览器自动化方案经过真实环境验证，可以投入实际使用")
        elif self.success_count > 0:
            print(f"\n⚠️ 现场测试部分成功")
            print(f"✅ {self.success_count}/{self.total_tests} 个测试通过，需要进一步优化")
        else:
            print(f"\n❌ 现场测试失败")
            print("🔧 需要检查环境配置和文档权限")

async def main():
    """主函数"""
    tester = RealFieldTester()
    await tester.run_field_tests()

if __name__ == "__main__":
    asyncio.run(main())