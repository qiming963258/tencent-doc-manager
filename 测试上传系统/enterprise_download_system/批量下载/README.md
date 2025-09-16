# 腾讯文档极简批量下载器

![状态](https://img.shields.io/badge/Status-Ready-brightgreen)
![版本](https://img.shields.io/badge/Version-1.0-blue)
![Python](https://img.shields.io/badge/Python-3.7%2B-orange)

## 🎯 功能说明

**一个极简的腾讯文档批量下载工具**，只需输入Cookie即可自动批量下载所有文档。

### ✨ 核心特性

- 🔐 **Cookie验证** - 自动验证Cookie有效性
- 🔍 **智能筛选** - 自动设置"我所有"+"近一个月"筛选条件
- 📜 **滚动加载** - 自动滚动直到加载所有文件
- 🖱️ **右键下载** - 逐个右键点击文件，选择下载
- 📁 **统一存储** - 所有文件下载到downloads目录

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装Python依赖
pip install playwright

# 安装浏览器
playwright install chromium
```

### 2. 获取Cookie

1. 打开Chrome浏览器，访问 https://docs.qq.com
2. 登录你的腾讯文档账户
3. 按F12打开开发者工具
4. 切换到"Application"(应用)选项卡
5. 左侧选择"Cookies" → "https://docs.qq.com"
6. 复制所有Cookie值，格式如：`RK=xxx; ptcz=xxx; uid=xxx; ...`

### 3. 运行下载器

```bash
python downloader.py
```

输入Cookie后，程序将自动：
1. 验证Cookie有效性
2. 设置筛选条件（我所有+近一个月）
3. 滚动加载所有文件
4. 逐个右键下载每个文件

## 📁 项目结构

```
enterprise_download_system/
├── downloader.py          # 主程序（单文件下载器）
├── requirements.txt       # Python依赖
├── config.json           # 配置文件（可选）
├── downloads/            # 下载文件存储目录
└── README.md            # 使用说明
```

## ⚙️ 技术实现

### 核心技术栈
- **Playwright** - 现代浏览器自动化框架
- **Python 3.7+** - 基础运行环境
- **Chrome/Chromium** - 自动化浏览器

### 下载流程
1. **Cookie注入** - 将用户Cookie注入浏览器上下文
2. **登录验证** - 访问腾讯文档主页，验证登录状态
3. **筛选设置** - 自动点击筛选按钮，设置条件
4. **内容加载** - 滚动页面直到加载完所有文件
5. **批量下载** - 逐个右键点击文件，选择下载选项
6. **文件保存** - 下载的文件自动保存到downloads目录

### 关键特性
- **智能元素定位** - 支持多种CSS选择器，适应页面结构变化
- **错误重试机制** - 下载失败时自动跳过，继续处理下一个文件
- **进度显示** - 实时显示下载进度和文件信息
- **无头模式** - 支持服务器环境运行（可在配置中开启）

## 🔧 配置说明

### config.json配置项

```json
{
  "browser": {
    "headless": false,        # 是否无头模式（false=显示浏览器窗口）
    "timeout": 30000,         # 页面加载超时时间（毫秒）
    "viewport": {             # 浏览器窗口大小
      "width": 1920,
      "height": 1080
    }
  },
  "download": {
    "directory": "downloads",           # 下载目录
    "max_scroll_attempts": 50,         # 最大滚动次数
    "scroll_wait_time": 2000,          # 滚动等待时间（毫秒）
    "download_wait_time": 1500,        # 下载等待时间（毫秒）
    "stable_scroll_count": 3           # 稳定滚动计数（连续几次无新内容）
  }
}
```

### 自定义配置
- **服务器环境**: 将`headless`设为`true`
- **下载速度**: 调整`download_wait_time`和`scroll_wait_time`
- **下载目录**: 修改`directory`路径

## ⚠️ 注意事项

### 使用限制
- 仅支持下载有权限访问的文档
- 请遵守腾讯文档的使用条款
- 避免在高峰时段进行大量下载
- Cookie有时效性，需定期更新

### 故障排除

**Cookie无效**
- 重新登录腾讯文档获取新Cookie
- 确保Cookie格式正确（包含所有必需字段）

**下载失败**
- 检查网络连接稳定性
- 确认账户对文档有下载权限
- 查看终端输出的错误信息

**页面元素找不到**
- 腾讯文档可能更新了页面结构
- 联系开发者更新元素选择器

## 📊 使用示例

### 输入示例
```
请输入腾讯文档Cookie字符串:
🔑 Cookie: RK=nI/1/PDC5y; ptcz=578cdfe2a37d597cc98734b933efee8f49efc3b1724d2a91c03f3c6f8afc9d9c; uid=144115414584628119; ...
```

### 输出示例
```
🚀 启动浏览器...
✅ 浏览器设置完成
🔍 验证Cookie有效性...
✅ Cookie验证成功，已登录
🔧 设置筛选条件...
✅ 已点击筛选按钮
✅ 筛选条件设置完成
📜 开始滚动加载所有文件...
✅ 滚动加载完成，总共发现 25 个文件
🎯 开始批量下载...
📄 处理第 1/25 个文件...
⬇️  下载: 工作计划表.xlsx
✅ 完成: 工作计划表.xlsx
...
🎉 批量下载完成！
✅ 成功处理: 25/25 个文件
📁 文件保存在: /path/to/downloads
```

## 🔒 安全说明

- Cookie包含敏感信息，请妥善保管
- 建议在可信的网络环境中使用
- 定期清理下载目录和浏览器缓存
- 不要分享包含个人Cookie的截图或日志

## 📞 技术支持

如有问题或建议：
- 查看终端输出的详细错误信息
- 确认网络连接和Cookie有效性
- 检查腾讯文档页面是否可正常访问

---

**开发**: Claude Code AI  
**版本**: 1.0  
**最后更新**: 2025-08-20