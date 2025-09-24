#!/usr/bin/env python3
"""
为8089界面添加API密钥管理功能
"""

def generate_api_key_ui_component():
    """生成API密钥管理的React组件"""

    component = '''
    // API密钥管理组件
    const APIKeyManager = ({ onUpdate }) => {
      const [apiKey, setApiKey] = useState('');
      const [showKey, setShowKey] = useState(false);
      const [testing, setTesting] = useState(false);
      const [balance, setBalance] = useState(null);
      const [status, setStatus] = useState('');

      // 加载当前密钥
      useEffect(() => {
        fetch('/api/get-api-key')
          .then(res => res.json())
          .then(data => {
            if (data.key) {
              setApiKey(data.key);
              setBalance(data.balance);
            }
          });
      }, []);

      // 测试API连接
      const testAPI = async () => {
        setTesting(true);
        setStatus('测试中...');

        try {
          const res = await fetch('/api/test-api-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: apiKey })
          });

          const data = await res.json();
          if (data.success) {
            setStatus('✅ API密钥有效');
            setBalance(data.balance);
          } else {
            setStatus('❌ ' + data.error);
          }
        } catch (error) {
          setStatus('❌ 测试失败: ' + error.message);
        } finally {
          setTesting(false);
        }
      };

      // 保存密钥
      const saveKey = async () => {
        try {
          const res = await fetch('/api/save-api-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: apiKey })
          });

          const data = await res.json();
          if (data.success) {
            setStatus('✅ 密钥已保存');
            onUpdate && onUpdate(apiKey);
          } else {
            setStatus('❌ 保存失败');
          }
        } catch (error) {
          setStatus('❌ 保存失败: ' + error.message);
        }
      };

      return (
        <div className="bg-white rounded-lg shadow-md p-4 mb-4">
          <h3 className="text-lg font-semibold mb-3">🔑 硅基流动API密钥管理</h3>

          <div className="space-y-3">
            {/* 密钥输入 */}
            <div className="flex items-center space-x-2">
              <label className="w-24 text-sm font-medium">API密钥:</label>
              <div className="flex-1 relative">
                <input
                  type={showKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showKey ? '🙈' : '👁️'}
                </button>
              </div>
            </div>

            {/* 账户余额 */}
            {balance !== null && (
              <div className="flex items-center space-x-2">
                <label className="w-24 text-sm font-medium">账户余额:</label>
                <span className="text-sm font-semibold text-green-600">
                  ￥{balance}
                </span>
              </div>
            )}

            {/* 操作按钮 */}
            <div className="flex space-x-3">
              <button
                onClick={testAPI}
                disabled={testing || !apiKey}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-400"
              >
                {testing ? '测试中...' : '测试连接'}
              </button>

              <button
                onClick={saveKey}
                disabled={!apiKey}
                className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:bg-gray-400"
              >
                保存密钥
              </button>
            </div>

            {/* 状态显示 */}
            {status && (
              <div className={`mt-2 p-2 rounded-md text-sm ${
                status.includes('✅') ? 'bg-green-100 text-green-700' :
                status.includes('❌') ? 'bg-red-100 text-red-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {status}
              </div>
            )}

            {/* 使用说明 */}
            <div className="mt-3 p-3 bg-gray-50 rounded-md text-xs text-gray-600">
              <p className="font-semibold mb-1">说明：</p>
              <ul className="list-disc list-inside space-y-1">
                <li>使用硅基流动(SiliconFlow)提供的DeepSeek API</li>
                <li>密钥格式：sk-开头的字符串</li>
                <li>用于L2列的智能语义分析</li>
                <li>当前L1列（如"重要程度"）不使用AI分析</li>
              </ul>
            </div>
          </div>
        </div>
      );
    };
    '''

    return component

def generate_backend_endpoints():
    """生成后端API端点"""

    endpoints = '''
# 添加到final_heatmap_server.py

@app.route('/api/get-api-key', methods=['GET'])
def get_api_key():
    """获取当前API密钥（脱敏）"""
    try:
        from dotenv import load_dotenv
        load_dotenv('/root/projects/tencent-doc-manager/.env')

        key = os.getenv('DEEPSEEK_API_KEY', '')
        if key:
            # 脱敏处理
            masked_key = key[:10] + '...' + key[-4:] if len(key) > 14 else key

            # 尝试获取余额
            balance = None
            try:
                from production.core_modules.deepseek_client import DeepSeekClient
                client = DeepSeekClient(key)
                # 调用余额查询API
                balance = client.get_balance()
            except:
                pass

            return jsonify({
                'success': True,
                'key': masked_key,
                'balance': balance
            })
        else:
            return jsonify({'success': False, 'key': ''})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test-api-key', methods=['POST'])
def test_api_key():
    """测试API密钥是否有效"""
    try:
        data = request.json
        api_key = data.get('key')

        if not api_key:
            return jsonify({'success': False, 'error': '密钥为空'})

        # 测试API
        import requests
        url = "https://api.siliconflow.cn/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-ai/DeepSeek-V3",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            # 获取余额
            balance_url = "https://api.siliconflow.cn/v1/user/info"
            balance_response = requests.get(balance_url, headers={"Authorization": f"Bearer {api_key}"})
            balance = "未知"
            if balance_response.status_code == 200:
                balance_data = balance_response.json()
                balance = balance_data.get('data', {}).get('totalBalance', '未知')

            return jsonify({'success': True, 'balance': balance})
        elif response.status_code == 401:
            return jsonify({'success': False, 'error': '密钥无效'})
        else:
            return jsonify({'success': False, 'error': f'API错误: {response.status_code}'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save-api-key', methods=['POST'])
def save_api_key():
    """保存API密钥到.env文件"""
    try:
        data = request.json
        api_key = data.get('key')

        if not api_key:
            return jsonify({'success': False, 'error': '密钥为空'})

        # 更新.env文件
        env_file = '/root/projects/tencent-doc-manager/.env'
        lines = []
        key_found = False

        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()

        # 更新或添加密钥
        for i, line in enumerate(lines):
            if line.startswith('DEEPSEEK_API_KEY='):
                lines[i] = f'DEEPSEEK_API_KEY={api_key}\\n'
                key_found = True
                break

        if not key_found:
            lines.append(f'DEEPSEEK_API_KEY={api_key}\\n')

        # 写回文件
        with open(env_file, 'w') as f:
            f.writelines(lines)

        # 重新加载环境变量
        os.environ['DEEPSEEK_API_KEY'] = api_key

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    '''

    return endpoints

def main():
    print("🔧 生成API密钥管理界面组件")
    print("="*80)

    print("\n1. React组件代码：")
    print("-"*40)
    component = generate_api_key_ui_component()
    print(component[:500] + "...")

    print("\n2. 后端API端点：")
    print("-"*40)
    endpoints = generate_backend_endpoints()
    print(endpoints[:500] + "...")

    print("\n" + "="*80)
    print("💡 集成步骤：")
    print("1. 将React组件添加到8089界面的监控设置部分")
    print("2. 将API端点添加到final_heatmap_server.py")
    print("3. 重启8089服务")
    print("4. 界面将显示API密钥输入框、余额显示和测试按钮")

    print("\n✨ 功能特性：")
    print("- 密钥输入框（支持显示/隐藏）")
    print("- 实时余额查询")
    print("- 连接测试功能")
    print("- 密钥持久化保存到.env")
    print("- 状态反馈显示")

if __name__ == "__main__":
    main()