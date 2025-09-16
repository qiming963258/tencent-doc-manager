#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的真实数据热力图服务器
"""

import os
import json
import glob
import csv
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 项目路径配置
PROJECT_ROOT = '/root/projects/tencent-doc-manager'
AUTO_DOWNLOADS_DIR = os.path.join(PROJECT_ROOT, 'auto_downloads')
COMPARISON_DIR = os.path.join(PROJECT_ROOT, 'csv_versions/comparison')
CONFIG_FILE = os.path.join(PROJECT_ROOT, 'auto_download_config.json')

def load_config():
    """加载配置文件"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ 加载配置失败: {e}")
    return {}

def scan_csv_files():
    """扫描真实的CSV文件"""
    csv_files = []
    
    for file_path in glob.glob(os.path.join(AUTO_DOWNLOADS_DIR, '*.csv')):
        file_name = os.path.basename(file_path)
        file_stat = os.stat(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
                row_count = len(rows)
                col_count = len(rows[0]) if rows else 0
        except:
            row_count = 0
            col_count = 0
            
        csv_files.append({
            'name': file_name,
            'path': file_path,
            'size': file_stat.st_size,
            'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            'rows': row_count,
            'columns': col_count
        })
    
    return sorted(csv_files, key=lambda x: x['modified'], reverse=True)

def load_comparison_result():
    """加载真实的对比结果"""
    comparison_file = os.path.join(COMPARISON_DIR, 'comparison_result.json')
    
    if os.path.exists(comparison_file):
        try:
            with open(comparison_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 加载对比结果失败: {e}")
    
    return None

@app.route('/')
def index():
    """简单的主页面"""
    return '''<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腾讯文档监控 - 真实数据版</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
</head>
<body class="bg-gray-100">
    <div id="root"></div>
    
    <script type="text/babel">
        const { useState, useEffect } = React;
        
        function RealDataDashboard() {
            const [data, setData] = useState(null);
            const [loading, setLoading] = useState(true);
            
            useEffect(() => {
                fetch('/api/real_data')
                    .then(res => res.json())
                    .then(result => {
                        setData(result);
                        setLoading(false);
                    })
                    .catch(err => {
                        console.error('数据加载失败:', err);
                        setLoading(false);
                    });
            }, []);
            
            if (loading) {
                return (
                    <div className="min-h-screen flex items-center justify-center">
                        <div className="text-xl">加载真实数据中...</div>
                    </div>
                );
            }
            
            if (!data || !data.success) {
                return (
                    <div className="min-h-screen flex items-center justify-center">
                        <div className="text-xl text-red-600">数据加载失败</div>
                    </div>
                );
            }
            
            return (
                <div className="p-6 max-w-7xl mx-auto">
                    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
                        <h1 className="text-3xl font-bold mb-4 text-blue-600">
                            腾讯文档监控系统 - 真实数据版
                        </h1>
                        <div className="grid grid-cols-4 gap-4 text-center">
                            <div className="bg-blue-50 p-4 rounded">
                                <div className="text-2xl font-bold text-blue-600">{data.file_count}</div>
                                <div className="text-sm text-gray-600">CSV文件数</div>
                            </div>
                            <div className="bg-green-50 p-4 rounded">
                                <div className="text-2xl font-bold text-green-600">{data.total_changes}</div>
                                <div className="text-sm text-gray-600">总变更数</div>
                            </div>
                            <div className="bg-yellow-50 p-4 rounded">
                                <div className="text-2xl font-bold text-yellow-600">{data.risk_score.toFixed(1)}</div>
                                <div className="text-sm text-gray-600">安全评分</div>
                            </div>
                            <div className="bg-purple-50 p-4 rounded">
                                <div className="text-2xl font-bold text-purple-600">{data.data_source}</div>
                                <div className="text-sm text-gray-600">数据源</div>
                            </div>
                        </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-6">
                        <div className="bg-white rounded-lg shadow-lg p-6">
                            <h2 className="text-xl font-bold mb-4">真实文件列表</h2>
                            <div className="space-y-3">
                                {data.row_names.map((name, i) => (
                                    <div key={i} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                                        <span className="font-medium">{name}</span>
                                        <div className="flex gap-2">
                                            {data.statistics[i] && (
                                                <>
                                                    <span className="text-sm bg-blue-100 px-2 py-1 rounded">
                                                        {data.statistics[i].modifications} 修改
                                                    </span>
                                                    <span className={
                                                        data.statistics[i].risk_level === 'L1' ? 'text-sm bg-red-100 text-red-600 px-2 py-1 rounded' :
                                                        data.statistics[i].risk_level === 'L2' ? 'text-sm bg-yellow-100 text-yellow-600 px-2 py-1 rounded' :
                                                        'text-sm bg-green-100 text-green-600 px-2 py-1 rounded'
                                                    }>
                                                        {data.statistics[i].risk_level}
                                                    </span>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        
                        <div className="bg-white rounded-lg shadow-lg p-6">
                            <h2 className="text-xl font-bold mb-4">热力图矩阵</h2>
                            <div className="text-sm text-gray-600 mb-4">
                                实际文件: {data.file_count} × 列数: {data.column_names.length}
                            </div>
                            <div className="grid grid-cols-10 gap-1">
                                {data.matrix.map((row, i) => 
                                    row.slice(0, 10).map((cell, j) => (
                                        <div 
                                            key={`${i}-${j}`}
                                            className="w-6 h-6 rounded"
                                            style={{
                                                backgroundColor: cell < 0.2 ? '#0066CC' :
                                                               cell < 0.4 ? '#00CCCC' :
                                                               cell < 0.6 ? '#00CC00' :
                                                               cell < 0.8 ? '#FFCC00' : '#FF3333',
                                                opacity: 0.8
                                            }}
                                            title={`行${i+1} 列${j+1}: ${cell.toFixed(2)}`}
                                        />
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                    
                    <div className="mt-6 bg-white rounded-lg shadow-lg p-6">
                        <h2 className="text-xl font-bold mb-4">系统信息</h2>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                                <span className="font-medium">配置文档URL:</span><br/>
                                <a href={data.document_url} target="_blank" className="text-blue-600 hover:underline">
                                    {data.document_url || '未配置'}
                                </a>
                            </div>
                            <div>
                                <span className="font-medium">最后更新:</span><br/>
                                {new Date(data.timestamp).toLocaleString()}
                            </div>
                            <div>
                                <span className="font-medium">数据来源:</span><br/>
                                真实CSV文件扫描
                            </div>
                        </div>
                    </div>
                </div>
            );
        }
        
        ReactDOM.render(<RealDataDashboard />, document.getElementById('root'));
    </script>
</body>
</html>'''

@app.route('/api/real_data')
def get_real_data():
    """获取真实数据API"""
    
    # 扫描CSV文件
    csv_files = scan_csv_files()
    
    # 加载对比结果
    comparison_result = load_comparison_result()
    
    # 加载配置
    config = load_config()
    
    # 生成基本矩阵
    num_files = len(csv_files)
    num_columns = 19
    matrix = [[0.05 for _ in range(num_columns)] for _ in range(num_files)]
    
    # 如果有对比结果，映射变更
    if comparison_result and 'differences' in comparison_result:
        for diff in comparison_result['differences']:
            row_idx = diff.get('行号', 1) - 1
            col_idx = diff.get('列索引', 1) - 1
            risk_score = diff.get('risk_score', 0.2)
            
            if 0 <= row_idx < num_files and 0 <= col_idx < num_columns:
                heat_value = 0.3 + (risk_score * 0.7)
                matrix[row_idx][col_idx] = min(1.0, heat_value)
    
    # 提取文件名和列名
    row_names = [f['name'].replace('.csv', '') for f in csv_files]
    column_names = ['部门', '员工姓名', '工号', '本周工作内容', '完成度', '风险等级'] + [f'列{i+7}' for i in range(13)]
    
    # 计算统计
    statistics = []
    for i, csv_file in enumerate(csv_files):
        modifications = 0
        if comparison_result and 'differences' in comparison_result:
            modifications = len([d for d in comparison_result['differences'] if d.get('行号', 1) - 1 == i])
        
        risk_level = 'L3'
        if modifications > 5:
            risk_level = 'L1'
        elif modifications > 2:
            risk_level = 'L2'
        
        statistics.append({
            'file_name': csv_file['name'],
            'modifications': modifications,
            'risk_level': risk_level,
            'row_count': csv_file['rows'],
            'column_count': csv_file['columns']
        })
    
    return jsonify({
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'matrix': matrix,
        'row_names': row_names,
        'column_names': column_names,
        'statistics': statistics,
        'total_changes': len(comparison_result.get('differences', [])) if comparison_result else 0,
        'risk_score': comparison_result.get('security_score', 0) if comparison_result else 0,
        'document_url': config.get('urls', [''])[0] if config else '',
        'data_source': 'real_csv_files',
        'file_count': len(csv_files)
    })

if __name__ == '__main__':
    print("🚀 启动简化版真实数据热力图服务器...")
    print("📊 数据源: 真实CSV文件")
    print("🔗 访问地址: http://202.140.143.88:8091")
    app.run(host='0.0.0.0', port=8089, debug=False)