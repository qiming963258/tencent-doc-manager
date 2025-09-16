# Cookie自动保存功能 - 使用指南

## ✅ 功能已实现

Cookie自动保存功能已成功添加到8109端口的上传测试页面。

## 🚀 功能特性

### 1. **自动保存**
- 当您在Cookie输入框中粘贴内容时，系统会自动保存
- 输入时有1秒防抖延迟，避免频繁保存
- 保存成功后显示绿色提示："✅ Cookie已自动保存"

### 2. **自动加载**
- 页面刷新或重新访问时，自动加载已保存的Cookie
- 无需重复输入，提高使用效率

### 3. **持久化存储**
- Cookie保存在：`/root/projects/tencent-doc-manager/config/cookies.json`
- 包含完整的Cookie字符串和解析后的键值对
- 记录最后更新时间

## 📋 使用步骤

### 1. 访问测试页面
```
http://202.140.143.88:8109
```

### 2. 粘贴Cookie
- 从浏览器复制腾讯文档的完整Cookie字符串
- 粘贴到"Cookie认证字符串"输入框
- 系统会自动保存，显示绿色确认提示

### 3. 上传文件
- Cookie保存后，选择要上传的Excel文件
- 点击"开始上传"按钮
- 系统会使用保存的Cookie进行认证

## 🔧 技术实现

### 前端JavaScript
```javascript
// 粘贴时立即保存
onpaste="handleCookiePaste()"

// 输入时防抖保存（1秒延迟）
oninput="saveCookieDebounced()"

// 页面加载时自动获取
window.addEventListener('DOMContentLoaded', loadSavedCookie)
```

### 后端API
- `POST /save_cookie` - 保存Cookie到配置文件
- `GET /get_saved_cookie` - 获取已保存的Cookie

### 配置文件格式
```json
{
  "cookies": [
    {"name": "key1", "value": "value1"},
    {"name": "key2", "value": "value2"}
  ],
  "cookie_string": "key1=value1; key2=value2",
  "last_updated": "2025-09-09 22:04:00"
}
```

## 🎯 优势

1. **用户体验提升**
   - 无需每次手动输入Cookie
   - 粘贴即保存，简化操作流程

2. **数据持久化**
   - Cookie保存在服务器端
   - 重启服务器后仍然有效

3. **可视化反馈**
   - 实时显示保存状态
   - 颜色编码（绿色成功，红色失败）

## ⚠️ 注意事项

1. **Cookie有效期**
   - 腾讯文档Cookie可能会过期
   - 如果上传失败，请重新获取Cookie

2. **安全性**
   - Cookie包含敏感信息
   - 请确保服务器安全
   - 不要在公共网络暴露此服务

## 📊 当前状态

- ✅ Cookie自动保存功能正常工作
- ✅ 页面自动加载已保存的Cookie
- ✅ 服务器正在运行：http://202.140.143.88:8109
- ✅ 已保存您提供的Cookie（58个键值对）

---

*更新时间: 2025-09-09 22:05*