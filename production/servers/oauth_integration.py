#!/usr/bin/env python3
"""
OAuth集成模块 - 为热力图服务器添加OAuth支持
"""

from flask import Blueprint, request, redirect, session, jsonify
import requests
import json
import os
from datetime import datetime, timedelta
from urllib.parse import urlencode

oauth_bp = Blueprint('oauth', __name__)

# 配置文件路径
API_CONFIG_FILE = '/root/projects/tencent-doc-manager/config/api_config.json'

def load_api_config():
    """加载API配置"""
    if os.path.exists(API_CONFIG_FILE):
        with open(API_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_api_config(config):
    """保存API配置"""
    os.makedirs(os.path.dirname(API_CONFIG_FILE), exist_ok=True)
    with open(API_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

@oauth_bp.route('/api/oauth/status')
def oauth_status():
    """检查OAuth状态"""
    config = load_api_config()
    
    # 检查token是否有效
    token_valid = False
    expires_at = config.get('token_expires_at')
    if expires_at:
        try:
            expires_time = datetime.fromisoformat(expires_at)
            token_valid = datetime.now() < expires_time
        except:
            pass
    
    return jsonify({
        'configured': bool(config.get('client_id')),
        'authorized': bool(config.get('access_token')),
        'token_valid': token_valid,
        'expires_at': expires_at,
        'client_id': config.get('client_id', '')[:10] + '...' if config.get('client_id') else None
    })

@oauth_bp.route('/api/oauth/config', methods=['POST'])
def save_oauth_config():
    """保存OAuth配置"""
    data = request.json
    
    config = load_api_config()
    config.update({
        'client_id': data.get('client_id'),
        'client_secret': data.get('client_secret'),
        'redirect_uri': data.get('redirect_uri', 'http://202.140.143.88:8089/oauth/callback')
    })
    
    save_api_config(config)
    
    return jsonify({
        'success': True,
        'message': 'OAuth配置已保存'
    })

@oauth_bp.route('/api/oauth/authorize')
def start_oauth():
    """开始OAuth授权流程"""
    config = load_api_config()
    
    if not config.get('client_id'):
        return jsonify({
            'error': '请先配置Client ID和Client Secret'
        }), 400
    
    # 生成授权URL
    params = {
        'client_id': config['client_id'],
        'redirect_uri': config.get('redirect_uri', 'http://202.140.143.88:8089/oauth/callback'),
        'response_type': 'code',
        'scope': 'all',
        'state': 'tencent_doc_monitor'
    }
    
    auth_url = f"https://docs.qq.com/oauth/v2/authorize?" + urlencode(params)
    
    return jsonify({
        'auth_url': auth_url,
        'message': '请在新窗口中完成授权'
    })

@oauth_bp.route('/oauth/callback')
def oauth_callback():
    """OAuth回调处理"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return f"""
        <html>
        <body>
            <h2>授权失败</h2>
            <p>错误: {error}</p>
            <p><a href="/oauth-setup.html">返回设置页面</a></p>
        </body>
        </html>
        """
    
    if not code:
        return f"""
        <html>
        <body>
            <h2>授权失败</h2>
            <p>未获取到授权码</p>
            <p><a href="/oauth-setup.html">返回设置页面</a></p>
        </body>
        </html>
        """
    
    # 交换access token
    config = load_api_config()
    
    token_url = "https://docs.qq.com/oauth/v2/token"
    token_data = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'redirect_uri': config.get('redirect_uri'),
        'grant_type': 'authorization_code',
        'code': code
    }
    
    try:
        response = requests.post(token_url, data=token_data, timeout=10)
        result = response.json()
        
        if 'access_token' in result:
            # 保存token
            expires_in = result.get('expires_in', 7200)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            config.update({
                'access_token': result['access_token'],
                'refresh_token': result.get('refresh_token'),
                'token_expires_at': expires_at.isoformat(),
                'token_type': result.get('token_type', 'Bearer'),
                'scope': result.get('scope')
            })
            
            save_api_config(config)
            
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial; padding: 20px; }}
                    .success {{ color: green; }}
                    .token-info {{ 
                        background: #f0f0f0; 
                        padding: 15px; 
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                </style>
            </head>
            <body>
                <h2 class="success">✅ 授权成功！</h2>
                <div class="token-info">
                    <p><strong>Access Token:</strong> {result['access_token'][:20]}...</p>
                    <p><strong>Token类型:</strong> {result.get('token_type', 'Bearer')}</p>
                    <p><strong>有效期:</strong> {expires_in}秒</p>
                    <p><strong>过期时间:</strong> {expires_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <p>Token已保存，您现在可以使用API方式下载文档了！</p>
                <p><a href="/">返回主页</a></p>
                <script>
                    // 自动关闭窗口或跳转
                    setTimeout(() => {{
                        if (window.opener) {{
                            window.opener.postMessage({{type: 'oauth_success'}}, '*');
                            window.close();
                        }} else {{
                            window.location.href = '/';
                        }}
                    }}, 3000);
                </script>
            </body>
            </html>
            """
        else:
            error_msg = result.get('error_description', '未知错误')
            return f"""
            <html>
            <body>
                <h2>Token交换失败</h2>
                <p>错误: {error_msg}</p>
                <pre>{json.dumps(result, indent=2)}</pre>
                <p><a href="/oauth-setup.html">返回设置页面</a></p>
            </body>
            </html>
            """
            
    except Exception as e:
        return f"""
        <html>
        <body>
            <h2>Token交换异常</h2>
            <p>错误: {str(e)}</p>
            <p><a href="/oauth-setup.html">返回设置页面</a></p>
        </body>
        </html>
        """

@oauth_bp.route('/api/oauth/refresh', methods=['POST'])
def refresh_token():
    """刷新Access Token"""
    config = load_api_config()
    
    if not config.get('refresh_token'):
        return jsonify({
            'success': False,
            'error': '没有refresh token'
        }), 400
    
    token_url = "https://docs.qq.com/oauth/v2/token"
    token_data = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'grant_type': 'refresh_token',
        'refresh_token': config['refresh_token']
    }
    
    try:
        response = requests.post(token_url, data=token_data, timeout=10)
        result = response.json()
        
        if 'access_token' in result:
            expires_in = result.get('expires_in', 7200)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            config.update({
                'access_token': result['access_token'],
                'refresh_token': result.get('refresh_token', config['refresh_token']),
                'token_expires_at': expires_at.isoformat()
            })
            
            save_api_config(config)
            
            return jsonify({
                'success': True,
                'message': 'Token刷新成功',
                'expires_at': expires_at.isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error_description', '刷新失败')
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@oauth_bp.route('/api/test-api-download', methods=['POST'])
def test_api_download():
    """测试API下载功能"""
    from tencent_api_client import TencentDocsAPIClient
    import asyncio
    
    data = request.json
    file_id = data.get('file_id')
    
    if not file_id:
        return jsonify({
            'success': False,
            'error': '请提供文档ID'
        }), 400
    
    try:
        client = TencentDocsAPIClient()
        
        # 使用asyncio运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success, result = loop.run_until_complete(
            client.download_document_as_csv(file_id)
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': '下载成功',
                'file_path': result,
                'stats': client.get_stats()
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500