#!/usr/bin/env python3
"""测试UI修复效果 - 验证综合打分数据能正确显示"""

import json
import requests
import time

def test_comprehensive_mode():
    """测试综合打分模式下的UI数据"""

    print("=" * 60)
    print("🔧 UI适配问题修复测试")
    print("=" * 60)

    base_url = "http://localhost:8089"

    # 1. 加载综合打分文件
    print("\n📁 步骤1: 加载综合打分文件...")
    comprehensive_file = "/root/projects/tencent-doc-manager/scoring_results/comprehensive/comprehensive_score_W38_20250915_032357.json"

    response = requests.get(f"{base_url}/api/load-comprehensive-data", params={"file": comprehensive_file})
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ 成功加载综合打分文件")
            print(f"   - 总修改数: {data.get('total_modifications', 0)}")
            print(f"   - 表格数量: {data.get('table_count', 0)}")
        else:
            print(f"❌ 加载失败: {data.get('error')}")
            return False
    else:
        print(f"❌ API调用失败: {response.status_code}")
        return False

    # 2. 切换到综合打分模式
    print("\n🔄 步骤2: 切换到综合打分模式...")
    response = requests.post(f"{base_url}/api/switch_data_source", json={"source": "comprehensive"})
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ 已切换到综合打分模式")
        else:
            print(f"❌ 切换失败: {data.get('error')}")
            return False

    # 3. 获取热力图数据
    print("\n📊 步骤3: 获取热力图数据...")
    response = requests.get(f"{base_url}/api/data")
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            heatmap_data = data['data']['heatmap_data']
            statistics = data['data']['statistics']

            print(f"✅ 成功获取热力图数据")
            print(f"\n📈 统计信息:")
            print(f"   - 总修改数: {statistics.get('total_changes', 0)}")
            print(f"   - 非零单元格: {statistics.get('non_zero_cells', 0)}")
            print(f"   - 热点单元格: {statistics.get('hot_cells', 0)}")
            print(f"   - 数据源: {statistics.get('data_source', 'unknown')}")

            # 检查热力图是否有非零值
            non_zero_count = 0
            heat_values_sample = []
            for row in heatmap_data:
                for val in row:
                    if val > 0.05:
                        non_zero_count += 1
                        if len(heat_values_sample) < 10:
                            heat_values_sample.append(round(val, 2))

            print(f"\n🔥 热力图分析:")
            print(f"   - 矩阵大小: {len(heatmap_data)}×{len(heatmap_data[0]) if heatmap_data else 0}")
            print(f"   - 非背景值单元格: {non_zero_count}")
            print(f"   - 热力值样本: {heat_values_sample}")

            # 验证修复是否成功
            if statistics.get('total_changes', 0) > 0 and non_zero_count > 0:
                print("\n✅ 修复验证成功！")
                print("   - UI正确显示了修改数量")
                print("   - 热力图包含有效的热力值")
                return True
            else:
                print("\n⚠️ 修复可能未完全生效:")
                if statistics.get('total_changes', 0) == 0:
                    print("   - 统计显示0修改（应该是19）")
                if non_zero_count == 0:
                    print("   - 热力图全部为背景色（应该有热力值）")
                return False
        else:
            print(f"❌ 获取数据失败: {data.get('error')}")
            return False
    else:
        print(f"❌ API调用失败: {response.status_code}")
        return False

def check_ui_server_logs():
    """检查UI服务器日志输出"""
    print("\n📝 检查服务器日志（最近输出）:")
    print("   请查看8089服务器控制台输出，应该看到:")
    print("   - ✅ 从ui_data填充表格 xxx 热力值: [...]")
    print("   - 而不是: ❌ 错误：表格 xxx 缺少必需的heat_values字段")

if __name__ == "__main__":
    try:
        # 确保服务器正在运行
        print("🚀 开始测试UI修复效果...")
        print("   确保8089端口服务器正在运行")
        time.sleep(1)

        # 运行测试
        success = test_comprehensive_mode()

        # 输出最终结果
        print("\n" + "=" * 60)
        if success:
            print("🎉 测试通过 - UI适配问题已修复！")
            print("   - 热力图显示正确的颜色")
            print("   - 统计信息显示正确的修改数")
        else:
            print("❌ 测试失败 - 需要进一步调试")
        print("=" * 60)

        # 提醒检查日志
        check_ui_server_logs()

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到8089端口，请确保服务器正在运行:")
        print("   python3 /root/projects/tencent-doc-manager/production/servers/final_heatmap_server.py")
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")