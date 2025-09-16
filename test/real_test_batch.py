#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实测试：批量下载和解密三份测试文档
验证完整的自动化流程
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
import subprocess
import os

class RealTestManager:
    """真实测试管理器"""
    
    def __init__(self):
        self.cookie_file = '/root/projects/tencent-doc-manager/config/cookies_new.json'
        self.output_dir = Path('/root/projects/tencent-doc-manager/real_test_results')
        self.output_dir.mkdir(exist_ok=True)
        
        # 测试文档列表
        self.test_documents = [
            {
                'name': '测试版本-小红书部门',
                'id': 'DWEVjZndkR2xVSWJN',
                'url': 'https://docs.qq.com/sheet/DWEVjZndkR2xVSWJN',
                'description': '小红书部门管理表'
            },
            {
                'name': '测试版本-回国销售计划表',
                'id': 'DRFppYm15RGZ2WExN', 
                'url': 'https://docs.qq.com/sheet/DRFppYm15RGZ2WExN',
                'description': '回国销售业务计划'
            },
            {
                'name': '测试版本-出国销售计划表',
                'id': 'DRHZrS1hOS3pwRGZB',
                'url': 'https://docs.qq.com/sheet/DRHZrS1hOS3pwRGZB', 
                'description': '出国销售业务计划'
            }
        ]
        
        self.load_cookies()
        
    def load_cookies(self):
        """加载认证Cookie"""
        with open(self.cookie_file, 'r') as f:
            cookie_data = json.load(f)
        self.cookie_str = cookie_data['current_cookies']
        
        print(f"✅ Cookie加载成功 ({len(self.cookie_str)} 字符)")
        
    def download_document(self, doc_info):
        """下载单个文档"""
        print(f"\n{'='*60}")
        print(f"下载文档: {doc_info['name']}")
        print(f"ID: {doc_info['id']}")
        print(f"{'='*60}")
        
        results = {
            'doc_info': doc_info,
            'download_success': False,
            'ejs_file': None,
            'decrypt_success': False, 
            'csv_file': None,
            'error': None
        }
        
        try:
            # 准备请求
            headers = {
                'Cookie': self.cookie_str,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': doc_info['url'],
                'Accept': '*/*'
            }
            
            # 下载CSV和Excel格式
            formats = [
                ('CSV', 'export_csv'),
                ('Excel', 'export_xlsx')
            ]
            
            for format_name, export_type in formats:
                print(f"\n下载 {format_name} 格式...")
                
                download_url = f"https://docs.qq.com/dop-api/opendoc?id={doc_info['id']}&type={export_type}"
                
                response = requests.get(download_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    print(f"✅ {format_name} 下载成功: {len(response.content)} bytes")
                    
                    # 检查内容类型
                    content_type = response.headers.get('Content-Type', '')
                    print(f"   Content-Type: {content_type}")
                    
                    if 'ejs-data' in content_type:
                        print(f"   ✅ 确认为EJS格式")
                        
                        # 保存EJS文件
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"{doc_info['id']}_{format_name}_{timestamp}.ejs"
                        file_path = self.output_dir / filename
                        
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        
                        results['download_success'] = True
                        results['ejs_file'] = str(file_path)
                        
                        print(f"   💾 已保存: {filename}")
                        
                        # 立即解密
                        csv_result = self.decrypt_ejs_file(str(file_path), doc_info)
                        if csv_result:
                            results['decrypt_success'] = True
                            results['csv_file'] = csv_result
                        
                        break  # 成功一个格式就够了
                    else:
                        print(f"   ❌ 非EJS格式: {content_type}")
                        
                else:
                    print(f"   ❌ 下载失败: HTTP {response.status_code}")
            
        except Exception as e:
            error_msg = f"下载异常: {e}"
            print(f"❌ {error_msg}")
            results['error'] = error_msg
            
        return results
    
    def decrypt_ejs_file(self, ejs_file, doc_info):
        """解密EJS文件"""
        print(f"\n  🔓 开始解密EJS文件...")
        
        try:
            # 使用Node.js解密脚本
            node_script = '/root/projects/tencent-doc-manager/complete_ejs_decoder.js'
            
            if not Path(node_script).exists():
                print(f"     ❌ Node.js解密脚本不存在: {node_script}")
                return None
            
            # 临时修改脚本以处理单个文件
            temp_script = self.create_temp_decoder_script(ejs_file, doc_info)
            
            # 执行Node.js脚本
            result = subprocess.run(
                ['node', temp_script],
                capture_output=True,
                text=True,
                cwd=str(self.output_dir)
            )
            
            if result.returncode == 0:
                print("     ✅ Node.js解密成功")
                
                # 查找生成的CSV文件
                csv_files = list(self.output_dir.glob(f"*{doc_info['id']}*decoded*.csv"))
                if csv_files:
                    latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
                    print(f"     💾 生成CSV: {latest_csv.name}")
                    return str(latest_csv)
            else:
                print(f"     ❌ Node.js解密失败: {result.stderr}")
                
            # 如果Node.js失败，使用Python方法
            return self.decrypt_with_python(ejs_file, doc_info)
            
        except Exception as e:
            print(f"     ❌ 解密异常: {e}")
            return None
    
    def create_temp_decoder_script(self, ejs_file, doc_info):
        """创建临时解密脚本"""
        temp_script = self.output_dir / f"temp_decoder_{doc_info['id']}.js"
        
        script_content = f'''
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

// 导入解密器
const TencentEJSDecoder = require('/root/projects/tencent-doc-manager/complete_ejs_decoder.js');

async function decryptSingleFile() {{
    const decoder = new TencentEJSDecoder();
    const result = await decoder.decodeEJSFile('{ejs_file}');
    
    if (result.success) {{
        console.log(`✅ 解密成功: ${{result.csvFile}}`);
    }} else {{
        console.log(`❌ 解密失败: ${{result.error}}`);
    }}
}}

decryptSingleFile().catch(console.error);
'''
        
        with open(temp_script, 'w') as f:
            f.write(script_content)
        
        return str(temp_script)
    
    def decrypt_with_python(self, ejs_file, doc_info):
        """使用Python解密方法"""
        print("     🐍 尝试Python解密方法...")
        
        try:
            # 导入Python解密模块
            import sys
            sys.path.append('/root/projects/tencent-doc-manager')
            
            # 这里可以调用之前开发的Python解密函数
            # 为简化，直接返回None，实际可以实现
            print("     ⚠️ Python解密方法待实现")
            return None
            
        except Exception as e:
            print(f"     ❌ Python解密失败: {e}")
            return None
    
    def analyze_csv_results(self, csv_file, doc_info):
        """分析CSV结果质量"""
        if not csv_file or not Path(csv_file).exists():
            return None
        
        print(f"\n  📊 分析CSV结果...")
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            # 统计数据
            analysis = {
                'total_lines': len(lines),
                'non_empty_lines': len(non_empty_lines),
                'file_size': Path(csv_file).stat().st_size,
                'has_chinese': bool(re.search(r'[\u4e00-\u9fff]', content)),
                'sample_lines': non_empty_lines[:5]
            }
            
            print(f"     总行数: {analysis['total_lines']}")
            print(f"     非空行: {analysis['non_empty_lines']}")
            print(f"     文件大小: {analysis['file_size']} bytes")
            print(f"     包含中文: {'是' if analysis['has_chinese'] else '否'}")
            
            # 显示前几行示例
            print(f"     前3行示例:")
            for i, line in enumerate(analysis['sample_lines'][:3], 1):
                preview = line[:80] + ('...' if len(line) > 80 else '')
                print(f"       行{i}: {preview}")
            
            return analysis
            
        except Exception as e:
            print(f"     ❌ 分析失败: {e}")
            return None
    
    def run_real_test(self):
        """执行真实测试"""
        print("🚀 开始真实测试批量处理")
        print("="*80)
        print(f"测试文档数量: {len(self.test_documents)}")
        print(f"输出目录: {self.output_dir}")
        print("="*80)
        
        all_results = []
        
        # 依次处理每个文档
        for i, doc_info in enumerate(self.test_documents, 1):
            print(f"\n🔄 处理文档 {i}/{len(self.test_documents)}")
            
            # 下载和解密
            result = self.download_document(doc_info)
            
            # 分析结果
            if result['csv_file']:
                result['analysis'] = self.analyze_csv_results(result['csv_file'], doc_info)
            
            all_results.append(result)
            
            # 等待一下避免请求太快
            time.sleep(2)
        
        # 生成测试报告
        self.generate_test_report(all_results)
        
        return all_results
    
    def generate_test_report(self, results):
        """生成测试报告"""
        print("\n" + "="*80)
        print("🎯 真实测试结果报告")
        print("="*80)
        
        success_count = sum(1 for r in results if r['decrypt_success'])
        download_count = sum(1 for r in results if r['download_success'])
        
        print(f"\n📊 总体统计:")
        print(f"   测试文档总数: {len(results)}")
        print(f"   下载成功: {download_count}/{len(results)}")
        print(f"   解密成功: {success_count}/{len(results)}")
        print(f"   成功率: {success_count/len(results)*100:.1f}%")
        
        print(f"\n📋 详细结果:")
        for i, result in enumerate(results, 1):
            doc_name = result['doc_info']['name']
            
            if result['decrypt_success']:
                print(f"   ✅ {i}. {doc_name}")
                print(f"      EJS文件: {Path(result['ejs_file']).name}")
                print(f"      CSV文件: {Path(result['csv_file']).name}")
                if result.get('analysis'):
                    analysis = result['analysis']
                    print(f"      数据行数: {analysis['non_empty_lines']}")
                    print(f"      包含中文: {'是' if analysis['has_chinese'] else '否'}")
            elif result['download_success']:
                print(f"   ⚠️  {i}. {doc_name} (下载成功但解密失败)")
                print(f"      EJS文件: {Path(result['ejs_file']).name}")
            else:
                print(f"   ❌ {i}. {doc_name} (下载失败)")
                if result.get('error'):
                    print(f"      错误: {result['error']}")
        
        # 保存详细报告
        report_file = self.output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 详细报告已保存: {report_file.name}")
        
        if success_count == len(results):
            print("\n🎉🎉🎉 所有测试完全成功！真实业务数据解密方案验证成功！")
        elif success_count > 0:
            print(f"\n🎯 部分成功，成功率 {success_count/len(results)*100:.1f}%")
        else:
            print("\n⚠️ 需要调试解密流程")

def main():
    """主函数"""
    # 导入re模块
    import re
    globals()['re'] = re
    
    # 执行真实测试
    test_manager = RealTestManager()
    results = test_manager.run_real_test()
    
    return results

if __name__ == "__main__":
    results = main()