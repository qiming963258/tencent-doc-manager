#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Flow Test - 修改Excel文件
使用openpyxl在A1单元格添加[已测试]标识
"""

import os
import openpyxl
import json
from datetime import datetime

def modify_excel_file(source_file, output_file):
    """
    修改Excel文件，在A1单元格添加[已测试]标识
    
    Args:
        source_file: 源Excel文件路径
        output_file: 输出Excel文件路径
    
    Returns:
        dict: 修改结果
    """
    try:
        print(f"开始修改Excel文件: {source_file}")
        
        # 打开Excel文件，忽略样式问题
        workbook = openpyxl.load_workbook(source_file, data_only=True)
        
        # 获取活动工作表
        worksheet = workbook.active
        print(f"当前工作表名称: {worksheet.title}")
        
        # 读取A1单元格的原始值
        original_a1_value = worksheet['A1'].value
        print(f"A1单元格原始值: {original_a1_value}")
        
        # 在A1单元格添加[已测试]标识
        if original_a1_value:
            # 如果A1单元格有值，在前面添加标识
            new_value = f"[已测试]{original_a1_value}"
        else:
            # 如果A1单元格为空，直接设置标识
            new_value = "[已测试]"
        
        worksheet['A1'] = new_value
        print(f"A1单元格新值: {new_value}")
        
        # 记录修改信息到B1单元格（作为元数据）
        modification_info = f"修改时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        worksheet['B1'] = modification_info
        print(f"B1单元格添加修改信息: {modification_info}")
        
        # 保存修改后的文件
        workbook.save(output_file)
        print(f"修改后的文件已保存: {output_file}")
        
        # 验证修改
        verification_workbook = openpyxl.load_workbook(output_file)
        verification_worksheet = verification_workbook.active
        verified_a1_value = verification_worksheet['A1'].value
        verified_b1_value = verification_worksheet['B1'].value
        
        print(f"验证 - A1单元格值: {verified_a1_value}")
        print(f"验证 - B1单元格值: {verified_b1_value}")
        
        # 获取文件大小信息
        source_size = os.path.getsize(source_file)
        output_size = os.path.getsize(output_file)
        
        return {
            "success": True,
            "source_file": source_file,
            "output_file": output_file,
            "original_a1_value": original_a1_value,
            "modified_a1_value": verified_a1_value,
            "modification_info": verified_b1_value,
            "source_file_size": source_size,
            "output_file_size": output_size,
            "worksheet_name": worksheet.title,
            "modification_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_msg = f"修改Excel文件失败: {e}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "source_file": source_file,
            "output_file": output_file
        }

def main():
    print("=== 腾讯文档完整流程测试 - Excel修改阶段 ===")
    
    # 文件路径
    base_dir = "/root/projects/tencent-doc-manager/real_test_results/complete_flow_test"
    source_file = os.path.join(base_dir, "测试版本-小红书部门.xlsx")
    output_file = os.path.join(base_dir, "测试版本-小红书部门_修改标记.xlsx")
    
    # 检查源文件是否存在
    if not os.path.exists(source_file):
        error_msg = f"源文件不存在: {source_file}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}
    
    # 执行修改
    result = modify_excel_file(source_file, output_file)
    
    # 保存测试结果
    test_result = {
        "timestamp": datetime.now().isoformat(),
        "test_phase": "excel_modification",
        "source_file": source_file,
        "output_file": output_file,
        "modification_result": result
    }
    
    result_file = os.path.join(base_dir, "excel_modification_result.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(test_result, f, ensure_ascii=False, indent=2)
    
    if result['success']:
        print(f"✅ Excel修改成功!")
        print(f"原始文件: {result['source_file']}")
        print(f"修改后文件: {result['output_file']}")
        print(f"原始A1值: {result['original_a1_value']}")
        print(f"修改后A1值: {result['modified_a1_value']}")
    else:
        print(f"❌ Excel修改失败: {result['error']}")
    
    return result

if __name__ == "__main__":
    main()