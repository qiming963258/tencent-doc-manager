#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档自动化服务 - Flask后端API
提供文档下载、上传、分析和修改的完整功能
"""

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import asyncio
import pandas as pd
from datetime import datetime
import hashlib
import sqlite3
from pathlib import Path
import secrets

# 导入现有的工具类
from tencent_export_automation import TencentDocAutoExporter
from tencent_upload_automation import TencentDocUploader
from concurrent_processor import get_processor, TaskType

app = Flask(__name__)
CORS(app)

# 配置
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB限制
app.config['DATABASE'] = 'tencent_docs.db'

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# 初始化数据库
def init_db():
    """初始化SQLite数据库"""
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    
    # 用户表（存储加密的cookies）
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  cookie_hash TEXT NOT NULL,
                  encrypted_cookies TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_used TIMESTAMP)''')
    
    # 文档历史表
    c.execute('''CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  doc_url TEXT,
                  doc_name TEXT,
                  file_path TEXT,
                  operation TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# 加密工具函数
def encrypt_cookies(cookies, user_key):
    """简单的cookie加密（生产环境应使用更强的加密）"""
    # 这里使用简单的XOR加密作为示例
    # 生产环境应使用 cryptography 库的 Fernet
    key_hash = hashlib.sha256(user_key.encode()).hexdigest()
    encrypted = []
    for i, char in enumerate(cookies):
        encrypted.append(chr(ord(char) ^ ord(key_hash[i % len(key_hash)])))
    return ''.join(encrypted)

def decrypt_cookies(encrypted_cookies, user_key):
    """解密cookies"""
    key_hash = hashlib.sha256(user_key.encode()).hexdigest()
    decrypted = []
    for i, char in enumerate(encrypted_cookies):
        decrypted.append(chr(ord(char) ^ ord(key_hash[i % len(key_hash)])))
    return ''.join(decrypted)

# API路由
@app.route('/')
def index():
    """主页"""
    return render_template('modern.html')

@app.route('/legacy')
def legacy_index():
    """传统版本主页"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': '腾讯文档自动化服务',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/save_cookies', methods=['POST'])
def save_cookies():
    """保存用户cookies"""
    try:
        data = request.json
        username = data.get('username')
        cookies = data.get('cookies')
        
        if not username or not cookies:
            return jsonify({'error': '用户名和cookies不能为空'}), 400
        
        # 生成用户密钥
        user_key = username + app.config['SECRET_KEY']
        
        # 加密cookies
        encrypted = encrypt_cookies(cookies, user_key)
        cookie_hash = hashlib.sha256(cookies.encode()).hexdigest()
        
        # 保存到数据库
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        
        # 检查用户是否存在
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        
        if user:
            # 更新现有用户
            c.execute("""UPDATE users SET cookie_hash = ?, encrypted_cookies = ?, 
                        last_used = CURRENT_TIMESTAMP WHERE username = ?""",
                     (cookie_hash, encrypted, username))
        else:
            # 创建新用户
            c.execute("""INSERT INTO users (username, cookie_hash, encrypted_cookies) 
                        VALUES (?, ?, ?)""",
                     (username, cookie_hash, encrypted))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Cookies保存成功',
            'username': username
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download_document():
    """下载腾讯文档"""
    try:
        data = request.json
        doc_url = data.get('doc_url')
        username = data.get('username')
        export_format = data.get('format', 'excel')
        
        if not doc_url or not username:
            return jsonify({'error': '文档URL和用户名不能为空'}), 400
        
        # 获取用户cookies
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        c.execute("SELECT encrypted_cookies FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': '用户不存在，请先保存Cookies'}), 404
        
        # 解密cookies
        user_key = username + app.config['SECRET_KEY']
        cookies = decrypt_cookies(user[0], user_key)
        
        # 创建异步任务下载文档
        async def download_task():
            exporter = TencentDocAutoExporter(download_dir=app.config['DOWNLOAD_FOLDER'])
            await exporter.start_browser(headless=True)
            
            if cookies:
                await exporter.login_with_cookies(cookies)
            
            result = await exporter.auto_export_document(doc_url, export_format)
            await exporter.cleanup()
            return result
        
        # 运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        downloaded_files = loop.run_until_complete(download_task())
        
        if downloaded_files:
            file_path = downloaded_files[0]
            
            # 记录到数据库
            conn = sqlite3.connect(app.config['DATABASE'])
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_id = c.fetchone()[0]
            c.execute("""INSERT INTO documents (user_id, doc_url, doc_name, file_path, operation)
                        VALUES (?, ?, ?, ?, 'download')""",
                     (user_id, doc_url, os.path.basename(file_path), file_path))
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': '文档下载成功',
                'file_path': file_path,
                'file_name': os.path.basename(file_path)
            })
        else:
            return jsonify({'error': '文档下载失败'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """上传文档到腾讯文档"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件'}), 400
        
        file = request.files['file']
        username = request.form.get('username')
        
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not username:
            return jsonify({'error': '用户名不能为空'}), 400
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 获取用户cookies
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        c.execute("SELECT encrypted_cookies FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': '用户不存在，请先保存Cookies'}), 404
        
        # 解密cookies
        user_key = username + app.config['SECRET_KEY']
        cookies = decrypt_cookies(user[0], user_key)
        
        # 创建异步任务上传文档
        async def upload_task():
            uploader = TencentDocUploader()
            await uploader.start_browser(headless=True)
            
            if cookies:
                await uploader.login_with_cookies(cookies)
            
            result = await uploader.upload_file_to_main_page(file_path)
            await uploader.cleanup()
            return result
        
        # 运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(upload_task())
        
        if success:
            # 记录到数据库
            conn = sqlite3.connect(app.config['DATABASE'])
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_id = c.fetchone()[0]
            c.execute("""INSERT INTO documents (user_id, doc_name, file_path, operation)
                        VALUES (?, ?, ?, 'upload')""",
                     (user_id, filename, file_path))
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': '文档上传成功',
                'file_name': filename
            })
        else:
            return jsonify({'error': '文档上传失败'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    """分析Excel文档"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 使用pandas分析Excel
        df = pd.read_excel(file_path)
        
        analysis = {
            'file_name': filename,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': df.columns.tolist(),
            'data_types': df.dtypes.astype(str).to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'summary': df.describe().to_dict() if not df.empty else {},
            'preview': df.head(10).to_dict('records')
        }
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/modify', methods=['POST'])
def modify_document():
    """修改Excel文档"""
    try:
        data = request.json
        file_path = data.get('file_path')
        modifications = data.get('modifications', [])
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        # 读取Excel
        df = pd.read_excel(file_path)
        
        # 应用修改
        for mod in modifications:
            row = mod.get('row')
            col = mod.get('column')
            value = mod.get('value')
            
            if row is not None and col is not None:
                df.iloc[row, col] = value
        
        # 保存修改后的文件
        modified_path = file_path.replace('.xlsx', '_modified.xlsx')
        df.to_excel(modified_path, index=False)
        
        return jsonify({
            'success': True,
            'message': '文档修改成功',
            'modified_file': modified_path
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """获取操作历史"""
    try:
        username = request.args.get('username')
        
        if not username:
            return jsonify({'error': '用户名不能为空'}), 400
        
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        
        # 获取用户ID
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        user_id = user[0]
        
        # 获取历史记录
        c.execute("""SELECT doc_url, doc_name, operation, created_at 
                    FROM documents WHERE user_id = ? 
                    ORDER BY created_at DESC LIMIT 50""", (user_id,))
        
        history = []
        for row in c.fetchall():
            history.append({
                'doc_url': row[0],
                'doc_name': row[1],
                'operation': row[2],
                'created_at': row[3]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download_file/<path:filename>', methods=['GET'])
def download_file(filename):
    """下载服务器上的文件"""
    try:
        file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 批量处理API端点 ====================

@app.route('/api/batch/download', methods=['POST'])
def batch_download_documents():
    """批量下载腾讯文档 - 支持30+文档并发处理"""
    try:
        data = request.json
        urls = data.get('urls', [])
        username = data.get('username')
        export_format = data.get('format', 'excel')
        job_name = data.get('job_name', f'批量下载-{datetime.now().strftime("%Y%m%d-%H%M%S")}')
        
        if not urls or not username:
            return jsonify({'error': 'URL列表和用户名不能为空'}), 400
        
        if len(urls) > 100:  # 限制最大批处理数量
            return jsonify({'error': '批处理数量不能超过100个'}), 400
        
        # 获取用户cookies
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        c.execute("SELECT encrypted_cookies FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': '用户不存在，请先保存Cookies'}), 404
        
        # 解密cookies
        user_key = username + app.config['SECRET_KEY']
        cookies = decrypt_cookies(user[0], user_key)
        
        # 创建批处理作业
        processor = get_processor()
        job_id = processor.create_download_job(
            name=job_name,
            urls=urls,
            username=username,
            cookies=cookies,
            format=export_format
        )
        
        return jsonify({
            'success': True,
            'message': f'批量下载作业已创建，共{len(urls)}个文档',
            'job_id': job_id,
            'job_name': job_name,
            'total_documents': len(urls)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch/upload', methods=['POST'])
def batch_upload_documents():
    """批量上传文档到腾讯文档 - 支持30+文件并发处理"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': '没有文件'}), 400
        
        files = request.files.getlist('files')
        username = request.form.get('username')
        job_name = request.form.get('job_name', f'批量上传-{datetime.now().strftime("%Y%m%d-%H%M%S")}')
        
        if not files or not username:
            return jsonify({'error': '文件列表和用户名不能为空'}), 400
        
        if len(files) > 50:  # 上传限制相对较小
            return jsonify({'error': '批处理上传数量不能超过50个'}), 400
        
        # 获取用户cookies
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        c.execute("SELECT encrypted_cookies FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': '用户不存在，请先保存Cookies'}), 404
        
        # 解密cookies
        user_key = username + app.config['SECRET_KEY']
        cookies = decrypt_cookies(user[0], user_key)
        
        # 保存所有上传的文件
        file_paths = []
        for file in files:
            if file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{username}_{filename}")
                file.save(file_path)
                file_paths.append(file_path)
        
        if not file_paths:
            return jsonify({'error': '没有有效文件'}), 400
        
        # 创建批处理作业
        processor = get_processor()
        job_id = processor.create_upload_job(
            name=job_name,
            file_paths=file_paths,
            username=username,
            cookies=cookies
        )
        
        return jsonify({
            'success': True,
            'message': f'批量上传作业已创建，共{len(file_paths)}个文件',
            'job_id': job_id,
            'job_name': job_name,
            'total_files': len(file_paths)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch/execute/<job_id>', methods=['POST'])
def execute_batch_job(job_id):
    """执行批处理作业"""
    try:
        processor = get_processor()
        
        # 创建异步执行任务
        async def execute_job():
            async def progress_callback(task):
                # 这里可以通过WebSocket或SSE推送进度更新
                # 暂时只记录到日志
                print(f"任务进度: {task.id[:8]} - {task.status.value} - {task.progress:.1%} - {task.message}")
            
            return await processor.execute_job(job_id, progress_callback)
        
        # 在后台执行任务
        import threading
        def run_job():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(execute_job())
            finally:
                loop.close()
        
        job_thread = threading.Thread(target=run_job, daemon=True)
        job_thread.start()
        
        return jsonify({
            'success': True,
            'message': '批处理作业已开始执行',
            'job_id': job_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch/status/<job_id>', methods=['GET'])
def get_batch_job_status(job_id):
    """获取批处理作业状态"""
    try:
        processor = get_processor()
        status = processor.get_job_status(job_id)
        
        if not status:
            return jsonify({'error': '作业不存在'}), 404
        
        return jsonify({
            'success': True,
            'job_status': status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch/cancel/<job_id>', methods=['POST'])
def cancel_batch_job(job_id):
    """取消批处理作业"""
    try:
        processor = get_processor()
        success = processor.cancel_job(job_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '作业已取消'
            })
        else:
            return jsonify({'error': '作业不存在或无法取消'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch/jobs', methods=['GET'])
def list_batch_jobs():
    """列出所有批处理作业"""
    try:
        username = request.args.get('username')
        processor = get_processor()
        
        # 获取所有作业状态
        all_jobs = []
        for job_id in processor.active_jobs.keys():
            status = processor.get_job_status(job_id)
            if status:
                # 如果指定了用户名，则过滤
                if username:
                    # 检查作业中的任务是否属于该用户
                    user_jobs = [task for task in status.get('tasks', []) 
                               if any(username in str(task.get('message', '')))]
                    if user_jobs:
                        all_jobs.append(status)
                else:
                    all_jobs.append(status)
        
        return jsonify({
            'success': True,
            'jobs': all_jobs
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch/cleanup', methods=['POST'])
def cleanup_batch_jobs():
    """清理完成的批处理作业"""
    try:
        max_age_hours = request.json.get('max_age_hours', 24) if request.is_json else 24
        processor = get_processor()
        processor.cleanup_completed_jobs(max_age_hours)
        
        return jsonify({
            'success': True,
            'message': f'已清理{max_age_hours}小时前的完成作业'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)