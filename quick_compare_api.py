#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速对比API - 使用缓存文件避免重复下载
解决502超时问题的临时方案
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
import hashlib

# 添加项目路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'production' / 'core_modules'))

from enhanced_csv_comparison import enhanced_csv_compare
from simple_comparison_handler import simple_csv_compare

app = Flask(__name__)
CORS(app)

# 缓存目录
CACHE_DIR = BASE_DIR / 'csv_versions' / '2025_W36' / 'midweek'
RESULT_DIR = BASE_DIR / 'comparison_results'

def get_url_hash(url):
    """生成URL的哈希值用于缓存匹配"""
    return hashlib.md5(url.encode()).hexdigest()[:8]

def find_cached_file(url, max_age_minutes=30):
    """查找最近下载的缓存文件"""
    url_patterns = {
        'DWEFNU25TemFnZXJN': '副本-测试版本-出国销售计划表',
        'DWHR6UXh1UVRtSERw': '副本-副本-测试版本-出国销售计划表',
        'DWFJzdWNwd0RGbU5R': '测试版本-小红书部门'
    }
    
    # 从URL中提取文档ID
    doc_id = None
    for key in url_patterns:
        if key in url:
            doc_id = key
            pattern = url_patterns[key]
            break
    
    if not doc_id:
        return None
    
    # 查找匹配的缓存文件
    now = datetime.now()
    for file_path in CACHE_DIR.glob(f"*{pattern}*.csv"):
        # 检查文件年龄
        file_age = now - datetime.fromtimestamp(file_path.stat().st_mtime)
        if file_age < timedelta(minutes=max_age_minutes):
            return str(file_path)
    
    return None

@app.route('/')
def index():
    """主页"""
    return '''
    <h1>快速对比API - 临时解决方案</h1>
    <p>使用缓存文件进行快速对比，避免502超时</p>
    <ul>
        <li>POST /api/quick-compare - 快速对比（使用缓存）</li>
        <li>GET /api/cached-files - 查看可用缓存文件</li>
        <li>POST /api/direct-compare - 直接对比已有文件</li>
    </ul>
    '''

@app.route('/api/quick-compare', methods=['POST'])
def quick_compare():
    """快速对比接口 - 优先使用缓存"""
    try:
        data = request.json
        baseline_url = data.get('baseline_url', '')
        target_url = data.get('target_url', '')
        
        if not baseline_url or not target_url:
            return jsonify({
                'success': False,
                'error': 'URLs are required'
            }), 400
        
        # 查找缓存文件
        baseline_file = find_cached_file(baseline_url)
        target_file = find_cached_file(target_url)
        
        if not baseline_file or not target_file:
            return jsonify({
                'success': False,
                'error': '缓存文件未找到，请先通过8094端口下载',
                'tip': '建议：先单独访问各URL进行下载，然后再对比'
            }), 404
        
        # 执行对比
        result = enhanced_csv_compare(baseline_file, target_file)
        
        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = RESULT_DIR / f'quick_comparison_{timestamp}.json'
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                'baseline_file': baseline_file,
                'target_file': target_file,
                'comparison_result': result,
                'timestamp': timestamp,
                'mode': 'quick_cached'
            }, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'comparison_result': result,
            'baseline_file': Path(baseline_file).name,
            'target_file': Path(target_file).name,
            'result_file': str(result_file),
            'mode': 'cached',
            'message': '使用缓存文件完成对比'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cached-files')
def list_cached_files():
    """列出可用的缓存文件"""
    files = []
    now = datetime.now()
    
    for file_path in CACHE_DIR.glob("*.csv"):
        file_age = now - datetime.fromtimestamp(file_path.stat().st_mtime)
        files.append({
            'name': file_path.name,
            'size': file_path.stat().st_size,
            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            'age_minutes': int(file_age.total_seconds() / 60),
            'path': str(file_path)
        })
    
    # 按修改时间排序
    files.sort(key=lambda x: x['modified'], reverse=True)
    
    return jsonify({
        'success': True,
        'cache_dir': str(CACHE_DIR),
        'files': files[:20],  # 只返回最近20个文件
        'total': len(files)
    })

@app.route('/api/direct-compare', methods=['POST'])
def direct_compare():
    """直接对比指定的文件路径"""
    try:
        data = request.json
        baseline_path = data.get('baseline_path', '')
        target_path = data.get('target_path', '')
        
        if not baseline_path or not target_path:
            return jsonify({
                'success': False,
                'error': '文件路径必需'
            }), 400
        
        # 检查文件存在
        if not Path(baseline_path).exists():
            return jsonify({
                'success': False,
                'error': f'基线文件不存在: {baseline_path}'
            }), 404
        
        if not Path(target_path).exists():
            return jsonify({
                'success': False,
                'error': f'目标文件不存在: {target_path}'
            }), 404
        
        # 执行对比
        result = enhanced_csv_compare(baseline_path, target_path)
        
        return jsonify({
            'success': True,
            'comparison_result': result,
            'baseline_file': Path(baseline_path).name,
            'target_file': Path(target_path).name,
            'mode': 'direct'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 快速对比API启动")
    print("📁 缓存目录:", CACHE_DIR)
    print("📊 功能: 使用缓存文件快速对比，避免502超时")
    print("🔗 访问: http://202.140.143.88:8095/")
    app.run(host='0.0.0.0', port=8095, debug=False)