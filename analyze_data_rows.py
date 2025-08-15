#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细数据行分析 - 检查实际数据内容
"""

import pandas as pd
import sys
import os

def analyze_data_rows():
    """分析数据行内容"""
    print("🔍 详细数据行内容分析")
    print("="*60)
    
    # 文件路径
    original_file = "/root/projects/tencent-doc-manager/refer/测试版本-小红书部门-工作表2.csv"
    modified_file = "/root/projects/tencent-doc-manager/测试版本-小红书部门-工作表2-修改版.csv"
    
    print("📋 原始文件内容分析:")
    try:
        # 读取原始文件的所有行
        with open(original_file, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()[:10]  # 前10行
            
        for i, line in enumerate(lines, 1):
            print(f"  第{i}行: {line.strip()[:100]}")
            
        # 使用pandas读取（跳过第一行标题）
        original_df = pd.read_csv(original_file, encoding='utf-8-sig', skiprows=1)
        print(f"\n原始数据形状: {original_df.shape}")
        print(f"有效数据行: {len(original_df.dropna(how='all'))}")
        
        # 显示第一个有效数据行
        first_valid_row = None
        for idx, row in original_df.iterrows():
            if not row.isna().all():
                first_valid_row = row
                print(f"第一个有效数据行 (行{idx}):")
                for col, val in row.items():
                    if pd.notna(val) and str(val).strip():
                        print(f"  {col}: {val}")
                break
                
    except Exception as e:
        print(f"❌ 读取原始文件失败: {e}")
    
    print("\n" + "-"*60)
    print("📋 修改文件内容分析:")
    try:
        # 读取修改文件的所有行
        with open(modified_file, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()[:10]  # 前10行
            
        for i, line in enumerate(lines, 1):
            print(f"  第{i}行: {line.strip()[:100]}")
            
        # 使用pandas读取
        modified_df = pd.read_csv(modified_file, encoding='utf-8-sig', skiprows=1)
        print(f"\n修改数据形状: {modified_df.shape}")
        print(f"有效数据行: {len(modified_df.dropna(how='all'))}")
        
        # 显示第一个有效数据行
        first_valid_row = None
        for idx, row in modified_df.iterrows():
            if not row.isna().all():
                first_valid_row = row
                print(f"第一个有效数据行 (行{idx}):")
                for col, val in row.items():
                    if pd.notna(val) and str(val).strip():
                        print(f"  {col}: {val}")
                break
                
    except Exception as e:
        print(f"❌ 读取修改文件失败: {e}")
    
    # 直接对比关键字段
    print("\n" + "-"*60)
    print("🔍 直接字段对比:")
    
    try:
        orig_df = pd.read_csv(original_file, encoding='utf-8-sig', skiprows=1)
        mod_df = pd.read_csv(modified_file, encoding='utf-8-sig', skiprows=1)
        
        # 找到第一个有效数据行的索引
        orig_valid_idx = None
        mod_valid_idx = None
        
        for idx, row in orig_df.iterrows():
            if not row.isna().all() and pd.notna(row.get('序号')):
                orig_valid_idx = idx
                break
                
        for idx, row in mod_df.iterrows():
            if not row.isna().all() and pd.notna(row.get('序号')):
                mod_valid_idx = idx
                break
        
        if orig_valid_idx is not None and mod_valid_idx is not None:
            print(f"对比数据行: 原始第{orig_valid_idx}行 vs 修改第{mod_valid_idx}行")
            
            key_fields = ["序号", "目标对齐", "关键KR对齐", "负责人", "重要程度"]
            
            for field in key_fields:
                if field in orig_df.columns and field in mod_df.columns:
                    orig_val = str(orig_df.iloc[orig_valid_idx][field]) if orig_valid_idx < len(orig_df) else "N/A"
                    mod_val = str(mod_df.iloc[mod_valid_idx][field]) if mod_valid_idx < len(mod_df) else "N/A"
                    
                    if orig_val != mod_val:
                        print(f"  🔄 {field}:")
                        print(f"    原: {orig_val}")
                        print(f"    新: {mod_val}")
                    else:
                        print(f"  ✅ {field}: {orig_val}")
        else:
            print("❌ 无法找到有效的数据行进行对比")
            
    except Exception as e:
        print(f"❌ 字段对比失败: {e}")
    
    print("\n" + "="*60)
    print("✅ 详细数据行分析完成")

if __name__ == "__main__":
    analyze_data_rows()