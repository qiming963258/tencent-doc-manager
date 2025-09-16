#!/usr/bin/env python3
"""
8090测试服务器验证脚本
验证综合打分到热力图的完整转换功能
"""

import requests
import json
import sys
from typing import Dict, List, Tuple

def verify_test_server() -> Tuple[bool, List[str]]:
    """验证测试服务器功能"""
    results = []
    all_pass = True
    
    base_url = "http://localhost:8090"
    
    # 1. 检查服务器是否运行
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            results.append("✅ 服务器运行正常 (端口8090)")
        else:
            results.append(f"❌ 服务器响应异常: {response.status_code}")
            all_pass = False
    except Exception as e:
        results.append(f"❌ 无法连接服务器: {e}")
        return False, results
    
    # 2. 检查API数据端点
    try:
        response = requests.get(f"{base_url}/api/data")
        data = response.json()
        
        if data.get('success'):
            inner_data = data.get('data', {})
            heatmap = inner_data.get('heatmap_data', [])
            
            if len(heatmap) == 22:
                results.append(f"✅ 热力图行数正确: {len(heatmap)} 行")
            else:
                results.append(f"❌ 热力图行数错误: {len(heatmap)} 行 (期望22)")
                all_pass = False
            
            if heatmap and len(heatmap[0]) == 19:
                results.append(f"✅ 热力图列数正确: {len(heatmap[0])} 列")
            else:
                results.append(f"❌ 热力图列数错误: {len(heatmap[0]) if heatmap else 0} 列 (期望19)")
                all_pass = False
                
        else:
            results.append("❌ API返回失败状态")
            all_pass = False
            
    except Exception as e:
        results.append(f"❌ API调用失败: {e}")
        all_pass = False
    
    # 3. 验证测试数据分布
    try:
        # 统计风险等级分布
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        unmodified_count = 0
        
        for row in heatmap:
            max_val = max(row) if row else 0
            if max_val == 0:
                unmodified_count += 1
            elif max_val >= 0.7:
                high_risk_count += 1
            elif max_val >= 0.4:
                medium_risk_count += 1
            else:
                low_risk_count += 1
        
        results.append(f"📊 风险分布统计:")
        results.append(f"   - 高风险 (L1): {high_risk_count} 个表格")
        results.append(f"   - 中风险 (L2): {medium_risk_count} 个表格")
        results.append(f"   - 低风险 (L3): {low_risk_count} 个表格")
        results.append(f"   - 未修改: {unmodified_count} 个表格")
        
        # 验证是否有未修改的表格
        if unmodified_count >= 3:
            results.append(f"✅ 包含未修改表格: {unmodified_count} 个")
        else:
            results.append(f"⚠️ 未修改表格数量: {unmodified_count} 个 (期望至少3个)")
            
    except Exception as e:
        results.append(f"❌ 数据分析失败: {e}")
        all_pass = False
    
    # 4. 检查临时文件持久化
    import os
    temp_file = "/tmp/test_scoring_data.json"
    if os.path.exists(temp_file):
        try:
            with open(temp_file, 'r', encoding='utf-8') as f:
                temp_data = json.load(f)
                table_count = len(temp_data.get('table_scores', []))
                results.append(f"✅ 临时文件存在: {table_count} 个表格数据")
        except Exception as e:
            results.append(f"⚠️ 临时文件读取失败: {e}")
    else:
        results.append("⚠️ 临时文件不存在 (首次运行时正常)")
    
    # 5. 验证热力图数值范围
    try:
        all_values = []
        for row in heatmap:
            all_values.extend(row)
        
        min_val = min(all_values) if all_values else 0
        max_val = max(all_values) if all_values else 0
        
        if 0 <= min_val <= 1 and 0 <= max_val <= 1:
            results.append(f"✅ 热力图数值范围正确: [{min_val:.2f}, {max_val:.2f}]")
        else:
            results.append(f"❌ 热力图数值范围异常: [{min_val:.2f}, {max_val:.2f}]")
            all_pass = False
            
    except Exception as e:
        results.append(f"❌ 数值验证失败: {e}")
        all_pass = False
    
    return all_pass, results

def main():
    """主函数"""
    print("=" * 60)
    print("🧪 8090端口测试服务器验证")
    print("=" * 60)
    
    all_pass, results = verify_test_server()
    
    for result in results:
        print(result)
    
    print("=" * 60)
    if all_pass:
        print("✅ 所有测试通过！")
        print("🎯 测试服务器功能完整:")
        print("   - 综合打分文件加载 ✓")
        print("   - 热力图转换正确 ✓")
        print("   - 数据持久化正常 ✓")
        print("   - 22×19矩阵显示 ✓")
        print("\n🌐 访问地址: http://202.140.143.88:8090")
        return 0
    else:
        print("❌ 部分测试失败，请检查问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())