#!/usr/bin/env python3
"""
简化版原版UI测试服务器
"""

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import json
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)

# 加载测试数据
try:
    with open('quick_visualization_data.json', 'r', encoding='utf-8') as f:
        viz_data = json.load(f)
    original_df = pd.read_csv('enterprise_test_original.csv', encoding='utf-8-sig')
    print("✅ 数据加载成功")
except Exception as e:
    print(f"❌ 数据加载失败: {e}")
    viz_data = None

# 简化版HTML模板
SIMPLE_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>表格变更风险热力图 - 简化版</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f8fafc;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            padding: 30px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e2e8f0;
        }
        .title {
            font-size: 32px;
            color: #1e293b;
            margin: 0;
            font-weight: 300;
        }
        .subtitle {
            color: #64748b;
            margin: 10px 0;
            font-size: 14px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        .stat-number {
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .stat-label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }
        .stat-desc {
            font-size: 10px;
            color: #64748b;
        }
        .l1 { color: #dc2626; }
        .l2 { color: #ea580c; }
        .l3 { color: #16a34a; }
        
        .heatmap-container {
            overflow-x: auto;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            margin: 30px 0;
        }
        .heatmap-table {
            width: 100%;
            border-collapse: collapse;
            min-width: 1000px;
        }
        .heatmap-table th,
        .heatmap-table td {
            border: 1px solid #e2e8f0;
            padding: 8px;
            text-align: center;
            font-size: 11px;
        }
        .heatmap-table th {
            background: #f1f5f9;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        .row-header {
            background: #f8fafc !important;
            font-weight: 500;
            text-align: left !important;
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .risk-cell {
            transition: transform 0.2s;
            cursor: pointer;
        }
        .risk-cell:hover {
            transform: scale(1.1);
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #64748b;
        }
        .api-status {
            margin: 20px 0;
            padding: 15px;
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 6px;
        }
        .button {
            padding: 8px 16px;
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
        }
        .button:hover {
            background: #2563eb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">📊 表格变更风险热力图</h1>
            <p class="subtitle">基于端到端测试数据 • 实时风险分析 • 智能排序</p>
        </div>
        
        <div class="api-status">
            <strong>🔄 数据加载状态:</strong> <span id="status">检查中...</span>
            <button class="button" onclick="loadData()">刷新数据</button>
            <button class="button" onclick="testAPI()">测试API</button>
        </div>
        
        <div id="stats-container">
            <div class="loading">正在加载统计数据...</div>
        </div>
        
        <div id="heatmap-container">
            <div class="loading">正在加载热力图数据...</div>
        </div>
        
        <div id="debug-info" style="margin-top: 30px; padding: 15px; background: #f1f5f9; border-radius: 6px; font-family: monospace; font-size: 12px;"></div>
    </div>

    <script>
        // 全局数据存储
        let apiData = {
            stats: {},
            heatmap: {},
            status: {}
        };
        
        // 状态更新函数
        function updateStatus(message, isError = false) {
            const statusEl = document.getElementById('status');
            statusEl.textContent = message;
            statusEl.style.color = isError ? '#dc2626' : '#16a34a';
        }
        
        // 调试信息显示
        function updateDebugInfo(info) {
            document.getElementById('debug-info').innerHTML = 
                '<strong>调试信息:</strong><br>' + 
                JSON.stringify(info, null, 2).replace(/\\n/g, '<br>').replace(/ /g, '&nbsp;');
        }
        
        // 测试API连接
        async function testAPI() {
            try {
                updateStatus('测试API连接中...');
                
                const response = await fetch('/api/status');
                const data = await response.json();
                
                updateDebugInfo({
                    'API状态': '正常',
                    '响应数据': data,
                    '数据加载': data.data_loaded ? '成功' : '失败',
                    '表格数量': data.tables_count,
                    '修改数量': data.modifications_count
                });
                
                updateStatus('API连接正常 ✅');
                return data;
            } catch (error) {
                updateStatus('API连接失败: ' + error.message, true);
                updateDebugInfo({
                    '错误': error.message,
                    '错误类型': error.name,
                    '时间': new Date().toISOString()
                });
                return null;
            }
        }
        
        // 加载统计数据
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                apiData.stats = stats;
                
                document.getElementById('stats-container').innerHTML = `
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number l1">${stats.criticalModifications || 0}</div>
                            <div class="stat-label l1">严重修改</div>
                            <div class="stat-desc">L1禁止修改</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number l2">${stats.L2Modifications || 0}</div>
                            <div class="stat-label l2">异常修改</div>
                            <div class="stat-desc">L2需要审核</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number l3">${stats.L3Modifications || 0}</div>
                            <div class="stat-label l3">常规修改</div>
                            <div class="stat-desc">L3可自由编辑</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${stats.totalModifications || 0}</div>
                            <div class="stat-label">总修改数</div>
                            <div class="stat-desc">所有变更</div>
                        </div>
                    </div>
                    <div style="text-align: center; margin: 20px 0; padding: 15px; background: #f0f9ff; border-radius: 6px;">
                        <strong>📊 详细统计:</strong><br>
                        <span>修改最多的列: <strong style="color: #2563eb;">${stats.mostModifiedColumn || '无'}</strong></span><br>
                        <span>修改最多的表格: <strong style="color: #2563eb;">${stats.mostModifiedTable || '无'}</strong></span>
                    </div>
                `;
                
                return true;
            } catch (error) {
                document.getElementById('stats-container').innerHTML = 
                    '<div class="loading" style="color: #dc2626;">统计数据加载失败: ' + error.message + '</div>';
                return false;
            }
        }
        
        // 加载热力图数据
        async function loadHeatmap() {
            try {
                const response = await fetch('/api/heatmap');
                const heatmapData = await response.json();
                apiData.heatmap = heatmapData;
                
                // 构建热力图表格
                let tableHTML = `
                    <div class="heatmap-container">
                        <table class="heatmap-table">
                            <thead>
                                <tr>
                                    <th class="row-header">表格名称</th>
                `;
                
                // 添加列标题
                for (let i = 0; i < heatmapData.columnNames.length; i++) {
                    const colName = heatmapData.columnNames[i];
                    tableHTML += `<th title="${colName}">${colName.length > 4 ? colName.substring(0, 4) + '...' : colName}</th>`;
                }
                
                tableHTML += '</tr></thead><tbody>';
                
                // 添加数据行
                for (let y = 0; y < heatmapData.data.length; y++) {
                    const tableName = heatmapData.tableNames[y] || '表格' + (y + 1);
                    tableHTML += `<tr><td class="row-header" title="${tableName}">${tableName.length > 15 ? tableName.substring(0, 15) + '...' : tableName}</td>`;
                    
                    for (let x = 0; x < heatmapData.data[y].length; x++) {
                        const value = heatmapData.data[y][x];
                        const intensity = Math.floor(value * 100);
                        
                        let bgColor = '#ffffff';
                        let textColor = '#333333';
                        
                        if (value > 0) {
                            if (value > 0.8) {
                                bgColor = '#dc2626'; // 高风险-红色
                                textColor = 'white';
                            } else if (value > 0.6) {
                                bgColor = '#ea580c'; // 中高风险-橙红
                                textColor = 'white';
                            } else if (value > 0.4) {
                                bgColor = '#f59e0b'; // 中等风险-橙色
                                textColor = 'white';
                            } else if (value > 0.2) {
                                bgColor = '#eab308'; // 低中风险-黄色
                                textColor = '#333';
                            } else {
                                bgColor = '#84cc16'; // 低风险-绿色
                                textColor = '#333';
                            }
                        }
                        
                        const tooltip = `表格: ${tableName}\\n列: ${heatmapData.columnNames[x]}\\n风险值: ${intensity}%`;
                        
                        tableHTML += `
                            <td class="risk-cell" 
                                style="background-color: ${bgColor}; color: ${textColor};" 
                                title="${tooltip}"
                                onclick="showCellDetail(${y}, ${x}, ${value})">
                                ${intensity > 5 ? intensity : ''}
                            </td>
                        `;
                    }
                    
                    tableHTML += '</tr>';
                }
                
                tableHTML += '</tbody></table></div>';
                
                document.getElementById('heatmap-container').innerHTML = tableHTML;
                return true;
                
            } catch (error) {
                document.getElementById('heatmap-container').innerHTML = 
                    '<div class="loading" style="color: #dc2626;">热力图数据加载失败: ' + error.message + '</div>';
                return false;
            }
        }
        
        // 显示单元格详情
        function showCellDetail(y, x, value) {
            const tableName = apiData.heatmap.tableNames[y] || '表格' + (y + 1);
            const columnName = apiData.heatmap.columnNames[x] || '列' + (x + 1);
            const intensity = Math.floor(value * 100);
            
            const riskLevel = value > 0.8 ? 'L1-高风险' : 
                             value > 0.4 ? 'L2-中风险' : 
                             value > 0 ? 'L3-低风险' : '无风险';
            
            alert(`📊 单元格详情\\n\\n表格: ${tableName}\\n列名: ${columnName}\\n风险值: ${intensity}%\\n风险等级: ${riskLevel}\\n\\n位置: [${y + 1}, ${x + 1}]`);
        }
        
        // 加载所有数据
        async function loadData() {
            updateStatus('正在加载数据...');
            
            const statusOk = await testAPI();
            if (!statusOk) return;
            
            const statsOk = await loadStats();
            const heatmapOk = await loadHeatmap();
            
            if (statsOk && heatmapOk) {
                updateStatus('所有数据加载完成 ✅');
                updateDebugInfo({
                    '状态': '数据加载完成',
                    '统计数据': apiData.stats,
                    '热力图尺寸': `${apiData.heatmap.data.length} × ${apiData.heatmap.columnNames.length}`,
                    '表格数量': apiData.heatmap.tables.length
                });
            } else {
                updateStatus('部分数据加载失败', true);
            }
        }
        
        // 页面加载完成后自动加载数据
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(loadData, 500);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """主页"""
    return SIMPLE_UI_TEMPLATE

@app.route('/api/status')
def api_status():
    """系统状态"""
    return jsonify({
        'status': 'running',
        'data_loaded': viz_data is not None,
        'tables_count': 30 if viz_data else 0,
        'modifications_count': len(viz_data['modification_locations']) if viz_data else 0,
        'server_time': '2025-08-12T17:30:00Z'
    })

@app.route('/api/stats')
def api_stats():
    """统计数据"""
    if not viz_data:
        return jsonify({'error': '数据未加载'}), 500
    
    risk_dist = viz_data['risk_distribution']
    
    # 分析最频繁修改的列
    column_count = {}
    for mod in viz_data['modification_locations']:
        col = mod['column_name']
        column_count[col] = column_count.get(col, 0) + 1
    
    most_modified_column = max(column_count.items(), key=lambda x: x[1])[0] if column_count else '无'
    
    return jsonify({
        'criticalModifications': risk_dist.get('L1', 0),
        'L1Modifications': risk_dist.get('L1', 0),
        'L2Modifications': risk_dist.get('L2', 0),
        'L3Modifications': risk_dist.get('L3', 0),
        'totalModifications': len(viz_data['modification_locations']),
        'mostModifiedColumn': most_modified_column,
        'mostModifiedTable': '企业项目管理表_修改版'
    })

@app.route('/api/heatmap')
def api_heatmap():
    """热力图数据"""
    if not viz_data:
        return jsonify({'error': '数据未加载'}), 500
    
    # 使用实际的风险矩阵数据
    risk_matrix = viz_data['risk_matrix']
    column_names = list(original_df.columns) if original_df is not None else []
    
    # 转换为0-1范围的热力值
    heat_data = []
    for row in risk_matrix:
        heat_row = []
        for cell in row:
            if cell == 0:
                heat_row.append(0)
            elif cell == 1:  # L3
                heat_row.append(0.3 + np.random.random() * 0.2)  # 0.3-0.5
            elif cell == 2:  # L2
                heat_row.append(0.5 + np.random.random() * 0.3)  # 0.5-0.8
            else:  # L1
                heat_row.append(0.8 + np.random.random() * 0.2)  # 0.8-1.0
        heat_data.append(heat_row)
    
    # 生成表格名称
    table_names = [
        '企业项目管理表_原始版',
        '企业项目管理表_修改版',
        '项目管理主计划表',
        '销售目标跟踪表'
    ]
    
    return jsonify({
        'data': heat_data,
        'columnNames': column_names,
        'tableNames': table_names,
        'tables': [{'name': name, 'id': i} for i, name in enumerate(table_names)]
    })

def main():
    print("🚀 启动简化版热力图UI测试服务器")
    print(f"🌐 访问地址: http://localhost:8090")
    print("=" * 50)
    
    if not viz_data:
        print("⚠️ 数据未正确加载")
        return
        
    try:
        app.run(host='0.0.0.0', port=8090, debug=False)
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()