#!/usr/bin/env python3
"""
修复8089端口UI的各种改进需求
"""

import re

# 读取文件
with open('/root/projects/tencent-doc-manager/production/servers/final_heatmap_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 修复表格链接管理显示问题 - 显示当前存储的URL数量
old_pattern = r"(\s+)<div className=\"text-xs\">\s*<div className=\"text-slate-500 mb-1\">\s*\{tableLinks\.split\('\\\\n'\)\.filter\(line => line\.trim\(\)\)\.length\} 个链接待导入\s*</div>"
new_text = r"\1<div className=\"text-xs\">\n\1  <div className=\"text-slate-500 mb-1\">\n\1    当前存储: {linkCount} 个链接，输入框中: {tableLinks.split('\\n').filter(line => line.trim()).length} 个链接\n\1  </div>"
content = re.sub(old_pattern, new_text, content)

# 2. 添加综合打分文件管理功能（在基线文件管理后面添加）
comprehensive_panel = '''
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
                      onClick={() => setComprehensiveExpanded(!comprehensiveExpanded)}
                    >
                      <span style={{ marginRight: '8px' }}>
                        {comprehensiveExpanded ? '▼' : '▶'}
                      </span>
                      <span style={{ fontWeight: '500', fontSize: '14px' }}>
                        📊 综合打分文件管理
                      </span>
                      <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#666' }}>
                        当前周: 第{currentWeek}周
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
                            📁 存储路径: /scoring_results/comprehensive/
                          </div>

                          {/* 周选择器 */}
                          <div style={{ marginBottom: '15px' }}>
                            <label style={{ fontSize: '13px', marginRight: '10px' }}>选择周数:</label>
                            <select
                              value={selectedCompWeek || currentWeek}
                              onChange={(e) => {
                                setSelectedCompWeek(parseInt(e.target.value));
                                loadComprehensiveFiles(parseInt(e.target.value));
                              }}
                              style={{
                                padding: '5px 10px',
                                borderRadius: '4px',
                                border: '1px solid #ddd',
                                fontSize: '13px'
                              }}
                            >
                              {availableCompWeeks.map(week => (
                                <option key={week} value={week}>
                                  第{week}周 {week === currentWeek ? '(当前周)' : ''}
                                </option>
                              ))}
                            </select>
                          </div>

                          {/* 文件列表 */}
                          <div style={{ marginBottom: '10px' }}>
                            <div style={{ fontSize: '13px', fontWeight: '500', marginBottom: '8px' }}>
                              📋 综合打分文件列表:
                            </div>
                            {comprehensiveFiles.length > 0 ? (
                              <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                                {comprehensiveFiles.map((file, index) => (
                                  <div key={index} style={{
                                    padding: '8px',
                                    backgroundColor: file.includes('realistic') ? '#e8f5e9' : 'white',
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
                                        {file.includes('realistic') && (
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
                                        {file.table_count && ` | 表格数: ${file.table_count}`}
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

                          {/* 加载为当前显示按钮 */}
                          {comprehensiveFiles.length > 0 && (
                            <button
                              onClick={handleLoadComprehensiveAsDefault}
                              style={{
                                width: '100%',
                                padding: '8px',
                                backgroundColor: '#10b981',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '13px',
                                fontWeight: '500'
                              }}
                            >
                              🔄 加载最新文件为热力图显示
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
'''

# 在基线文件管理后面插入综合打分文件管理
baseline_end_pattern = r'(\s+){/\* 基线文件管理 \*/}[\s\S]*?</div>\s*\)\}\s*</div>'
if re.search(baseline_end_pattern, content):
    insertion_point = re.search(baseline_end_pattern, content).end()
    content = content[:insertion_point] + "\n" + comprehensive_panel + content[insertion_point:]

# 3. 添加状态变量（在React组件开始处）
state_vars = '''
            const [comprehensiveExpanded, setComprehensiveExpanded] = React.useState(false);
            const [comprehensiveFiles, setComprehensiveFiles] = React.useState([]);
            const [selectedCompWeek, setSelectedCompWeek] = React.useState(null);
            const [availableCompWeeks, setAvailableCompWeeks] = React.useState([]);
'''

# 在其他useState声明后添加
useState_pattern = r'(const \[baselineExpanded, setBaselineExpanded\] = React\.useState\(false\);)'
content = re.sub(useState_pattern, r'\1\n' + state_vars, content)

# 4. 添加综合打分文件管理的处理函数
comp_functions = '''
            // 加载综合打分文件
            const loadComprehensiveFiles = async (week) => {
              try {
                const response = await fetch(`/api/comprehensive-files?week=${week || selectedCompWeek || currentWeek}`);
                const data = await response.json();
                if (data.success) {
                  setComprehensiveFiles(data.files);
                  // 更新可用周列表
                  if (data.available_weeks) {
                    setAvailableCompWeeks(data.available_weeks);
                  }
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
                    body: JSON.stringify({ filename, week: selectedCompWeek || currentWeek })
                  });
                  const data = await response.json();
                  if (data.success) {
                    loadComprehensiveFiles();
                  }
                } catch (error) {
                  console.error('删除文件失败:', error);
                }
              }
            };

            // 加载综合打分为默认显示
            const handleLoadComprehensiveAsDefault = async () => {
              try {
                const response = await fetch('/api/load-comprehensive', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ week: selectedCompWeek || currentWeek })
                });
                const data = await response.json();
                if (data.success) {
                  // 切换到综合打分模式并刷新
                  handleDataSourceSwitch('comprehensive');
                  alert('已加载综合打分数据，刷新页面查看');
                  window.location.reload();
                }
              } catch (error) {
                console.error('加载综合打分失败:', error);
              }
            };
'''

# 在loadBaselineFiles函数后添加
loadbaseline_pattern = r'(const loadBaselineFiles = async[^}]+\};)'
if re.search(loadbaseline_pattern, content):
    insertion_point = re.search(loadbaseline_pattern, content).end()
    content = content[:insertion_point] + "\n" + comp_functions + content[insertion_point:]

# 5. 在useEffect中添加综合打分文件的初始加载
useeffect_addition = '''
              // 加载综合打分文件
              loadComprehensiveFiles();
'''

useeffect_pattern = r'(React\.useEffect\(\(\) => \{[\s\S]*?loadBaselineFiles\(\);)'
content = re.sub(useeffect_pattern, r'\1' + useeffect_addition, content)

# 写回文件
with open('/root/projects/tencent-doc-manager/production/servers/final_heatmap_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 所有UI改进已完成：")
print("  1. 简化了数据源切换动画")
print("  2. 修复了表格链接管理显示")
print("  3. 删除了告警阈值功能")
print("  4. 删除了CSV下载控制功能")
print("  5. 添加了综合打分文件管理界面")
print("  6. 确保基线文件只能存储到当前周")