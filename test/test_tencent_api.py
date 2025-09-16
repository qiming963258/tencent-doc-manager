#!/usr/bin/env python3
"""
腾讯文档API快速测试脚本
用于验证API的可行性和基本功能
"""

import requests
import json
import time
from urllib.parse import urlencode, quote

class TencentDocsAPITester:
    """腾讯文档API测试器"""
    
    def __init__(self):
        # TODO: 从开放平台获取这些值
        self.client_id = "YOUR_CLIENT_ID"  # 替换为实际值
        self.client_secret = "YOUR_CLIENT_SECRET"  # 替换为实际值
        self.redirect_uri = "http://localhost:8089/oauth/callback"
        
        # API基础URL
        self.auth_base = "https://docs.qq.com/oauth/v2"
        self.api_base = "https://docs.qq.com/openapi"
        
        # Token存储
        self.access_token = None
        self.refresh_token = None
        
    def step1_get_auth_url(self):
        """步骤1: 生成授权URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'all',  # 申请所有基础权限
            'state': 'test123'  # 防CSRF攻击
        }
        
        auth_url = f"{self.auth_base}/authorize?" + urlencode(params)
        
        print("=" * 60)
        print("步骤1: 获取用户授权")
        print("=" * 60)
        print("请在浏览器中访问以下URL进行授权：")
        print(auth_url)
        print("\n授权后会跳转到回调URL，请复制URL中的code参数")
        print("=" * 60)
        
        return auth_url
    
    def step2_exchange_token(self, auth_code):
        """步骤2: 用授权码换取access_token"""
        print("\n" + "=" * 60)
        print("步骤2: 交换Access Token")
        print("=" * 60)
        
        url = f"{self.auth_base}/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code',
            'code': auth_code
        }
        
        try:
            response = requests.post(url, data=data)
            result = response.json()
            
            if 'access_token' in result:
                self.access_token = result['access_token']
                self.refresh_token = result.get('refresh_token')
                
                print("✅ Token获取成功！")
                print(f"Access Token: {self.access_token[:20]}...")
                print(f"Token类型: {result.get('token_type', 'Bearer')}")
                print(f"过期时间: {result.get('expires_in', 0)}秒")
                
                # 保存token到文件
                with open('api_tokens.json', 'w') as f:
                    json.dump(result, f, indent=2)
                print("\n已保存到 api_tokens.json")
                
                return True
            else:
                print(f"❌ Token获取失败: {result}")
                return False
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return False
    
    def step3_test_api(self):
        """步骤3: 测试API调用"""
        if not self.access_token:
            print("❌ 请先获取access_token")
            return
        
        print("\n" + "=" * 60)
        print("步骤3: 测试API调用")
        print("=" * 60)
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # 测试1: 获取用户信息
        print("\n测试1: 获取用户信息...")
        try:
            response = requests.get(
                f"{self.api_base}/user/info",
                headers=headers
            )
            if response.status_code == 200:
                user_info = response.json()
                print(f"✅ 用户信息: {json.dumps(user_info, ensure_ascii=False, indent=2)}")
            else:
                print(f"❌ 获取失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        
        # 测试2: 列出用户文档
        print("\n测试2: 列出用户文档...")
        try:
            response = requests.get(
                f"{self.api_base}/drive/v2/files",
                headers=headers,
                params={
                    'limit': 10,
                    'orderBy': 'modifiedTime'
                }
            )
            if response.status_code == 200:
                files = response.json()
                print(f"✅ 文档列表: {json.dumps(files, ensure_ascii=False, indent=2)[:500]}...")
                
                # 如果有文档，尝试导出第一个
                if files.get('files'):
                    first_file = files['files'][0]
                    print(f"\n找到文档: {first_file.get('name')}")
                    print(f"文档ID: {first_file.get('fileID')}")
            else:
                print(f"❌ 获取失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    def test_document_export(self, file_id):
        """测试文档导出功能"""
        if not self.access_token:
            print("❌ 请先获取access_token")
            return
        
        print("\n" + "=" * 60)
        print("测试文档导出")
        print("=" * 60)
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # 发起异步导出请求
        print(f"正在导出文档 {file_id}...")
        response = requests.post(
            f"{self.api_base}/drive/v2/files/{file_id}/async-export",
            headers=headers,
            json={'exportType': 'csv'}  # 导出为CSV
        )
        
        if response.status_code == 200:
            result = response.json()
            operation_id = result.get('operationID')
            print(f"✅ 导出任务已创建: {operation_id}")
            
            # 轮询导出进度
            for i in range(10):
                time.sleep(2)
                progress_response = requests.get(
                    f"{self.api_base}/drive/v2/files/{file_id}/export-progress",
                    headers=headers,
                    params={'operationID': operation_id}
                )
                
                if progress_response.status_code == 200:
                    progress = progress_response.json()
                    if progress['data']['progress'] == 100:
                        download_url = progress['data']['url']
                        print(f"✅ 导出完成！")
                        print(f"下载链接: {download_url}")
                        
                        # 下载文件
                        csv_response = requests.get(download_url)
                        with open('exported_document.csv', 'wb') as f:
                            f.write(csv_response.content)
                        print("✅ 已保存到 exported_document.csv")
                        break
                    else:
                        print(f"导出进度: {progress['data']['progress']}%")
        else:
            print(f"❌ 导出失败: {response.status_code} - {response.text}")

def main():
    """主测试流程"""
    print("腾讯文档API测试工具")
    print("=" * 60)
    
    tester = TencentDocsAPITester()
    
    # 步骤1: 生成授权URL
    auth_url = tester.step1_get_auth_url()
    
    # 等待用户输入授权码
    print("\n请完成授权后，输入获得的code参数：")
    auth_code = input("Code: ").strip()
    
    # 步骤2: 交换token
    if tester.step2_exchange_token(auth_code):
        # 步骤3: 测试API
        tester.step3_test_api()
        
        # 如果需要测试导出功能
        print("\n是否测试文档导出？(输入文档ID或按回车跳过)")
        file_id = input("文档ID: ").strip()
        if file_id:
            tester.test_document_export(file_id)
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()