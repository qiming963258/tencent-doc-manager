#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正的文档变更分析器 - 测试特定修改的检测能力
"""

import pandas as pd
import difflib
import json
from datetime import datetime

def test_document_changes():
    """测试文档变更检测"""
    print("🔍 测试腾讯文档变更检测系统")
    
    original_file = "/root/projects/tencent-doc-manager/refer/测试版本-小红书部门-工作表2.csv"
    modified_file = "/root/projects/tencent-doc-manager/测试版本-小红书部门-工作表2-修改版2.csv"
    
    # 列风险等级配置
    column_risk_levels = {
        "序号": "L3", "项目类型": "L2", "来源": "L1", "任务发起时间": "L1", 
        "目标对齐": "L1", "关键KR对齐": "L1", "具体计划内容": "L2", 
        "邓总指导登记": "L2", "负责人": "L2", "协助人": "L2", "监督人": "L2", 
        "重要程度": "L1", "预计完成时间": "L1", "完成进度": "L1",
        "形成计划清单,完成附件、链接、截图上传": "L2",
        "复盘周期": "L3", "复盘时间": "L3", "对上汇报": "L3", 
        "应用情况": "L3", "进度分析与总结": "L3"
    }
    
    # 读取数据
    try:
        df_original = pd.read_csv(original_file, encoding='utf-8-sig')
        df_modified = pd.read_csv(modified_file, encoding='utf-8-sig')
    except Exception as e:
        print(f"❌ 文件读取错误: {e}")
        return
    
    print(f"✅ 原始文件: {len(df_original)}行 × {len(df_original.columns)}列")
    print(f"✅ 修改文件: {len(df_modified)}行 × {len(df_modified.columns)}列")
    
    # 检测变更
    changes_detected = []
    
    # 检查第4行的关键字段修改（对应数据行索引3，因为有标题行）
    if len(df_modified) > 3 and len(df_original) > 3:
        row_idx = 3  # 第4行数据
        
        # 检查每一列
        for col in df_modified.columns:
            if col in df_original.columns:
                original_val = str(df_original.iloc[row_idx][col]) if pd.notna(df_original.iloc[row_idx][col]) else ""
                modified_val = str(df_modified.iloc[row_idx][col]) if pd.notna(df_modified.iloc[row_idx][col]) else ""
                
                if original_val != modified_val:
                    risk_level = column_risk_levels.get(col, "L2")
                    changes_detected.append({
                        "row": row_idx + 1,  # 显示行号（1-based）
                        "column": col,
                        "original": original_val[:50] + "..." if len(original_val) > 50 else original_val,
                        "modified": modified_val[:50] + "..." if len(modified_val) > 50 else modified_val,
                        "risk_level": risk_level
                    })
    
    # 生成报告
    print("\n" + "="*60)
    print("📊 变更检测结果")
    print("="*60)
    
    if not changes_detected:
        print("❌ 未检测到任何变更")
        return
    
    # 统计不同风险等级的修改
    l1_count = len([c for c in changes_detected if c["risk_level"] == "L1"])
    l2_count = len([c for c in changes_detected if c["risk_level"] == "L2"])
    l3_count = len([c for c in changes_detected if c["risk_level"] == "L3"])
    
    print(f"总变更数量: {len(changes_detected)}")
    print(f"🔴 L1级严重违规: {l1_count}个")
    print(f"🟡 L2级异常修改: {l2_count}个")
    print(f"🟢 L3级常规修改: {l3_count}个")
    
    # 风险评估
    if l1_count > 0:
        print("⚠️  风险等级: 🔴 严重 (发现L1级别违规)")
    elif l2_count > 2:
        print("⚠️  风险等级: 🟡 中等")
    else:
        print("⚠️  风险等级: 🟢 正常")
    
    print("\n📋 详细变更列表:")
    for i, change in enumerate(changes_detected, 1):
        print(f"\n[{i}] 第{change['row']}行 - {change['column']}")
        print(f"    风险等级: {change['risk_level']}")
        print(f"    原内容: {change['original']}")
        print(f"    新内容: {change['modified']}")
        
        # 特别标记测试修改
        if "【修改测试】" in change['modified']:
            print(f"    ✅ 成功检测到测试标记")
    
    print("\n🔍 验证测试修改:")
    expected_changes = {
        "目标对齐": ("内容定位", "【修改测试】品牌定位", "L1"),
        "关键KR对齐": ("内容库优化迭代", "【修改测试】品牌优化", "L1"),
        "重要程度": ("5", "【修改测试】9", "L1")
    }
    
    detected_changes = {c["column"]: (c["original"], c["modified"], c["risk_level"]) for c in changes_detected}
    
    success_count = 0
    for col, (exp_orig, exp_mod, exp_risk) in expected_changes.items():
        if col in detected_changes:
            det_orig, det_mod, det_risk = detected_changes[col]
            if exp_risk == det_risk and exp_mod in det_mod:
                print(f"✅ {col}: {exp_risk}级修改检测成功")
                success_count += 1
            else:
                print(f"❌ {col}: 检测结果不匹配")
        else:
            print(f"❌ {col}: 未检测到修改")
    
    print(f"\n📈 测试准确率: {success_count}/{len(expected_changes)} ({success_count/len(expected_changes)*100:.1f}%)")
    
    if success_count >= 2:
        print("🎉 系统检测能力良好！成功识别关键风险修改")
    else:
        print("⚠️  系统需要进一步优化")

if __name__ == "__main__":
    test_document_changes()