#!/usr/bin/env python3
"""
评估在文件名中加入URL作为唯一标识的影响和可行性分析
"""
import os
import re
import json
from urllib.parse import urlparse, quote, unquote

def analyze_current_naming():
    """分析当前的命名规则"""
    print("📋 当前命名规则分析")
    print("=" * 60)

    # 当前命名格式
    current_format = "tencent_{文档名}_{时间戳}_{版本类型}_W{周数}.{扩展名}"
    print(f"当前格式: {current_format}")

    # 示例文件名
    examples = [
        "tencent_出国销售计划表_20250915_0145_baseline_W39.csv",
        "tencent_回国销售计划表_20250914_2309_baseline_W39.csv",
        "tencent_小红书部门_20250915_0146_baseline_W39.csv"
    ]

    print("\n示例文件名:")
    for ex in examples:
        print(f"  - {ex}")
        # 解析文件名
        match = re.search(r'^tencent_(.+?)_(\d{8}_\d{4})_(baseline|midweek)_W(\d+)\.(\w+)$', ex)
        if match:
            doc_name, timestamp, version, week, ext = match.groups()
            print(f"    解析: 文档={doc_name}, 时间={timestamp}, 版本={version}, 周={week}")

    return examples

def propose_url_naming_schemes():
    """提出包含URL的命名方案"""
    print("\n\n💡 提出的URL命名方案")
    print("=" * 60)

    # 测试URL
    test_url = "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN"
    doc_id = urlparse(test_url).path.split('/')[-1]  # DWEFNU25TemFnZXJN

    print(f"测试URL: {test_url}")
    print(f"提取的文档ID: {doc_id}")

    schemes = {}

    # 方案1: 在文档名后添加文档ID
    schemes["方案1"] = {
        "格式": "tencent_{文档名}_{文档ID}_{时间戳}_{版本}_W{周}.{ext}",
        "示例": f"tencent_出国销售计划表_{doc_id}_20250915_0145_baseline_W39.csv",
        "优点": ["文档ID唯一标识", "向后兼容", "URL可反推"],
        "缺点": ["文件名变长", "需要ID到URL映射表"],
        "影响": "低 - 只需修改文件名生成和解析逻辑"
    }

    # 方案2: 使用简化的哈希ID
    import hashlib
    hash_id = hashlib.md5(test_url.encode()).hexdigest()[:8]
    schemes["方案2"] = {
        "格式": "tencent_{文档名}_{哈希ID}_{时间戳}_{版本}_W{周}.{ext}",
        "示例": f"tencent_出国销售计划表_{hash_id}_20250915_0145_baseline_W39.csv",
        "优点": ["ID更短", "唯一性好"],
        "缺点": ["需要哈希映射表", "不可反推URL"],
        "影响": "中 - 需要维护哈希映射表"
    }

    # 方案3: 建立独立的映射文件(推荐)
    schemes["方案3"] = {
        "格式": "保持现有格式不变",
        "映射文件": "baseline_url_mapping.json",
        "示例": {
            "tencent_出国销售计划表_20250915_0145_baseline_W39.csv": {
                "url": test_url,
                "doc_id": doc_id,
                "doc_name": "出国销售计划表",
                "download_time": "2025-09-15 01:45"
            }
        },
        "优点": ["零改动现有代码", "完整信息记录", "灵活扩展"],
        "缺点": ["需要维护映射文件"],
        "影响": "最小 - 仅新增映射文件读写"
    }

    for name, scheme in schemes.items():
        print(f"\n{name}:")
        for key, value in scheme.items():
            if isinstance(value, list):
                print(f"  {key}:")
                for item in value:
                    print(f"    - {item}")
            elif isinstance(value, dict):
                print(f"  {key}: {json.dumps(value, ensure_ascii=False, indent=4)}")
            else:
                print(f"  {key}: {value}")

    return schemes

def analyze_impact_on_existing_code():
    """分析对现有代码的影响"""
    print("\n\n📊 对现有代码的影响分析")
    print("=" * 60)

    # 检查所有使用基线文件的地方
    affected_files = {
        "production_integrated_test_system_8093.py": {
            "影响点": ["基线匹配逻辑", "文件名解析"],
            "修改量": "中等",
            "关键代码": "if doc_name in basename:"
        },
        "week_time_manager.py": {
            "影响点": ["基线文件查找"],
            "修改量": "小",
            "关键代码": "glob.glob(pattern)"
        },
        "final_heatmap_server.py": {
            "影响点": ["基线文件显示"],
            "修改量": "无",
            "关键代码": "不直接使用文件名"
        }
    }

    print("受影响的文件:")
    for file, info in affected_files.items():
        print(f"\n📄 {file}")
        for key, value in info.items():
            if isinstance(value, list):
                print(f"  {key}: {', '.join(value)}")
            else:
                print(f"  {key}: {value}")

    # 评估总体影响
    print("\n\n🎯 总体影响评估:")
    print("-" * 40)

    if os.path.exists("production_integrated_test_system_8093.py"):
        with open("production_integrated_test_system_8093.py", "r") as f:
            content = f.read()
            # 统计相关代码行数
            baseline_refs = len(re.findall(r'baseline', content, re.IGNORECASE))
            basename_refs = len(re.findall(r'os\.path\.basename', content))
            print(f"baseline相关引用: {baseline_refs}次")
            print(f"文件名解析引用: {basename_refs}次")

    return affected_files

def recommend_solution():
    """推荐最佳解决方案"""
    print("\n\n✅ 推荐解决方案")
    print("=" * 60)

    recommendation = {
        "短期方案（立即可行）": {
            "方法": "改进匹配逻辑 + 映射文件",
            "步骤": [
                "1. 修改匹配逻辑为精确匹配（解决问题1）",
                "2. 创建baseline_url_mapping.json记录URL映射（解决问题3）",
                "3. 保持文件名格式不变（避免颠覆性改动）"
            ],
            "代码示例": """
# 精确匹配逻辑
def extract_doc_name(filename):
    match = re.search(r'^tencent_(.+?)_\\d{8}_\\d{4}', filename)
    return match.group(1) if match else None

# 匹配改进
if extract_doc_name(baseline) == doc_name:
    matched_baseline = baseline

# URL映射记录
mapping = {
    filename: {
        "url": download_url,
        "doc_name": doc_name,
        "timestamp": timestamp
    }
}
"""
        },
        "长期方案（架构优化）": {
            "方法": "建立文档管理系统",
            "特性": [
                "统一的文档元数据管理",
                "URL、文件名、版本的完整映射",
                "支持多版本追踪",
                "API接口查询"
            ]
        }
    }

    print("📌 推荐采用短期方案，原因：")
    print("  1. ✅ 改动最小，不影响现有系统")
    print("  2. ✅ 立即解决文件匹配问题")
    print("  3. ✅ 保留URL信息用于追踪")
    print("  4. ✅ 可逐步过渡到长期方案")

    print("\n实施步骤:")
    for key, value in recommendation["短期方案（立即可行）"].items():
        if isinstance(value, list):
            print(f"\n{key}:")
            for item in value:
                print(f"  {item}")
        else:
            print(f"\n{key}:{value}")

    return recommendation

def main():
    print("🔍 文件命名方案影响评估报告")
    print("=" * 80)
    print("评估时间: 2025-09-24")
    print("目的: 评估在文件名中加入URL的可行性和影响")
    print("=" * 80)

    # 1. 分析当前命名
    current_examples = analyze_current_naming()

    # 2. 提出URL方案
    schemes = propose_url_naming_schemes()

    # 3. 影响分析
    impact = analyze_impact_on_existing_code()

    # 4. 推荐方案
    recommendation = recommend_solution()

    print("\n\n📊 结论")
    print("=" * 60)
    print("✅ 不建议在文件名中直接加入完整URL（会造成颠覆性改动）")
    print("✅ 建议采用映射文件方案（影响最小，效果最好）")
    print("✅ 立即可行的改进：精确匹配 + URL映射文件")
    print("✅ 预计改动量：< 50行代码")
    print("✅ 风险等级：低")

    # 创建示例映射文件
    sample_mapping = {
        "baseline_url_mapping": {
            "tencent_出国销售计划表_20250915_0145_baseline_W39.csv": {
                "url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN",
                "doc_id": "DWEFNU25TemFnZXJN",
                "doc_name": "副本-测试版本-出国销售计划表",
                "download_time": "2025-09-15 01:45:00"
            },
            "tencent_回国销售计划表_20250914_2309_baseline_W39.csv": {
                "url": "https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr",
                "doc_id": "DWGZDZkxpaGVQaURr",
                "doc_name": "副本-测试版本-回国销售计划表",
                "download_time": "2025-09-14 23:09:00"
            }
        }
    }

    # 保存示例映射文件
    mapping_file = "baseline_url_mapping.json"
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(sample_mapping, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已创建示例映射文件: {mapping_file}")

if __name__ == "__main__":
    main()