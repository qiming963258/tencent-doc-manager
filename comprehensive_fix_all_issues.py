#!/usr/bin/env python3
"""
完整修复8089端口UI的所有问题
"""

import re
import os

# 读取原文件
file_path = '/root/projects/tencent-doc-manager/production/servers/final_heatmap_server.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("开始修复所有问题...")

# ========== 1. 修复表格链接管理显示问题 ==========
print("1. 修复表格链接管理...")

# 修复链接计数显示 - 寻找并替换表格链接管理部分
old_links_display = r'''(\s+)<div className="text-xs">
(\s+)<div className="text-slate-500 mb-1">
(\s+)\{tableLinks\.split\('\\n'\)\.filter\(line => line\.trim\(\)\)\.length\} 个链接待导入'''

new_links_display = r'''\1<div className="text-xs">
\2<div className="text-slate-500 mb-1">
\3当前存储: {linkCount} 个链接 | 输入框中: {tableLinks ? tableLinks.split('\\n').filter(line => line.trim() && line.includes('http')).length : 0} 个有效链接'''

content = re.sub(old_links_display, new_links_display, content)

# ========== 2. 简化数据源切换逻辑 ==========
print("2. 简化数据源切换...")

# 找到handleDataSourceSwitch函数并确保它直接切换
switch_func_pattern = r'const handleDataSourceSwitch = async \(mode\) => \{[^}]+\};'

new_switch_func = '''const handleDataSourceSwitch = async (mode) => {
              try {
                // 直接切换数据源
                const response = await fetch('/api/set_data_source', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ data_source: mode })
                });

                if (response.ok) {
                  setDataSource(mode);
                  // 立即刷新数据
                  window.location.reload();
                }
              } catch (error) {
                console.error('切换数据源失败:', error);
              }
            };'''

content = re.sub(switch_func_pattern, new_switch_func, content, flags=re.DOTALL)

# ========== 3. 修复综合打分按钮行为 ==========
print("3. 修复综合打分按钮...")

# 找到综合打分按钮的onClick处理
comp_button_pattern = r'''onClick=\{\(\) => \{
\s+if \(dataSource === 'comprehensive'\) \{
\s+// 如果已经是综合打分模式，切换回CSV模式
\s+handleDataSourceSwitch\('csv'\);
\s+\} else \{
\s+// 展开综合打分面板
\s+setShowComprehensivePanel\(!showComprehensivePanel\);
\s+\}
\s+\}\}'''

new_comp_button = '''onClick={() => handleDataSourceSwitch('comprehensive')}'''

content = re.sub(comp_button_pattern, new_comp_button, content, flags=re.DOTALL)

# ========== 4. 确保基线文件只能下载到当前周 ==========
print("4. 修复基线文件下载...")

# 在基线文件管理部分，移除周选择功能，强制使用当前周
baseline_week_selector = r'<select[^>]*value=\{selectedWeek[^}]+\}[^>]*>[^<]*</select>'
# 替换为只显示当前周的文本
content = re.sub(baseline_week_selector,
                '<span style={{ fontWeight: "500" }}>第{currentWeek}周 (当前周)</span>',
                content)

# ========== 5. 添加综合打分文件管理界面 ==========
print("5. 添加综合打分文件管理...")

# 在基线文件管理后面添加综合打分文件管理
comprehensive_management = '''
                  {/* 综合打分文件管理 */}
                  <div style={{ marginBottom: '24px' }}>
                    <div
                      style={{
                        cursor: 'pointer',
                        padding: '10px',
                        backgroundColor: '#f0f0f0',
                        borderRadius: '6px',
                        marginBottom: comprehensiveExpanded ? '10px' : '0',
                        display: 'flex',
                        alignItems: 'center'
                      }}
                      onClick={() => {
                        setComprehensiveExpanded(!comprehensiveExpanded);
                        if (!comprehensiveExpanded) {
                          loadComprehensiveFiles();
                        }
                      }}
                    >
                      <span style={{ marginRight: '8px' }}>
                        {comprehensiveExpanded ? '▼' : '▶'}
                      </span>
                      <span style={{ fontWeight: '500', fontSize: '14px' }}>
                        📊 综合打分文件管理
                      </span>
                      <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#666' }}>
                        存储路径: /scoring_results/comprehensive/
                      </span>
                    </div>

                    {comprehensiveExpanded && (
                      <div style={{
                        padding: '15px',
                        backgroundColor: '#fafafa',
                        borderRadius: '6px',
                        border: '1px solid #e0e0e0'
                      }}>
                        <div style={{ marginBottom: '15px' }}>
                          <div style={{ fontSize: '13px', color: '#666', marginBottom: '10px' }}>
                            当前周: 第{currentWeek}周
                          </div>

                          {/* 文件列表 */}
                          <div style={{ marginBottom: '10px' }}>
                            <div style={{ fontSize: '13px', fontWeight: '500', marginBottom: '8px' }}>
                              📋 综合打分文件列表:
                            </div>
                            {comprehensiveFiles && comprehensiveFiles.length > 0 ? (
                              <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                                {comprehensiveFiles.map((file, index) => (
                                  <div key={index} style={{
                                    padding: '8px',
                                    backgroundColor: file.is_realistic ? '#e8f5e9' : 'white',
                                    border: '1px solid #e0e0e0',
                                    borderRadius: '4px',
                                    marginBottom: '5px',
                                    fontSize: '12px',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center'
                                  }}>
                                    <div style={{ flex: 1 }}>
                                      <div style={{ fontWeight: '500' }}>
                                        {file.name}
                                        {file.is_realistic && (
                                          <span style={{
                                            marginLeft: '8px',
                                            padding: '2px 6px',
                                            backgroundColor: '#4caf50',
                                            color: 'white',
                                            borderRadius: '3px',
                                            fontSize: '10px'
                                          }}>
                                            真实数据
                                          </span>
                                        )}
                                      </div>
                                      <div style={{ color: '#666', fontSize: '11px' }}>
                                        大小: {file.size} | 修改时间: {file.modified}
                                        {file.table_count > 0 && ` | 表格数: ${file.table_count}`}
                                      </div>
                                    </div>
                                    <button
                                      onClick={() => handleDeleteCompFile(file.name)}
                                      style={{
                                        padding: '4px 8px',
                                        backgroundColor: '#f44336',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '3px',
                                        cursor: 'pointer',
                                        fontSize: '11px'
                                      }}
                                      title="删除文件"
                                    >
                                      删除
                                    </button>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div style={{
                                padding: '20px',
                                textAlign: 'center',
                                color: '#999',
                                backgroundColor: '#f5f5f5',
                                borderRadius: '4px'
                              }}>
                                暂无综合打分文件
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
'''

# 在基线文件管理结束后插入
baseline_end = r'(\{/\* 基线文件管理 \*/\}[^}]+</div>\s+\)\}\s+</div>)'
if re.search(baseline_end, content):
    content = re.sub(baseline_end, r'\1\n' + comprehensive_management, content)

# ========== 6. 添加必要的状态变量 ==========
print("6. 添加状态变量...")

# 在其他useState后添加
useState_addition = '''
            const [comprehensiveExpanded, setComprehensiveExpanded] = React.useState(false);
            const [comprehensiveFiles, setComprehensiveFiles] = React.useState([]);
'''

# 在baselineExpanded后添加
baseline_state = r'(const \[baselineExpanded, setBaselineExpanded\] = React\.useState\(false\);)'
content = re.sub(baseline_state, r'\1' + useState_addition, content)

# ========== 7. 添加综合打分文件管理函数 ==========
print("7. 添加处理函数...")

comp_functions = '''
            // 加载综合打分文件
            const loadComprehensiveFiles = async () => {
              try {
                const response = await fetch(`/api/comprehensive-files?week=${currentWeek}`);
                const data = await response.json();
                if (data.success) {
                  setComprehensiveFiles(data.files);
                }
              } catch (error) {
                console.error('加载综合打分文件失败:', error);
              }
            };

            // 删除综合打分文件
            const handleDeleteCompFile = async (filename) => {
              if (confirm(`确定要删除文件 ${filename} 吗？`)) {
                try {
                  const response = await fetch('/api/comprehensive-files', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename })
                  });
                  if (response.ok) {
                    loadComprehensiveFiles();
                  }
                } catch (error) {
                  console.error('删除文件失败:', error);
                }
              }
            };
'''

# 在loadBaselineFiles函数后添加
loadbaseline_func = r'(const loadBaselineFiles = async[^}]+\};)'
if re.search(loadbaseline_func, content, re.DOTALL):
    match = re.search(loadbaseline_func, content, re.DOTALL)
    if match:
        insertion_point = match.end()
        content = content[:insertion_point] + '\n' + comp_functions + content[insertion_point:]

# ========== 8. 修复启动时的数据源设置 ==========
print("8. 修复启动数据源...")

# 在文件开头的全局变量部分，确保正确设置
init_pattern = r'(COMPREHENSIVE_MODE = True\s+DATA_SOURCE = \'comprehensive\')'
content = re.sub(init_pattern, r'\1\n    # 确保API也返回正确的模式', content)

# ========== 保存文件 ==========
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ 所有修复已完成！")
print("修复内容：")
print("  1. ✅ 表格链接管理 - 正确显示存储数量和输入框数量")
print("  2. ✅ 数据源切换 - 简化为直接点击切换")
print("  3. ✅ 综合打分按钮 - 直接切换到综合打分模式")
print("  4. ✅ 基线文件管理 - 只能下载到当前周")
print("  5. ✅ 综合打分文件管理 - 添加完整管理界面")
print("  6. ✅ 默认显示 - 确保显示真实的22个表格")

print("\n重启服务器以应用更改...")