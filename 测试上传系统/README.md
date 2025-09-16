# 腾讯文档上传测试系统 - Windows可视化调试版

## 📁 文件结构

```
测试上传系统/
├── tencent_upload_enhanced.py    # 核心上传模块
├── upload_test_server_8109.py    # Web界面服务器
├── visual_debug.py                # 可视化调试工具
├── test_real_upload.py            # 命令行测试工具
├── config/
│   └── cookies.json               # Cookie配置文件
├── test_files/
│   └── test_upload_20250909.xlsx # 测试Excel文件
├── logs/                          # 日志目录
├── docs/                          # 文档目录
├── requirements.txt               # Python依赖
├── windows_setup.bat              # Windows环境设置
├── 启动可视化调试.bat              # 快速启动可视化调试
└── 启动Web界面.bat                 # 快速启动Web界面
```

## 🚀 快速开始（Windows）

### 1. 环境准备

```bash
# 方式1：双击运行
windows_setup.bat

# 方式2：命令行运行
pip install -r requirements.txt
playwright install chromium
```

### 2. 配置Cookie

编辑 `config/cookies.json` 文件，添加您的腾讯文档Cookie：

```json
{
  "cookie_string": "您的完整Cookie字符串",
  "last_updated": "2025-09-09 23:00:00"
}
```

获取Cookie方法：
1. 登录腾讯文档网页版
2. 按F12打开开发者工具
3. 进入Application/Storage/Cookies
4. 复制所有Cookie拼接成字符串

### 3. 运行测试

#### 方式1：可视化调试（推荐）
```bash
# 双击运行
启动可视化调试.bat

# 或命令行
python visual_debug.py
```

特点：
- ✅ 可以看到浏览器操作过程
- ✅ 支持交互式调试
- ✅ 便于定位问题

#### 方式2：Web界面
```bash
# 双击运行
启动Web界面.bat

# 或命令行
python upload_test_server_8109.py
```

然后访问：http://localhost:8109

特点：
- ✅ 友好的Web界面
- ✅ 拖拽上传文件
- ✅ Cookie自动保存

#### 方式3：命令行测试
```bash
python test_real_upload.py
```

## 🔍 可视化调试器功能

### 交互式模式

启动后选择"交互式调试"，支持以下操作：

1. **上传测试文件** - 使用预置的Excel文件测试
2. **上传自定义文件** - 指定任意文件路径
3. **重新加载Cookie** - 刷新认证信息
4. **访问腾讯文档主页** - 导航到主页
5. **等待观察** - 暂停30秒手动操作

### 快速测试模式

自动执行完整上传流程：
1. 启动浏览器（可见）
2. 加载Cookie
3. 上传测试文件
4. 显示结果

## 📊 测试文件说明

`test_files/test_upload_20250909.xlsx` 包含：

| 产品名称 | 风险等级 | 标记颜色 |
|---------|---------|---------|
| 产品A,B,F | L1 | 正常 |
| 产品C,D | L2 | 黄色 |
| 产品E,G | L3 | 红色 |

## 🐛 调试技巧

### 1. 查看日志
```bash
# 实时日志在控制台显示
# 历史日志保存在 logs/debug.log
```

### 2. 常见问题

**问题：Cookie认证失败**
- 解决：重新获取最新的Cookie
- 检查：Cookie是否包含DOC_SID和SID字段

**问题：文件选择器超时**
- 解决：使用可视化模式观察实际情况
- 可能需要手动点击确认按钮

**问题：上传后无法获取URL**
- 解决：等待时间可能不够，增加超时时间
- 检查：网络连接是否稳定

### 3. 修改调试参数

编辑 `visual_debug.py`：

```python
# 修改为headless模式（后台运行）
await self.uploader.start_browser(headless=True)

# 增加等待时间
await asyncio.sleep(60)  # 等待60秒
```

## 🔧 高级配置

### 代理设置

如需使用代理，修改 `tencent_upload_enhanced.py`：

```python
self.browser = await p.chromium.launch(
    headless=False,
    proxy={
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass"
    }
)
```

### 自定义选择器

如果腾讯文档UI更新，修改选择器：

```python
self.selectors = {
    'import_button': '新的选择器',
    'confirm_button': '新的选择器'
}
```

## 📝 API文档

### TencentDocUploadEnhanced 类

主要方法：

```python
# 启动浏览器
await uploader.start_browser(headless=False)

# 设置Cookie
await uploader.login_with_cookies(cookie_string)

# 上传文件
result = await uploader.upload_file(file_path)

# 清理资源
await uploader.cleanup()
```

### 返回结果格式

```json
{
  "success": true,
  "url": "https://docs.qq.com/sheet/xxx",
  "filename": "上传的文件名",
  "message": "上传成功"
}
```

## 🌐 网络要求

- 需要访问：https://docs.qq.com
- 建议网络：稳定的互联网连接
- 防火墙：允许Chromium浏览器访问

## 📞 技术支持

遇到问题时：

1. 查看 `logs/debug.log` 日志文件
2. 使用可视化模式观察操作过程
3. 检查Cookie是否有效
4. 确认网络连接正常

## 🔄 更新记录

### v1.0.0 (2025-09-09)
- ✅ 初始版本发布
- ✅ 支持Windows可视化调试
- ✅ Cookie自动保存功能
- ✅ 交互式调试模式
- ✅ Web界面上传
- ✅ 完整错误处理

## 📄 许可证

内部测试使用，请勿外传。

---

*最后更新：2025-09-09 23:50*