#!/usr/bin/env python3
"""
添加综合打分文件管理功能到8089端口服务
"""

import os
import json
import glob

# 1. 创建API端点代码
api_endpoint_code = '''
@app.route('/api/comprehensive-files', methods=['GET', 'DELETE'])
def handle_comprehensive_files():
    """处理综合打分文件的管理"""
    try:
        # 获取请求的周数
        from production.core_modules.week_time_manager import WeekTimeManager
        week_manager = WeekTimeManager()
        week_info = week_manager.get_current_week_info()
        current_week = week_info['week_number']
        requested_week = request.args.get('week', type=int, default=current_week)

        # 综合打分文件目录
        scoring_dir = '/root/projects/tencent-doc-manager/scoring_results/comprehensive'

        if request.method == 'GET':
            # 获取指定周的综合打分文件
            files = []
            week_pattern = f'comprehensive_score_W{requested_week:02d}_*.json'
            # 也尝试单数字格式
            alt_pattern = f'comprehensive_score_W{requested_week}_*.json'

            matching_files = glob.glob(os.path.join(scoring_dir, week_pattern))
            matching_files.extend(glob.glob(os.path.join(scoring_dir, alt_pattern)))

            for file_path in matching_files:
                filename = os.path.basename(file_path)
                file_info = {
                    'name': filename,
                    'path': file_path,
                    'size': f'{os.path.getsize(file_path) / 1024:.1f} KB',
                    'modified': datetime.datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).strftime('%Y-%m-%d %H:%M'),
                    'is_realistic': 'realistic' in filename.lower()
                }

                # 尝试读取文件获取表格数量
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        file_info['table_count'] = len(data.get('table_scores', []))
                except:
                    file_info['table_count'] = 0

                files.append(file_info)

            # 按修改时间排序，最新的在前
            files.sort(key=lambda x: x['modified'], reverse=True)

            # 获取所有有综合打分文件的周数
            available_weeks = set()
            all_files = glob.glob(os.path.join(scoring_dir, 'comprehensive_score_W*.json'))

            for file_path in all_files:
                filename = os.path.basename(file_path)
                # 提取周数
                import re
                match = re.search(r'_W(\d+)_', filename)
                if match:
                    week_num = int(match.group(1))
                    available_weeks.add(week_num)

            return jsonify({
                'success': True,
                'files': files,
                'available_weeks': sorted(list(available_weeks)),
                'current_week': current_week,
                'selected_week': requested_week
            })

        elif request.method == 'DELETE':
            # 删除文件（软删除到.deleted文件夹）
            data = request.json
            filename = data.get('filename')

            if not filename:
                return jsonify({'success': False, 'error': '未指定文件名'})

            file_path = os.path.join(scoring_dir, filename)
            if not os.path.exists(file_path):
                return jsonify({'success': False, 'error': '文件不存在'})

            # 创建.deleted文件夹
            deleted_dir = os.path.join(scoring_dir, '.deleted')
            os.makedirs(deleted_dir, exist_ok=True)

            # 移动文件到.deleted文件夹
            import shutil
            deleted_path = os.path.join(deleted_dir, f'{filename}.{int(time.time())}')
            shutil.move(file_path, deleted_path)

            return jsonify({
                'success': True,
                'message': f'文件已删除: {filename}'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/load-comprehensive', methods=['POST'])
def load_comprehensive_as_default():
    """加载综合打分文件作为默认显示"""
    try:
        data = request.json
        week = data.get('week', 37)  # 默认第37周

        scoring_dir = '/root/projects/tencent-doc-manager/scoring_results/comprehensive'
        week_files = glob.glob(f'{scoring_dir}/comprehensive_score_W{week:02d}_*.json')
        if not week_files:
            week_files = glob.glob(f'{scoring_dir}/comprehensive_score_W{week}_*.json')

        if not week_files:
            return jsonify({'success': False, 'error': f'未找到第{week}周的综合打分文件'})

        # 优先选择realistic文件
        realistic_files = [f for f in week_files if 'realistic' in f]
        if realistic_files:
            selected_file = max(realistic_files, key=os.path.getmtime)
        else:
            # 选择表格数量最多的文件
            file_info = []
            for f in week_files:
                try:
                    with open(f, 'r') as fp:
                        data = json.load(fp)
                        table_count = len(data.get('table_scores', []))
                        file_info.append((f, table_count))
                except:
                    file_info.append((f, 0))

            file_info.sort(key=lambda x: x[1], reverse=True)
            selected_file = file_info[0][0] if file_info else week_files[0]

        # 加载文件
        global comprehensive_scoring_data, COMPREHENSIVE_MODE, DATA_SOURCE
        with open(selected_file, 'r', encoding='utf-8') as f:
            comprehensive_scoring_data = json.load(f)
            COMPREHENSIVE_MODE = True
            DATA_SOURCE = 'comprehensive'

            # 保存到临时文件
            with open('/tmp/comprehensive_scoring_data.json', 'w', encoding='utf-8') as tmp_f:
                json.dump(comprehensive_scoring_data, tmp_f)

        return jsonify({
            'success': True,
            'message': f'已加载文件: {os.path.basename(selected_file)}',
            'table_count': len(comprehensive_scoring_data.get('table_scores', []))
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
'''

# 2. 创建前端界面代码
frontend_code = '''
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
                                const week = parseInt(e.target.value);
                                setSelectedCompWeek(week);
                                loadComprehensiveFiles(week);
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

print("综合打分文件管理功能代码已准备就绪。")
print("\n需要添加的内容：")
print("1. API端点 - 在基线文件管理API后添加")
print("2. 前端界面 - 在基线文件管理界面后添加")
print("3. 状态变量 - 在React组件开始处添加")
print("4. 处理函数 - 在loadBaselineFiles函数后添加")

# 保存代码到文件供后续使用
with open('/tmp/comprehensive_api.py', 'w') as f:
    f.write(api_endpoint_code)

with open('/tmp/comprehensive_frontend.jsx', 'w') as f:
    f.write(frontend_code)

print("\n代码已保存到：")
print("- /tmp/comprehensive_api.py (API端点)")
print("- /tmp/comprehensive_frontend.jsx (前端界面)")