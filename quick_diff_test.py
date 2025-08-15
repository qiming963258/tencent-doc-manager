#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速差异识别测试 - 测试版本内CSV对比程序的快速识别能力
"""

import pandas as pd
import sys
import os

# 添加路径以导入模块
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

from document_change_analyzer import DocumentChangeAnalyzer

def quick_diff_test():
    """快速差异识别测试"""
    print("🔍 测试版本内CSV对比程序快速差异识别功能")
    print("="*60)
    
    # 文件路径
    original_file = "/root/projects/tencent-doc-manager/refer/测试版本-小红书部门-工作表2.csv"
    modified_file = "/root/projects/tencent-doc-manager/测试版本-小红书部门-工作表2-修改版.csv"
    
    print(f"原始文件: {os.path.basename(original_file)}")
    print(f"修改文件: {os.path.basename(modified_file)}")
    
    # 创建分析器
    analyzer = DocumentChangeAnalyzer()
    
    # 快速加载并比较前几行关键数据
    print("\n📋 快速数据加载...")
    
    try:
        # 加载原始数据的前5行用于快速对比
        original_df = pd.read_csv(original_file, encoding='utf-8-sig', skiprows=1, nrows=5)
        modified_df = pd.read_csv(modified_file, encoding='utf-8-sig', skiprows=1, nrows=5)
        
        print(f"原始数据: {len(original_df)}行 × {len(original_df.columns)}列")
        print(f"修改数据: {len(modified_df)}行 × {len(modified_df.columns)}列")
        
        # 快速对比关键列的变化
        print(f"\n🔍 快速差异识别 - 关键列对比:")
        
        key_columns = ["目标对齐", "关键KR对齐", "负责人", "重要程度"]
        
        for col in key_columns:
            if col in original_df.columns and col in modified_df.columns:
                original_val = str(original_df[col].iloc[0]) if len(original_df) > 0 else ""
                modified_val = str(modified_df[col].iloc[0]) if len(modified_df) > 0 else ""
                
                if original_val != modified_val:
                    print(f"  🔄 【{col}】发现变更:")
                    print(f"      原值: {original_val}")
                    print(f"      新值: {modified_val}")
                    
                    # 判断风险等级
                    risk_level = analyzer.column_risk_levels.get(col, "L3")
                    risk_icons = {"L1": "🔴", "L2": "🟡", "L3": "🟢"}
                    print(f"      风险: {risk_icons.get(risk_level, '❓')} {risk_level}")
                else:
                    print(f"  ✅ 【{col}】无变更")
            else:
                print(f"  ❌ 【{col}】列不存在")
        
        # 详细差异分析（仅针对第一行数据）
        print(f"\n🔍 第一行详细差异分析:")
        
        if len(original_df) > 0 and len(modified_df) > 0:
            changes_found = 0
            
            for col in original_df.columns:
                if col in modified_df.columns:
                    orig_val = str(original_df[col].iloc[0])
                    mod_val = str(modified_df[col].iloc[0])
                    
                    if orig_val != mod_val:
                        changes_found += 1
                        risk_level = analyzer.column_risk_levels.get(col, "L3")
                        risk_icons = {"L1": "🔴", "L2": "🟡", "L3": "🟢"}
                        
                        print(f"  [{changes_found}] {risk_icons.get(risk_level, '❓')} {col}")
                        print(f"      原: {orig_val[:50]}{'...' if len(orig_val) > 50 else ''}")
                        print(f"      新: {mod_val[:50]}{'...' if len(mod_val) > 50 else ''}")
            
            print(f"\n📊 快速识别结果:")
            print(f"  总差异数: {changes_found}")
            
            # 计算快速风险评估
            l1_count = sum(1 for col in original_df.columns 
                         if col in modified_df.columns and 
                         analyzer.column_risk_levels.get(col, "L3") == "L1" and
                         str(original_df[col].iloc[0]) != str(modified_df[col].iloc[0]))
            
            l2_count = sum(1 for col in original_df.columns 
                         if col in modified_df.columns and 
                         analyzer.column_risk_levels.get(col, "L3") == "L2" and
                         str(original_df[col].iloc[0]) != str(modified_df[col].iloc[0]))
                         
            print(f"  L1高风险变更: {l1_count}")
            print(f"  L2中风险变更: {l2_count}")
            
            if l1_count > 0:
                print(f"  ⚠️  风险等级: 🔴 严重")
            elif l2_count > 2:
                print(f"  ⚠️  风险等级: 🟡 中等")
            else:
                print(f"  ⚠️  风险等级: 🟢 正常")
                
        else:
            print("  ❌ 无有效数据进行对比")
            
    except Exception as e:
        print(f"❌ 快速差异识别失败: {e}")
    
    print("\n" + "="*60)
    print("✅ 快速差异识别测试完成")

if __name__ == "__main__":
    quick_diff_test()