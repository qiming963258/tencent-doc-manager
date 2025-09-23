#!/usr/bin/env python3
"""
修复8093工作流的基线文件匹配问题
让每个文档使用自己对应的基线文件，而不是都用同一个
"""

import re
import os

def extract_doc_name_from_url(url: str) -> str:
    """从腾讯文档URL提取文档名称"""
    # 从download_config.json匹配文档名
    import json
    config_path = '/root/projects/tencent-doc-manager/config/download_config.json'

    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        doc_id = url.split('/')[-1].split('?')[0]
        for doc in config.get('document_links', []):
            if doc.get('id') == doc_id:
                full_name = doc['name']
                # 去掉前缀，保留核心名称
                doc_name = full_name.replace('副本-测试版本-', '').replace('测试版本-', '')
                return doc_name

    return None

def find_matching_baseline(doc_name: str, baseline_files: list) -> str:
    """根据文档名称找到匹配的基线文件"""
    if not doc_name or not baseline_files:
        return None

    # 尝试精确匹配
    for baseline in baseline_files:
        basename = os.path.basename(baseline)
        # 检查基线文件名是否包含文档名
        if doc_name in basename:
            print(f"✅ 为文档 '{doc_name}' 找到匹配基线: {basename}")
            return baseline

    # 如果没有精确匹配，尝试模糊匹配
    doc_keywords = doc_name.replace('-', '').replace('_', '').lower()
    for baseline in baseline_files:
        basename = os.path.basename(baseline).lower()
        if any(keyword in basename for keyword in doc_keywords.split()):
            print(f"✅ 为文档 '{doc_name}' 找到模糊匹配基线: {os.path.basename(baseline)}")
            return baseline

    print(f"⚠️ 未找到文档 '{doc_name}' 的匹配基线，使用默认")
    return None

def fix_baseline_matching():
    """修复production_integrated_test_system_8093.py的基线匹配逻辑"""

    file_path = '/root/projects/tencent-doc-manager/production_integrated_test_system_8093.py'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 找到需要替换的代码段
    old_code = """                    baseline_files, baseline_desc = week_manager.find_baseline_files()
                    if baseline_files:
                        baseline_file = baseline_files[0]  # 使用最新的基线文件"""

    new_code = """                    baseline_files, baseline_desc = week_manager.find_baseline_files()
                    if baseline_files:
                        # 从目标URL提取文档名称以匹配正确的基线
                        doc_name = None
                        if target_url:
                            import json
                            config_path = '/root/projects/tencent-doc-manager/config/download_config.json'
                            if os.path.exists(config_path):
                                with open(config_path, 'r', encoding='utf-8') as cf:
                                    config = json.load(cf)
                                doc_id = target_url.split('/')[-1].split('?')[0]
                                for doc in config.get('document_links', []):
                                    if doc.get('id') == doc_id:
                                        full_name = doc['name']
                                        doc_name = full_name.replace('副本-测试版本-', '').replace('测试版本-', '')
                                        workflow_state.add_log(f"📝 处理文档: {doc_name}")
                                        break

                        # 根据文档名匹配基线文件
                        matched_baseline = None
                        if doc_name:
                            for baseline in baseline_files:
                                basename = os.path.basename(baseline)
                                if doc_name in basename:
                                    matched_baseline = baseline
                                    workflow_state.add_log(f"✅ 匹配基线: {basename}")
                                    break

                        baseline_file = matched_baseline if matched_baseline else baseline_files[0]"""

    # 替换两处使用baseline_files[0]的地方
    content = content.replace(old_code, new_code)

    # 还有第二处在603行附近
    old_code2 = """                    baseline_files, baseline_desc = week_manager.find_baseline_files()
                    if baseline_files:
                        baseline_file = baseline_files[0]  # 使用最新的基线文件"""

    new_code2 = """                    baseline_files, baseline_desc = week_manager.find_baseline_files()
                    if baseline_files:
                        # 从目标URL提取文档名称以匹配正确的基线
                        doc_name = None
                        if target_url:
                            import json
                            config_path = '/root/projects/tencent-doc-manager/config/download_config.json'
                            if os.path.exists(config_path):
                                with open(config_path, 'r', encoding='utf-8') as cf:
                                    config = json.load(cf)
                                doc_id = target_url.split('/')[-1].split('?')[0]
                                for doc in config.get('document_links', []):
                                    if doc.get('id') == doc_id:
                                        full_name = doc['name']
                                        doc_name = full_name.replace('副本-测试版本-', '').replace('测试版本-', '')
                                        workflow_state.add_log(f"📝 处理文档: {doc_name}")
                                        break

                        # 根据文档名匹配基线文件
                        matched_baseline = None
                        if doc_name:
                            for baseline in baseline_files:
                                basename = os.path.basename(baseline)
                                if doc_name in basename:
                                    matched_baseline = baseline
                                    workflow_state.add_log(f"✅ 匹配基线: {basename}")
                                    break

                        baseline_file = matched_baseline if matched_baseline else baseline_files[0]"""

    content = content.replace(old_code2, new_code2)

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ 已修复基线匹配逻辑")
    print("现在每个文档将使用对应的基线文件进行对比")

if __name__ == "__main__":
    fix_baseline_matching()