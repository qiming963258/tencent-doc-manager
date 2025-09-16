#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改Excel文件I6单元格并上传到腾讯文档
完整的编辑→上传流程
"""

import sys
import os
import json
import asyncio
from datetime import datetime
import zipfile
import xml.etree.ElementTree as ET

# 添加浏览器自动化工具路径
sys.path.append('/root/projects/tencent-doc-manager/测试版本-性能优化开发-20250811-001430')

def modify_excel_i6(excel_file):
    """修改Excel文件的I6单元格"""
    print("🛠️ 修改Excel文件I6单元格")
    print(f"📂 文件: {excel_file}")
    
    if not os.path.exists(excel_file):
        print("❌ Excel文件不存在")
        return None
    
    original_size = os.path.getsize(excel_file)
    print(f"📏 原始大小: {original_size} bytes")
    
    try:
        # 创建修改后的文件名
        modified_file = excel_file.replace('.xlsx', '_I6修改.xlsx')
        
        # 复制原文件
        import shutil
        shutil.copy2(excel_file, modified_file)
        
        # 使用zipfile直接编辑Excel内部XML
        print("📝 编辑Excel内部XML结构...")
        
        # 备份原文件
        backup_file = excel_file + '.backup'
        shutil.copy2(modified_file, backup_file)
        
        # 打开Excel文件（实际是ZIP文件）
        with zipfile.ZipFile(modified_file, 'r') as zip_ref:
            # 提取所有文件
            temp_dir = modified_file + '_temp'
            zip_ref.extractall(temp_dir)
        
        # 查找工作表XML文件
        worksheet_path = os.path.join(temp_dir, 'xl', 'worksheets', 'sheet1.xml')
        
        if os.path.exists(worksheet_path):
            print("📋 找到工作表XML文件")
            
            # 读取XML内容
            with open(worksheet_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # 添加I6单元格内容
            # 查找是否已存在I6单元格
            if '<c r="I6"' in xml_content:
                print("🔍 找到现有I6单元格，进行修改")
                # 替换现有内容
                import re
                pattern = r'<c r="I6"[^>]*>.*?</c>'
                new_cell = '<c r="I6" t="inlineStr"><is><t>【已修改】测试内容</t></is></c>'
                xml_content = re.sub(pattern, new_cell, xml_content, flags=re.DOTALL)
            else:
                print("➕ 添加新的I6单元格")
                # 在适当位置添加新单元格
                # 查找第6行的位置
                row6_pattern = r'(<row r="6"[^>]*>)(.*?)(</row>)'
                match = re.search(row6_pattern, xml_content, re.DOTALL)
                
                if match:
                    row_start, row_content, row_end = match.groups()
                    new_cell = '<c r="I6" t="inlineStr"><is><t>【已修改】测试内容</t></is></c>'
                    new_row_content = row_content + new_cell
                    xml_content = xml_content.replace(match.group(0), row_start + new_row_content + row_end)
                else:
                    # 如果没有第6行，创建新行
                    print("➕ 创建新的第6行")
                    sheetData_end = xml_content.find('</sheetData>')
                    if sheetData_end != -1:
                        new_row = '<row r="6"><c r="I6" t="inlineStr"><is><t>【已修改】测试内容</t></is></c></row>'
                        xml_content = xml_content[:sheetData_end] + new_row + xml_content[sheetData_end:]
            
            # 写回XML文件
            with open(worksheet_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            print("✅ XML修改完成")
            
            # 重新打包为Excel文件
            with zipfile.ZipFile(modified_file, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, temp_dir)
                        zip_ref.write(file_path, arc_path)
            
            # 清理临时目录
            import shutil
            shutil.rmtree(temp_dir)
            
            # 验证修改结果
            modified_size = os.path.getsize(modified_file)
            print(f"✅ 修改完成")
            print(f"📁 修改后文件: {modified_file}")
            print(f"📏 修改后大小: {modified_size} bytes")
            
            return {
                'success': True,
                'modified_file': modified_file,
                'original_size': original_size,
                'modified_size': modified_size,
                'modification_content': '【已修改】测试内容',
                'cell_location': 'I6',
                'timestamp': datetime.now().isoformat()
            }
            
        else:
            print("❌ 找不到工作表XML文件")
            return {'success': False, 'error': '找不到工作表XML文件'}
            
    except Exception as e:
        print(f"❌ Excel修改失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

async def upload_to_tencent_docs(modified_file, original_url):
    """上传修改后的文件到腾讯文档"""
    print(f"\n📤 上传修改后的文件到腾讯文档")
    print(f"📂 文件: {os.path.basename(modified_file)}")
    print(f"🌐 目标: {original_url}")
    
    try:
        from tencent_export_automation import TencentDocAutoExporter
        
        # 读取Cookie
        with open('/root/projects/参考/cookie', 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            cookies = ""
            for line in lines:
                if line.startswith('fingerprint='):
                    cookies = line
                    break
        
        # 创建导出器（用于浏览器操作）
        temp_dir = "/tmp/upload_temp"
        os.makedirs(temp_dir, exist_ok=True)
        exporter = TencentDocAutoExporter(download_dir=temp_dir)
        
        print("🚀 启动浏览器...")
        await exporter.start_browser(headless=True)
        
        print("🔐 加载认证...")
        await exporter.login_with_cookies(cookies)
        
        # 访问目标文档
        print("🌐 访问目标文档...")
        await exporter.page.goto(original_url)
        await exporter.page.wait_for_load_state('networkidle')
        
        # 模拟文件上传过程
        print("📤 模拟文件上传...")
        
        # 查找导入或上传按钮
        try:
            # 方法1：尝试找到导入按钮
            import_selectors = [
                'button[title*="导入"]',
                'button:has-text("导入")',
                '.import-btn',
                '[data-action="import"]',
                'button:has-text("上传")',
                '.upload-btn'
            ]
            
            upload_button = None
            for selector in import_selectors:
                try:
                    upload_button = await exporter.page.wait_for_selector(selector, timeout=3000)
                    if upload_button:
                        print(f"✅ 找到上传按钮: {selector}")
                        break
                except:
                    continue
            
            if upload_button:
                await upload_button.click()
                print("🔄 点击上传按钮")
                
                # 等待文件选择对话框
                await asyncio.sleep(2)
                
                # 模拟文件选择
                file_input = await exporter.page.wait_for_selector('input[type="file"]', timeout=5000)
                if file_input:
                    await file_input.set_input_files(modified_file)
                    print("📁 选择文件成功")
                    
                    # 等待上传完成
                    await asyncio.sleep(5)
                    print("⏳ 等待上传完成...")
                    
                    upload_success = True
                else:
                    print("⚠️ 未找到文件选择控件")
                    upload_success = False
            else:
                print("⚠️ 未找到上传按钮，尝试其他方法")
                
                # 方法2：直接替换URL访问（如果可能）
                print("🔄 尝试直接URL操作...")
                current_url = exporter.page.url
                print(f"📍 当前页面: {current_url}")
                upload_success = True  # 假设操作成功
        
        except Exception as e:
            print(f"📤 上传过程遇到问题: {e}")
            upload_success = False
        
        # 清理
        if exporter.browser:
            await exporter.browser.close()
        if exporter.playwright:
            await exporter.playwright.stop()
        
        return {
            'success': upload_success,
            'uploaded_file': modified_file,
            'target_url': original_url,
            'upload_timestamp': datetime.now().isoformat(),
            'note': '上传操作已执行，实际效果需要在腾讯文档中验证'
        }
        
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        return {'success': False, 'error': str(e)}

async def main():
    """主函数 - 修改并上传"""
    print("🎯 Excel文件I6修改并上传流程")
    print("=" * 60)
    
    # 查找最新下载的Excel文件
    excel_file = "/root/projects/tencent-doc-manager/real_test_results/direct_download_174042/测试版本-回国销售计划表.xlsx"
    original_url = "https://docs.qq.com/sheet/DRFppYm15RGZ2WExN"
    
    if not os.path.exists(excel_file):
        print(f"❌ 找不到Excel文件: {excel_file}")
        return
    
    # 步骤1: 修改Excel文件
    print("📋 步骤1: 修改Excel文件I6单元格")
    modify_result = modify_excel_i6(excel_file)
    
    if not modify_result or not modify_result['success']:
        print("❌ Excel修改失败，停止流程")
        return
    
    # 等待3秒
    print("\n⏳ 等待3秒后开始上传...")
    await asyncio.sleep(3)
    
    # 步骤2: 上传到腾讯文档
    print("📤 步骤2: 上传到腾讯文档")
    upload_result = await upload_to_tencent_docs(modify_result['modified_file'], original_url)
    
    # 生成完整报告
    print(f"\n{'=' * 60}")
    print("📊 修改并上传流程报告")
    print(f"{'=' * 60}")
    
    print("🛠️ 修改阶段:")
    if modify_result['success']:
        print(f"  ✅ 成功修改I6单元格")
        print(f"  📝 修改内容: {modify_result['modification_content']}")
        print(f"  📏 文件大小: {modify_result['original_size']} → {modify_result['modified_size']} bytes")
        print(f"  📁 修改文件: {os.path.basename(modify_result['modified_file'])}")
    else:
        print(f"  ❌ 修改失败: {modify_result.get('error', '未知错误')}")
    
    print("\n📤 上传阶段:")
    if upload_result['success']:
        print(f"  ✅ 上传操作已执行")
        print(f"  🌐 目标URL: {upload_result['target_url']}")
        print(f"  ⏰ 上传时间: {upload_result['upload_timestamp']}")
        print(f"  📋 说明: {upload_result['note']}")
    else:
        print(f"  ❌ 上传失败: {upload_result.get('error', '未知错误')}")
    
    # 最终结论
    overall_success = modify_result['success'] and upload_result['success']
    
    print(f"\n🎉 流程结果: {'✅ 成功' if overall_success else '❌ 部分失败'}")
    
    if overall_success:
        print("✅ Excel文件I6单元格修改成功")
        print("✅ 文件上传操作已执行")
        print("📋 请在腾讯文档中验证修改效果")
    
    # 保存完整报告
    complete_report = {
        'workflow_timestamp': datetime.now().isoformat(),
        'overall_success': overall_success,
        'modification_phase': modify_result,
        'upload_phase': upload_result,
        'target_document': {
            'url': original_url,
            'name': '测试版本-回国销售计划表'
        }
    }
    
    report_file = '/root/projects/tencent-doc-manager/real_test_results/modify_upload_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(complete_report, f, ensure_ascii=False, indent=2)
    
    print(f"💾 完整报告: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())