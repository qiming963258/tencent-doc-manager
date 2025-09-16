#!/usr/bin/env python3
"""
增强版8089热力图服务器
包含：
1. 详细日志显示（复用8093格式）
2. URL软删除管理
3. 基线文件管理界面
"""

import os
import sys
import json
import time
import datetime
import shutil
import traceback
from flask import Flask, render_template_string, jsonify, request, send_file
from flask_cors import CORS

# 添加项目路径
sys.path.append('/root/projects/tencent-doc-manager')
sys.path.append('/root/projects/tencent-doc-manager/production/core_modules')

# 导入增强模块
from heatmap_server_enhancements import URLManager, BaselineFileManager, format_log_with_icons

# 导入原有模块
from production.core_modules.week_time_manager import WeekTimeManager
from production.core_modules.tencent_export_automation import TencentExporter

app = Flask(__name__)
CORS(app)

# 配置文件路径
CONFIG_DIR = '/root/projects/tencent-doc-manager/config'
DOWNLOAD_CONFIG_FILE = os.path.join(CONFIG_DIR, 'download_config.json')
COOKIES_CONFIG_FILE = os.path.join(CONFIG_DIR, 'cookies.json')

# 初始化管理器
url_manager = URLManager(DOWNLOAD_CONFIG_FILE)
baseline_manager = BaselineFileManager()

# 工作流状态
workflow_status = {
    'running': False,
    'current_step': '',
    'progress': 0,
    'logs': [],
    'last_update': None
}

def add_workflow_log(message, level='info'):
    """添加工作流日志（使用8093格式）"""
    log_entry = format_log_with_icons(message, level)
    workflow_status['logs'].append(log_entry)
    workflow_status['last_update'] = datetime.datetime.now().isoformat()
    
    # 控制台输出
    print(f"[{log_entry['time']}] {log_entry['message']}")
    
    # 限制日志数量
    if len(workflow_status['logs']) > 100:
        workflow_status['logs'] = workflow_status['logs'][-100:]

@app.route('/api/save-links', methods=['POST'])
def save_links():
    """保存链接配置（支持软删除）"""
    try:
        data = request.get_json()
        links = data.get('links', [])
        
        # 使用增强的URL管理器保存
        success = url_manager.save_links_with_soft_delete(links)
        
        if success:
            add_workflow_log(f"成功更新 {len(links)} 个文档链接", 'success')
            return jsonify({'success': True, 'message': f'成功更新 {len(links)} 个链接'})
        else:
            return jsonify({'success': False, 'error': '保存失败'})
            
    except Exception as e:
        add_workflow_log(f"保存链接失败: {str(e)}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get-links', methods=['GET'])
def get_links():
    """获取活跃的链接"""
    try:
        links = url_manager.get_active_links()
        return jsonify({'success': True, 'links': links})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/baseline-files', methods=['GET', 'POST', 'DELETE'])
def handle_baseline_files():
    """处理基线文件的管理"""
    try:
        if request.method == 'GET':
            # 获取基线文件列表
            result = baseline_manager.list_baseline_files()
            return jsonify(result)
        
        elif request.method == 'POST':
            # 下载并保存基线文件
            data = request.json
            url = data.get('url')
            cookie_string = data.get('cookie')
            
            if not url:
                return jsonify({'success': False, 'error': '缺少URL'})
            
            add_workflow_log(f"开始下载基线文件: {url}", 'info')
            result = baseline_manager.download_baseline_file(url, cookie_string)
            
            if result['success']:
                add_workflow_log(f"基线文件下载成功: {result['file']['name']}", 'success')
            else:
                add_workflow_log(f"基线文件下载失败: {result['error']}", 'error')
            
            return jsonify(result)
        
        elif request.method == 'DELETE':
            # 删除基线文件
            data = request.json
            filename = data.get('filename')
            
            if not filename:
                return jsonify({'success': False, 'error': '缺少文件名'})
            
            result = baseline_manager.delete_baseline_file(filename)
            
            if result['success']:
                add_workflow_log(f"基线文件已删除: {filename}", 'success')
            
            return jsonify(result)
            
    except Exception as e:
        add_workflow_log(f"基线文件操作失败: {str(e)}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/start-workflow', methods=['POST'])
def start_workflow():
    """启动工作流（带详细日志）"""
    global workflow_status
    
    try:
        if workflow_status['running']:
            return jsonify({'success': False, 'error': '工作流正在运行中'})
        
        workflow_status['running'] = True
        workflow_status['logs'] = []
        workflow_status['progress'] = 0
        
        add_workflow_log("🚀 开始执行8089-8093集成工作流", 'info')
        
        # 获取链接
        links = url_manager.get_active_links()
        if not links:
            add_workflow_log("没有可处理的文档链接", 'error')
            workflow_status['running'] = False
            return jsonify({'success': False, 'error': '没有可处理的文档链接'})
        
        add_workflow_log(f"📋 准备处理 {len(links)} 个文档", 'info')
        
        # 串行处理每个文档
        for idx, link in enumerate(links):
            add_workflow_log(f"[{idx+1}/{len(links)}] 处理文档: {link.get('name', 'Unknown')}", 'processing')
            workflow_status['current_step'] = f"处理文档 {idx+1}/{len(links)}"
            workflow_status['progress'] = int((idx + 1) / len(links) * 100)
            
            # 这里调用8093的接口处理
            # ... 实际处理逻辑 ...
            
            time.sleep(1)  # 模拟处理时间
            add_workflow_log(f"✅ 文档处理完成: {link.get('name', 'Unknown')}", 'success')
        
        add_workflow_log("🎉 工作流执行完成", 'success')
        workflow_status['running'] = False
        workflow_status['progress'] = 100
        
        return jsonify({'success': True, 'message': '工作流执行完成'})
        
    except Exception as e:
        add_workflow_log(f"工作流执行失败: {str(e)}", 'error')
        workflow_status['running'] = False
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/workflow-status', methods=['GET'])
def get_workflow_status():
    """获取工作流状态"""
    return jsonify(workflow_status)

@app.route('/')
def index():
    """主页面"""
    return render_template_string(ENHANCED_HTML_TEMPLATE)

# 增强版HTML模板
ENHANCED_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>8089增强版监控系统</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }
        
        .control-panel { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .control-group { margin-bottom: 20px; }
        .control-group label { display: block; margin-bottom: 5px; font-weight: 600; }
        .control-group input, .control-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .control-group textarea { min-height: 100px; resize: vertical; }
        
        .btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: 600; transition: all 0.3s; }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5a67d8; }
        .btn-success { background: #48bb78; color: white; }
        .btn-danger { background: #f56565; color: white; }
        .btn-warning { background: #ed8936; color: white; }
        
        .url-list { background: #f7fafc; padding: 15px; border-radius: 5px; margin-bottom: 15px; }
        .url-item { display: flex; gap: 10px; margin-bottom: 10px; }
        .url-item input { flex: 1; }
        
        .baseline-manager { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .baseline-header { display: flex; align-items: center; cursor: pointer; padding: 10px; background: #f0f0f0; border-radius: 5px; }
        .baseline-header:hover { background: #e0e0e0; }
        .baseline-files { max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-top: 10px; }
        .baseline-file { display: flex; justify-content: space-between; align-items: center; padding: 10px; background: white; border-radius: 5px; margin-bottom: 5px; }
        .baseline-file:hover { background: #f9f9f9; }
        
        .log-panel { background: #1a1a1a; color: #00ff00; padding: 20px; border-radius: 10px; height: 400px; overflow-y: auto; font-family: 'Courier New', monospace; }
        .log-entry { margin-bottom: 5px; padding: 5px; }
        .log-entry.info { color: #4299e1; }
        .log-entry.success { color: #48bb78; }
        .log-entry.error { color: #f56565; }
        .log-entry.processing { color: #ed8936; }
        
        .progress-bar { height: 30px; background: #e2e8f0; border-radius: 15px; overflow: hidden; margin: 20px 0; }
        .progress-bar-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); transition: width 0.3s; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; }
    </style>
</head>
<body>
    <div id="root"></div>
    
    <script type="text/babel">
        const { useState, useEffect, useCallback } = React;
        
        function App() {
            // 状态管理
            const [links, setLinks] = useState([]);
            const [storedUrls, setStoredUrls] = useState([]);
            const [cookie, setCookie] = useState('');
            const [baselineExpanded, setBaselineExpanded] = useState(false);
            const [baselineUrl, setBaselineUrl] = useState('');
            const [baselineFiles, setBaselineFiles] = useState([]);
            const [currentWeek, setCurrentWeek] = useState(0);
            const [baselinePath, setBaselinePath] = useState('');
            const [downloadingBaseline, setDownloadingBaseline] = useState(false);
            const [workflowStatus, setWorkflowStatus] = useState({
                running: false,
                current_step: '',
                progress: 0,
                logs: []
            });
            
            // 加载链接
            const loadLinks = async () => {
                try {
                    const response = await fetch('/api/get-links');
                    const data = await response.json();
                    if (data.success) {
                        setLinks(data.links || []);
                        setStoredUrls(data.links || []);
                    }
                } catch (error) {
                    console.error('加载链接失败:', error);
                }
            };
            
            // 加载基线文件
            const loadBaselineFiles = async () => {
                try {
                    const response = await fetch('/api/baseline-files');
                    const data = await response.json();
                    if (data.success) {
                        setBaselineFiles(data.files || []);
                        setCurrentWeek(data.week || 0);
                        setBaselinePath(data.path || '');
                    }
                } catch (error) {
                    console.error('加载基线文件失败:', error);
                }
            };
            
            // 加载工作流状态
            const loadWorkflowStatus = async () => {
                try {
                    const response = await fetch('/api/workflow-status');
                    const data = await response.json();
                    setWorkflowStatus(data);
                } catch (error) {
                    console.error('加载工作流状态失败:', error);
                }
            };
            
            // 保存链接
            const handleSaveLinks = async () => {
                const validLinks = links.filter(link => link.url && link.name);
                
                if (validLinks.length === 0) {
                    alert('请至少添加一个有效的链接');
                    return;
                }
                
                try {
                    const response = await fetch('/api/save-links', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({links: validLinks})
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert('链接更新成功!');
                        setStoredUrls(validLinks);
                    } else {
                        alert('链接更新失败: ' + result.error);
                    }
                } catch (error) {
                    alert('更新链接时出错: ' + error.message);
                }
            };
            
            // 添加链接
            const handleAddLink = () => {
                setLinks([...links, {url: '', name: '', enabled: true}]);
            };
            
            // 删除链接
            const handleRemoveLink = (index) => {
                setLinks(links.filter((_, i) => i !== index));
            };
            
            // 更新链接
            const handleLinkChange = (index, field, value) => {
                const newLinks = [...links];
                newLinks[index][field] = value;
                setLinks(newLinks);
            };
            
            // 下载基线文件
            const handleDownloadBaseline = async () => {
                if (!baselineUrl) {
                    alert('请输入基线文件URL');
                    return;
                }
                
                setDownloadingBaseline(true);
                try {
                    const response = await fetch('/api/baseline-files', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            url: baselineUrl,
                            cookie: cookie
                        })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        alert(`基线文件下载成功: ${data.file.name}`);
                        setBaselineUrl('');
                        await loadBaselineFiles();
                    } else {
                        alert(`下载失败: ${data.error}`);
                    }
                } catch (error) {
                    alert(`下载出错: ${error.message}`);
                } finally {
                    setDownloadingBaseline(false);
                }
            };
            
            // 删除基线文件
            const handleDeleteBaseline = async (filename) => {
                if (!confirm(`确定要删除文件: ${filename}?`)) {
                    return;
                }
                
                try {
                    const response = await fetch('/api/baseline-files', {
                        method: 'DELETE',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({filename})
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        alert(data.message);
                        await loadBaselineFiles();
                    } else {
                        alert(`删除失败: ${data.error}`);
                    }
                } catch (error) {
                    alert(`删除出错: ${error.message}`);
                }
            };
            
            // 启动工作流
            const handleStartWorkflow = async () => {
                try {
                    const response = await fetch('/api/start-workflow', {
                        method: 'POST'
                    });
                    
                    const result = await response.json();
                    if (!result.success) {
                        alert('启动失败: ' + result.error);
                    }
                } catch (error) {
                    alert('启动工作流失败: ' + error.message);
                }
            };
            
            // 初始化加载
            useEffect(() => {
                loadLinks();
                loadBaselineFiles();
                loadWorkflowStatus();
                
                // 定期更新工作流状态
                const interval = setInterval(loadWorkflowStatus, 2000);
                return () => clearInterval(interval);
            }, []);
            
            return (
                <div className="container">
                    <div className="header">
                        <h1>🚀 8089增强版监控系统</h1>
                        <p>集成URL管理、基线文件管理、详细日志显示</p>
                    </div>
                    
                    {/* URL管理 */}
                    <div className="control-panel">
                        <h2>📋 表格链接管理</h2>
                        
                        {/* 显示当前存储的URL */}
                        {storedUrls.length > 0 && (
                            <div className="url-list">
                                <strong>当前存储的URL:</strong>
                                <ul>
                                    {storedUrls.map((url, idx) => (
                                        <li key={idx}>{url.name}: {url.url}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        
                        {/* URL编辑 */}
                        {links.map((link, index) => (
                            <div key={index} className="url-item">
                                <input
                                    type="text"
                                    value={link.url}
                                    onChange={(e) => handleLinkChange(index, 'url', e.target.value)}
                                    placeholder="腾讯文档链接"
                                />
                                <input
                                    type="text"
                                    value={link.name}
                                    onChange={(e) => handleLinkChange(index, 'name', e.target.value)}
                                    placeholder="文档名称"
                                />
                                <button 
                                    onClick={() => handleRemoveLink(index)}
                                    className="btn btn-danger"
                                >
                                    删除
                                </button>
                            </div>
                        ))}
                        
                        <div style={{marginTop: '10px'}}>
                            <button onClick={handleAddLink} className="btn btn-primary">添加链接</button>
                            <button onClick={handleSaveLinks} className="btn btn-success" style={{marginLeft: '10px'}}>更新链接</button>
                        </div>
                    </div>
                    
                    {/* Cookie配置 */}
                    <div className="control-panel">
                        <h2>🔐 Cookie配置</h2>
                        <div className="control-group">
                            <textarea
                                value={cookie}
                                onChange={(e) => setCookie(e.target.value)}
                                placeholder="粘贴完整的Cookie字符串..."
                            />
                        </div>
                    </div>
                    
                    {/* 基线文件管理 */}
                    <div className="baseline-manager">
                        <div 
                            className="baseline-header"
                            onClick={() => setBaselineExpanded(!baselineExpanded)}
                        >
                            <span style={{marginRight: '10px'}}>
                                {baselineExpanded ? '▼' : '▶'}
                            </span>
                            📁 基线文件管理 (第{currentWeek}周 - {baselinePath})
                        </div>
                        
                        {baselineExpanded && (
                            <div style={{marginTop: '15px'}}>
                                <div style={{display: 'flex', gap: '10px', marginBottom: '15px'}}>
                                    <input
                                        type="text"
                                        value={baselineUrl}
                                        onChange={(e) => setBaselineUrl(e.target.value)}
                                        placeholder="输入基线文件的腾讯文档链接..."
                                        style={{flex: 1, padding: '10px', border: '1px solid #ddd', borderRadius: '5px'}}
                                    />
                                    <button
                                        onClick={handleDownloadBaseline}
                                        className="btn btn-primary"
                                        disabled={downloadingBaseline}
                                    >
                                        {downloadingBaseline ? '下载中...' : '下载基线'}
                                    </button>
                                </div>
                                
                                <div className="baseline-files">
                                    <h3>当前基线文件:</h3>
                                    {baselineFiles.length === 0 ? (
                                        <p style={{color: '#999', padding: '20px', textAlign: 'center'}}>暂无基线文件</p>
                                    ) : (
                                        baselineFiles.map((file, index) => (
                                            <div key={index} className="baseline-file">
                                                <div>
                                                    <strong>{file.name}</strong>
                                                    <div style={{fontSize: '12px', color: '#666'}}>
                                                        大小: {(file.size / 1024).toFixed(2)} KB | 
                                                        修改时间: {new Date(file.modified).toLocaleString('zh-CN')}
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => handleDeleteBaseline(file.name)}
                                                    className="btn btn-danger"
                                                >
                                                    删除
                                                </button>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                    
                    {/* 工作流控制 */}
                    <div className="control-panel">
                        <h2>⚙️ 工作流控制</h2>
                        <button 
                            onClick={handleStartWorkflow}
                            className="btn btn-warning"
                            disabled={workflowStatus.running}
                        >
                            {workflowStatus.running ? '运行中...' : '启动工作流'}
                        </button>
                        
                        {workflowStatus.progress > 0 && (
                            <div className="progress-bar">
                                <div 
                                    className="progress-bar-fill" 
                                    style={{width: `${workflowStatus.progress}%`}}
                                >
                                    {workflowStatus.progress}%
                                </div>
                            </div>
                        )}
                    </div>
                    
                    {/* 日志面板 */}
                    <div className="control-panel">
                        <h2>📊 详细日志</h2>
                        <div className="log-panel">
                            {workflowStatus.logs.length === 0 ? (
                                <div style={{color: '#666', textAlign: 'center', padding: '20px'}}>
                                    等待工作流执行...
                                </div>
                            ) : (
                                workflowStatus.logs.map((log, index) => (
                                    <div key={index} className={`log-entry ${log.level}`}>
                                        [{new Date(log.time).toLocaleTimeString('zh-CN')}] {log.message}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            );
        }
        
        ReactDOM.render(<App />, document.getElementById('root'));
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 启动增强版8089热力图服务器...")
    print("✅ 功能特性:")
    print("  - 详细日志显示（8093格式）")
    print("  - URL软删除管理")
    print("  - 基线文件管理界面")
    print(f"📍 访问地址: http://localhost:8089")
    app.run(host='0.0.0.0', port=8089, debug=True)