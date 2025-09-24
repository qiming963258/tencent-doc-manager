#!/usr/bin/env python3
"""
改进的文件匹配逻辑实现
使用精确匹配替代包含匹配，并创建URL映射文件
"""
import os
import re
import json
from datetime import datetime
from pathlib import Path

def extract_doc_name_from_filename(filename):
    """从文件名中精确提取文档名称

    Args:
        filename: 文件名，如 tencent_出国销售计划表_20250915_0145_baseline_W39.csv

    Returns:
        文档名称，如 出国销售计划表
    """
    basename = os.path.basename(filename)

    # 匹配格式：tencent_{文档名}_{时间戳}_{版本}_W{周}.{扩展名}
    match = re.search(r'^tencent_(.+?)_\d{8}_\d{4}_(baseline|midweek)_W\d+\.\w+$', basename)
    if match:
        return match.group(1)

    # 备用匹配（如果格式不完全标准）
    match = re.search(r'^tencent_(.+?)_\d{8}_\d{4}', basename)
    if match:
        return match.group(1)

    return None

def find_exact_matching_baseline(doc_name, baseline_files):
    """精确匹配基线文件

    Args:
        doc_name: 要匹配的文档名称
        baseline_files: 基线文件列表

    Returns:
        匹配的基线文件路径，如果没有匹配则返回None
    """
    for baseline in baseline_files:
        baseline_doc_name = extract_doc_name_from_filename(baseline)

        # 精确匹配
        if baseline_doc_name and baseline_doc_name == doc_name:
            return baseline

    return None

class BaselineURLMapper:
    """基线文件URL映射管理器"""

    def __init__(self):
        self.mapping_file = Path('/root/projects/tencent-doc-manager/baseline_url_mapping.json')
        self.mapping = self.load_mapping()

    def load_mapping(self):
        """加载映射文件"""
        if self.mapping_file.exists():
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_mapping(self):
        """保存映射文件"""
        self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            json.dump(self.mapping, f, ensure_ascii=False, indent=2)

    def add_baseline_mapping(self, filename, url, doc_name=None):
        """添加基线文件到URL的映射

        Args:
            filename: 基线文件名
            url: 腾讯文档URL
            doc_name: 文档名称（可选）
        """
        basename = os.path.basename(filename)

        if doc_name is None:
            doc_name = extract_doc_name_from_filename(filename)

        self.mapping[basename] = {
            "url": url,
            "doc_name": doc_name,
            "doc_id": self._extract_doc_id(url),
            "added_time": datetime.now().isoformat(),
            "full_path": str(filename)
        }

        self.save_mapping()

    def get_url_for_baseline(self, filename):
        """获取基线文件对应的URL"""
        basename = os.path.basename(filename)
        if basename in self.mapping:
            return self.mapping[basename].get('url')
        return None

    def get_baseline_for_url(self, url):
        """根据URL查找对应的基线文件"""
        for filename, info in self.mapping.items():
            if info.get('url') == url:
                return filename
        return None

    def _extract_doc_id(self, url):
        """从URL提取文档ID"""
        if 'docs.qq.com/sheet/' in url:
            return url.split('/')[-1]
        return None

    def cleanup_deleted_files(self):
        """清理已删除文件的映射"""
        to_remove = []
        for filename, info in self.mapping.items():
            full_path = info.get('full_path')
            if full_path and not os.path.exists(full_path):
                to_remove.append(filename)

        for filename in to_remove:
            del self.mapping[filename]
            print(f"清理已删除文件的映射: {filename}")

        if to_remove:
            self.save_mapping()

def apply_improved_matching_to_8093():
    """应用改进的匹配逻辑到8093工作流"""

    # 读取8093文件
    file_path = '/root/projects/tencent-doc-manager/production_integrated_test_system_8093.py'

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找需要替换的代码段
    old_matching = """if doc_name in basename:
                                    matched_baseline = baseline"""

    new_matching = """# 使用精确匹配
                                baseline_doc_name = extract_doc_name_from_filename(baseline)
                                if baseline_doc_name and baseline_doc_name == doc_name:
                                    matched_baseline = baseline"""

    if old_matching in content:
        # 添加必要的导入
        if 'def extract_doc_name_from_filename' not in content:
            # 在文件开头添加函数定义
            import_section = """
# 精确匹配函数
def extract_doc_name_from_filename(filename):
    \"\"\"从文件名中精确提取文档名称\"\"\"
    import re
    basename = os.path.basename(filename)
    match = re.search(r'^tencent_(.+?)_\\d{8}_\\d{4}_(baseline|midweek)_W\\d+\\.\\w+$', basename)
    if match:
        return match.group(1)
    match = re.search(r'^tencent_(.+?)_\\d{8}_\\d{4}', basename)
    if match:
        return match.group(1)
    return None

"""
            # 在第一个函数定义前插入
            content = content.replace('def main():', import_section + 'def main():', 1)

        # 替换匹配逻辑
        content = content.replace(old_matching, new_matching)

        # 保存修改
        backup_path = file_path + '.backup_before_matching_fix'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 已应用精确匹配逻辑到 {file_path}")
        print(f"✅ 备份保存在: {backup_path}")
    else:
        print("⚠️ 未找到需要替换的匹配逻辑，可能已经修复")

def test_improved_matching():
    """测试改进的匹配逻辑"""
    print("\n🧪 测试改进的匹配逻辑")
    print("=" * 60)

    # 测试文件名
    test_files = [
        "tencent_出国销售计划表_20250915_0145_baseline_W39.csv",
        "tencent_回国销售计划表_20250914_2309_baseline_W39.csv",
        "tencent_小红书部门_20250915_0146_baseline_W39.csv"
    ]

    # 测试提取文档名
    print("\n1. 测试文档名提取:")
    for file in test_files:
        doc_name = extract_doc_name_from_filename(file)
        print(f"  {file}")
        print(f"  → 文档名: {doc_name}")

    # 测试精确匹配
    print("\n2. 测试精确匹配:")
    baseline_files = test_files

    test_cases = [
        ("出国销售计划表", "应该匹配第1个文件"),
        ("出国", "不应该匹配（非完全匹配）"),
        ("小红书部门", "应该匹配第3个文件"),
        ("小红书", "不应该匹配（非完全匹配）")
    ]

    for doc_name, expected in test_cases:
        matched = find_exact_matching_baseline(doc_name, baseline_files)
        if matched:
            print(f"  '{doc_name}' → 匹配: {os.path.basename(matched)}")
        else:
            print(f"  '{doc_name}' → 无匹配")
        print(f"    预期: {expected}")

    # 测试URL映射
    print("\n3. 测试URL映射:")
    mapper = BaselineURLMapper()

    # 添加映射
    mapper.add_baseline_mapping(
        test_files[0],
        "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN"
    )

    # 获取URL
    url = mapper.get_url_for_baseline(test_files[0])
    print(f"  获取URL: {url}")

    # 反向查找
    baseline = mapper.get_baseline_for_url(url)
    print(f"  反向查找: {baseline}")

    print("\n✅ 测试完成")

def main():
    """主函数"""
    print("🔧 改进的文件匹配逻辑实现")
    print("=" * 80)

    # 1. 测试新逻辑
    test_improved_matching()

    # 2. 应用到8093工作流
    print("\n📝 应用到8093工作流:")
    apply_improved_matching_to_8093()

    # 3. 清理无效映射
    print("\n🧹 清理无效映射:")
    mapper = BaselineURLMapper()
    mapper.cleanup_deleted_files()

    print("\n✅ 所有任务完成")

if __name__ == "__main__":
    main()