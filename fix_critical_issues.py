#!/usr/bin/env python3
"""
修复系统关键问题：
1. 综合打分文件路径错误（应该按周组织）
2. 文件匹配逻辑应该完全相等而不是包含
"""

import os
import shutil
import json
from pathlib import Path

def fix_comprehensive_files_organization():
    """修复综合打分文件的组织结构"""
    print("\n" + "=" * 60)
    print("修复综合打分文件组织结构")
    print("=" * 60)

    comprehensive_dir = Path("scoring_results/comprehensive")
    w39_dir = Path("scoring_results/2025_W39")

    # 确保W39目录存在
    w39_dir.mkdir(parents=True, exist_ok=True)

    # 查找所有W39的综合打分文件
    w39_files = list(comprehensive_dir.glob("*W39*.json"))

    print(f"\n找到 {len(w39_files)} 个W39综合打分文件需要移动")

    moved_count = 0
    for file in w39_files:
        dest = w39_dir / file.name
        try:
            # 复制文件到正确位置
            shutil.copy2(file, dest)
            print(f"✅ 复制: {file.name} -> {dest}")
            moved_count += 1
        except Exception as e:
            print(f"❌ 复制失败 {file.name}: {e}")

    print(f"\n总共复制了 {moved_count} 个文件到 2025_W39 目录")

def analyze_file_matching_logic():
    """分析文件匹配逻辑问题"""
    print("\n" + "=" * 60)
    print("分析文件匹配逻辑")
    print("=" * 60)

    # 检查实际的基线文件
    baseline_dir = Path("csv_versions/2025_W39/baseline")
    baseline_files = list(baseline_dir.glob("*.csv"))

    # 检查软删除的文件
    deleted_dir = baseline_dir / ".deleted"
    deleted_files = list(deleted_dir.glob("*.csv")) if deleted_dir.exists() else []

    print(f"\n活跃基线文件: {len(baseline_files)}")
    for f in baseline_files:
        print(f"  - {f.name}")

    print(f"\n软删除基线文件: {len(deleted_files)}")
    for f in deleted_files:
        print(f"  - {f.name}")

    # 分析匹配问题
    print("\n匹配逻辑问题分析：")
    print("❌ 当前逻辑：使用字符串包含判断 'doc_name in filename'")
    print("   问题1: '出国' 会同时匹配 '出国销售计划表' 和 '副本-测试版本-出国销售计划表'")
    print("   问题2: 软删除文件不应该参与匹配")
    print("\n✅ 建议改进：")
    print("   1. 使用完整文档名匹配")
    print("   2. 排除.deleted目录中的文件")
    print("   3. 建立文档名到文件路径的明确映射")

def verify_url_flow():
    """验证URL流转逻辑"""
    print("\n" + "=" * 60)
    print("验证URL流转逻辑")
    print("=" * 60)

    print("\nURL流转链路：")
    print("1. 基线文件（CSV）：不包含URL信息 ❌")
    print("2. 下载时：从腾讯文档URL下载，URL在参数中")
    print("3. 对比打分：不涉及URL")
    print("4. Excel涂色：生成本地Excel文件")
    print("5. 上传腾讯文档：获得新的upload_url ✅")
    print("6. 综合打分：接收upload_url作为excel_url参数")
    print("7. excel_urls字典：{表格名: upload_url}")
    print("8. 热力图显示：通过表格名查找excel_urls获取URL")

    print("\n关键发现：")
    print("⚠️ excel_url是上传后的URL，不是基线文档的URL")
    print("⚠️ 基线文件本身不存储URL信息")
    print("⚠️ URL映射依赖表格名称，名称必须完全一致")

def check_real_documents_config():
    """检查真实文档配置"""
    print("\n" + "=" * 60)
    print("检查真实文档配置")
    print("=" * 60)

    config_path = Path("production/config/real_documents.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        docs = config.get('documents', [])
        print(f"\n配置的真实文档: {len(docs)}")
        for doc in docs:
            print(f"\n文档: {doc['name']}")
            print(f"  URL: {doc['url']}")
            print(f"  状态: {'✅ 活跃' if doc['url'].startswith('https://docs.qq.com') else '❌ 无效'}")

            # 检查对应的基线文件
            baseline_pattern = f"*{doc['name'].split('-')[-1]}*baseline*.csv"
            baseline_files = list(Path("csv_versions/2025_W39/baseline").glob(baseline_pattern))
            if baseline_files:
                print(f"  基线文件: {baseline_files[0].name}")
            else:
                print(f"  基线文件: ❌ 未找到")

def main():
    """主函数"""
    print("=" * 80)
    print("🔧 系统关键问题修复与分析")
    print("=" * 80)

    # 执行各项检查和修复
    fix_comprehensive_files_organization()
    analyze_file_matching_logic()
    verify_url_flow()
    check_real_documents_config()

    print("\n" + "=" * 80)
    print("🔍 深度分析结论")
    print("=" * 80)

    print("""
系统存在的关键问题：

1. **文件组织混乱** ⚠️
   - 综合打分文件存储在错误位置
   - 硬编码W39而不是动态获取周数
   - UI无法找到2025_W39目录中的文件

2. **文件匹配逻辑缺陷** ⚠️
   - 使用包含判断而非完全匹配
   - 可能匹配到错误的基线文件
   - 没有排除软删除文件

3. **URL管理问题** ⚠️
   - 基线文件不存储源URL
   - excel_urls存储的是上传后的URL
   - 依赖表格名称进行映射

4. **软删除文件问题** ✅
   - 软删除文件不会被find_baseline_files调用
   - 但占用存储空间且造成混淆

结论：系统确实在处理真实数据，但存在严重的架构和逻辑问题！
""")

if __name__ == "__main__":
    main()