/**
 * 腾讯文档自动化服务 - 现代API客户端
 * 支持请求/响应拦截器、错误处理、重试机制、缓存
 * 基于Fetch API，提供现代化的异步接口
 */

/* ===== HTTP状态码常量 ===== */
const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503
};

/* ===== API错误类 ===== */
class APIError extends Error {
  constructor(message, status, code, details = null) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.code = code;
    this.details = details;
    this.timestamp = new Date().toISOString();
  }
  
  // 判断是否为网络错误
  get isNetworkError() {
    return this.status === 0 || this.code === 'NETWORK_ERROR';
  }
  
  // 判断是否为服务器错误
  get isServerError() {
    return this.status >= 500;
  }
  
  // 判断是否为客户端错误
  get isClientError() {
    return this.status >= 400 && this.status < 500;
  }
  
  // 判断是否为认证错误
  get isAuthError() {
    return this.status === HTTP_STATUS.UNAUTHORIZED;
  }
  
  // 转换为用户友好的错误信息
  getUserFriendlyMessage() {
    const messages = {
      400: '请求参数有误，请检查输入内容',
      401: '身份验证失败，请重新登录',
      403: '没有权限执行此操作',
      404: '请求的资源不存在',
      500: '服务器内部错误，请稍后重试',
      502: '服务器网关错误，请稍后重试',
      503: '服务暂时不可用，请稍后重试'
    };
    
    if (this.isNetworkError) {
      return '网络连接失败，请检查网络状态';
    }
    
    return messages[this.status] || this.message || '未知错误，请稍后重试';
  }
}

/* ===== 请求重试器 ===== */
class RequestRetrier {
  constructor(options = {}) {
    this.maxRetries = options.maxRetries || 3;
    this.retryDelay = options.retryDelay || 1000;
    this.retryCondition = options.retryCondition || this.defaultRetryCondition;
    this.onRetry = options.onRetry || null;
  }
  
  defaultRetryCondition(error, attemptNumber) {
    // 网络错误或5xx服务器错误才重试
    return (error.isNetworkError || error.isServerError) && attemptNumber < this.maxRetries;
  }
  
  async executeWithRetry(requestFn) {
    let lastError;
    
    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const result = await requestFn();
        return result;
      } catch (error) {
        lastError = error;
        
        // 检查是否应该重试
        if (!this.retryCondition(error, attempt)) {
          break;
        }
        
        // 通知重试事件
        if (this.onRetry) {
          this.onRetry(error, attempt + 1);
        }
        
        // 等待重试延迟
        if (attempt < this.maxRetries) {
          await this.delay(this.retryDelay * Math.pow(2, attempt)); // 指数退避
        }
      }
    }
    
    throw lastError;
  }
  
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/* ===== 响应缓存器 ===== */
class ResponseCache {
  constructor(options = {}) {
    this.maxSize = options.maxSize || 100;
    this.defaultTTL = options.defaultTTL || 300000; // 5分钟
    this.cache = new Map();
  }
  
  generateKey(url, method, body) {
    const key = `${method}:${url}`;
    if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      const bodyStr = typeof body === 'string' ? body : JSON.stringify(body);
      return `${key}:${this.hash(bodyStr)}`;
    }
    return key;
  }
  
  hash(str) {
    let hash = 0;
    if (str.length === 0) return hash;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // 转为32位整数
    }
    return hash.toString();
  }
  
  set(key, data, ttl = this.defaultTTL) {
    // 如果缓存已满，删除最旧的项
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    
    const expiresAt = Date.now() + ttl;
    this.cache.set(key, { data, expiresAt });
  }
  
  get(key) {
    const cached = this.cache.get(key);
    if (!cached) return null;
    
    // 检查是否过期
    if (Date.now() > cached.expiresAt) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.data;
  }
  
  delete(key) {
    this.cache.delete(key);
  }
  
  clear() {
    this.cache.clear();
  }
  
  // 清理过期缓存
  cleanup() {
    const now = Date.now();
    for (const [key, cached] of this.cache.entries()) {
      if (now > cached.expiresAt) {
        this.cache.delete(key);
      }
    }
  }
}

/* ===== 核心API客户端 ===== */
class APIClient {
  constructor(options = {}) {
    this.baseURL = options.baseURL || '/api';
    this.timeout = options.timeout || 30000;
    this.retrier = new RequestRetrier(options.retry);
    this.cache = options.enableCache ? new ResponseCache(options.cache) : null;
    
    // 拦截器
    this.requestInterceptors = [];
    this.responseInterceptors = [];
    
    // 默认配置
    this.defaults = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      credentials: 'same-origin',
      ...options.defaults
    };
    
    // 启动缓存清理定时器
    if (this.cache) {
      setInterval(() => this.cache.cleanup(), 60000); // 每分钟清理一次
    }
  }
  
  /* ===== 拦截器管理 ===== */
  addRequestInterceptor(interceptor) {
    this.requestInterceptors.push(interceptor);
    return this.requestInterceptors.length - 1;
  }
  
  addResponseInterceptor(interceptor) {
    this.responseInterceptors.push(interceptor);
    return this.responseInterceptors.length - 1;
  }
  
  removeRequestInterceptor(id) {
    this.requestInterceptors.splice(id, 1);
  }
  
  removeResponseInterceptor(id) {
    this.responseInterceptors.splice(id, 1);
  }
  
  /* ===== 请求处理 ===== */
  async processRequestInterceptors(config) {
    let processedConfig = { ...config };
    
    for (const interceptor of this.requestInterceptors) {
      try {
        processedConfig = await interceptor(processedConfig) || processedConfig;
      } catch (error) {
        throw new APIError('Request interceptor failed', 0, 'INTERCEPTOR_ERROR', error);
      }
    }
    
    return processedConfig;
  }
  
  async processResponseInterceptors(response, config) {
    let processedResponse = response;
    
    for (const interceptor of this.responseInterceptors) {
      try {
        processedResponse = await interceptor(processedResponse, config) || processedResponse;
      } catch (error) {
        throw new APIError('Response interceptor failed', 0, 'INTERCEPTOR_ERROR', error);
      }
    }
    
    return processedResponse;
  }
  
  /* ===== 核心请求方法 ===== */
  async request(url, options = {}) {
    // 合并配置
    const config = {\n      ...this.defaults,\n      ...options,\n      url: this.resolveURL(url),\n      headers: { ...this.defaults.headers, ...options.headers }\n    };\n    \n    // 处理请求拦截器\n    const processedConfig = await this.processRequestInterceptors(config);\n    \n    // 检查缓存\n    if (this.cache && processedConfig.method === 'GET') {\n      const cacheKey = this.cache.generateKey(processedConfig.url, processedConfig.method);\n      const cached = this.cache.get(cacheKey);\n      if (cached) {\n        return cached;\n      }\n    }\n    \n    // 执行请求（带重试）\n    return await this.retrier.executeWithRetry(async () => {\n      const response = await this.executeRequest(processedConfig);\n      \n      // 处理响应拦截器\n      const processedResponse = await this.processResponseInterceptors(response, processedConfig);\n      \n      // 缓存GET请求响应\n      if (this.cache && processedConfig.method === 'GET' && processedResponse.success) {\n        const cacheKey = this.cache.generateKey(processedConfig.url, processedConfig.method);\n        this.cache.set(cacheKey, processedResponse);\n      }\n      \n      return processedResponse;\n    });\n  }\n  \n  async executeRequest(config) {\n    const controller = new AbortController();\n    const timeoutId = setTimeout(() => controller.abort(), this.timeout);\n    \n    try {\n      const fetchOptions = {\n        method: config.method || 'GET',\n        headers: config.headers,\n        credentials: config.credentials,\n        signal: controller.signal\n      };\n      \n      // 添加请求体\n      if (config.body && config.method !== 'GET' && config.method !== 'HEAD') {\n        if (config.body instanceof FormData) {\n          // FormData不需要设置Content-Type\n          delete fetchOptions.headers['Content-Type'];\n          fetchOptions.body = config.body;\n        } else if (typeof config.body === 'object') {\n          fetchOptions.body = JSON.stringify(config.body);\n        } else {\n          fetchOptions.body = config.body;\n        }\n      }\n      \n      const response = await fetch(config.url, fetchOptions);\n      \n      return await this.handleResponse(response, config);\n      \n    } catch (error) {\n      if (error.name === 'AbortError') {\n        throw new APIError('Request timeout', 0, 'TIMEOUT');\n      } else if (error instanceof TypeError && error.message.includes('fetch')) {\n        throw new APIError('Network error', 0, 'NETWORK_ERROR', error);\n      } else if (error instanceof APIError) {\n        throw error;\n      } else {\n        throw new APIError('Request failed', 0, 'REQUEST_ERROR', error);\n      }\n    } finally {\n      clearTimeout(timeoutId);\n    }\n  }\n  \n  async handleResponse(response, config) {\n    const { status, statusText, headers } = response;\n    \n    let data;\n    const contentType = headers.get('content-type') || '';\n    \n    try {\n      if (contentType.includes('application/json')) {\n        data = await response.json();\n      } else if (contentType.includes('text/')) {\n        data = await response.text();\n      } else {\n        data = await response.blob();\n      }\n    } catch (error) {\n      throw new APIError('Failed to parse response', status, 'PARSE_ERROR', error);\n    }\n    \n    // 检查响应状态\n    if (!response.ok) {\n      const message = data?.error || data?.message || statusText || 'Request failed';\n      const code = data?.code || 'HTTP_ERROR';\n      throw new APIError(message, status, code, data);\n    }\n    \n    return {\n      data,\n      status,\n      statusText,\n      headers: this.parseHeaders(headers),\n      config,\n      success: true\n    };\n  }\n  \n  parseHeaders(headers) {\n    const parsed = {};\n    for (const [key, value] of headers.entries()) {\n      parsed[key] = value;\n    }\n    return parsed;\n  }\n  \n  resolveURL(url) {\n    if (url.startsWith('http://') || url.startsWith('https://')) {\n      return url;\n    }\n    return `${this.baseURL.replace(/\\/$/, '')}/${url.replace(/^\\//, '')}`;\n  }\n  \n  /* ===== 便捷方法 ===== */\n  async get(url, options = {}) {\n    return this.request(url, { ...options, method: 'GET' });\n  }\n  \n  async post(url, body, options = {}) {\n    return this.request(url, { ...options, method: 'POST', body });\n  }\n  \n  async put(url, body, options = {}) {\n    return this.request(url, { ...options, method: 'PUT', body });\n  }\n  \n  async patch(url, body, options = {}) {\n    return this.request(url, { ...options, method: 'PATCH', body });\n  }\n  \n  async delete(url, options = {}) {\n    return this.request(url, { ...options, method: 'DELETE' });\n  }\n  \n  /* ===== 文件上传 ===== */\n  async uploadFile(url, file, options = {}) {\n    const formData = new FormData();\n    \n    if (file instanceof File) {\n      formData.append('file', file);\n    } else if (Array.isArray(file)) {\n      file.forEach((f, index) => {\n        formData.append(`files[${index}]`, f);\n      });\n    }\n    \n    // 添加其他字段\n    if (options.fields) {\n      Object.entries(options.fields).forEach(([key, value]) => {\n        formData.append(key, value);\n      });\n    }\n    \n    return this.post(url, formData, {\n      ...options,\n      onUploadProgress: options.onProgress\n    });\n  }\n  \n  /* ===== 批量请求 ===== */\n  async batch(requests) {\n    const results = await Promise.allSettled(\n      requests.map(req => this.request(req.url, req.options))\n    );\n    \n    return results.map((result, index) => {\n      if (result.status === 'fulfilled') {\n        return { success: true, data: result.value, request: requests[index] };\n      } else {\n        return { success: false, error: result.reason, request: requests[index] };\n      }\n    });\n  }\n  \n  /* ===== 工具方法 ===== */\n  clearCache() {\n    if (this.cache) {\n      this.cache.clear();\n    }\n  }\n  \n  getCacheStats() {\n    if (!this.cache) return null;\n    \n    return {\n      size: this.cache.cache.size,\n      maxSize: this.cache.maxSize\n    };\n  }\n}\n\n/* ===== 腾讯文档API客户端 ===== */\nclass TencentDocAPI extends APIClient {\n  constructor(options = {}) {\n    super({\n      baseURL: '/api',\n      enableCache: true,\n      retry: {\n        maxRetries: 3,\n        retryDelay: 1000,\n        onRetry: (error, attempt) => {\n          console.log(`Request failed, retrying (${attempt}/3):`, error.message);\n        }\n      },\n      ...options\n    });\n    \n    this.setupDefaultInterceptors();\n  }\n  \n  setupDefaultInterceptors() {\n    // 请求拦截器：添加认证信息\n    this.addRequestInterceptor((config) => {\n      const token = this.getAuthToken();\n      if (token) {\n        config.headers.Authorization = `Bearer ${token}`;\n      }\n      return config;\n    });\n    \n    // 请求拦截器：添加请求ID用于追踪\n    this.addRequestInterceptor((config) => {\n      config.headers['X-Request-ID'] = this.generateRequestId();\n      return config;\n    });\n    \n    // 响应拦截器：处理通用错误\n    this.addResponseInterceptor((response, config) => {\n      // 记录API调用\n      this.logAPICall(config, response);\n      return response;\n    });\n    \n    // 响应拦截器：自动处理认证过期\n    this.addResponseInterceptor(async (response, config) => {\n      if (response.status === HTTP_STATUS.UNAUTHORIZED) {\n        // 清除过期的认证信息\n        this.clearAuth();\n        \n        // 触发重新认证事件\n        window.dispatchEvent(new CustomEvent('auth:required', {\n          detail: { response, config }\n        }));\n      }\n      return response;\n    });\n  }\n  \n  /* ===== 认证相关 ===== */\n  getAuthToken() {\n    return localStorage.getItem('auth_token');\n  }\n  \n  setAuthToken(token) {\n    localStorage.setItem('auth_token', token);\n  }\n  \n  clearAuth() {\n    localStorage.removeItem('auth_token');\n    localStorage.removeItem('user_info');\n  }\n  \n  generateRequestId() {\n    return Math.random().toString(36).substring(2) + Date.now().toString(36);\n  }\n  \n  logAPICall(config, response) {\n    if (process.env.NODE_ENV !== 'production') {\n      console.log(`API ${config.method} ${config.url}:`, {\n        status: response.status,\n        requestId: config.headers['X-Request-ID'],\n        duration: Date.now() - config.startTime\n      });\n    }\n  }\n  \n  /* ===== 腾讯文档专用API方法 ===== */\n  \n  // 健康检查\n  async healthCheck() {\n    return this.get('health');\n  }\n  \n  // Cookie管理\n  async saveCookies(username, cookies) {\n    return this.post('save_cookies', { username, cookies });\n  }\n  \n  // 文档下载\n  async downloadDocument(docUrl, username, format = 'excel') {\n    return this.post('download', {\n      doc_url: docUrl,\n      username,\n      format\n    });\n  }\n  \n  // 文档上传\n  async uploadDocument(file, username, options = {}) {\n    return this.uploadFile('upload', file, {\n      fields: { username },\n      ...options\n    });\n  }\n  \n  // 文档分析\n  async analyzeDocument(file, options = {}) {\n    return this.uploadFile('analyze', file, options);\n  }\n  \n  // 文档修改\n  async modifyDocument(filePath, modifications) {\n    return this.post('modify', {\n      file_path: filePath,\n      modifications\n    });\n  }\n  \n  // 获取历史记录\n  async getHistory(username, limit = 50) {\n    return this.get(`history?username=${encodeURIComponent(username)}&limit=${limit}`);\n  }\n  \n  // 下载文件\n  async downloadFile(filename) {\n    const response = await this.get(`download_file/${encodeURIComponent(filename)}`, {\n      headers: {\n        'Accept': 'application/octet-stream'\n      }\n    });\n    \n    return response.data; // Blob对象\n  }\n  \n  /* ===== 批量操作 ===== */\n  async batchDownload(documents) {\n    const requests = documents.map(doc => ({\n      url: 'download',\n      options: {\n        method: 'POST',\n        body: doc\n      }\n    }));\n    \n    return this.batch(requests);\n  }\n  \n  async batchUpload(files, username) {\n    const requests = files.map(file => ({\n      url: 'upload',\n      options: {\n        method: 'POST',\n        body: (() => {\n          const formData = new FormData();\n          formData.append('file', file);\n          formData.append('username', username);\n          return formData;\n        })()\n      }\n    }));\n    \n    return this.batch(requests);\n  }\n}\n\n/* ===== 全局错误处理器 ===== */\nclass GlobalErrorHandler {\n  constructor(apiClient) {\n    this.apiClient = apiClient;\n    this.setupGlobalHandlers();\n  }\n  \n  setupGlobalHandlers() {\n    // 全局未处理的Promise拒绝\n    window.addEventListener('unhandledrejection', (event) => {\n      if (event.reason instanceof APIError) {\n        this.handleAPIError(event.reason);\n        event.preventDefault();\n      }\n    });\n    \n    // 认证相关事件\n    window.addEventListener('auth:required', (event) => {\n      this.handleAuthRequired(event.detail);\n    });\n  }\n  \n  handleAPIError(error) {\n    // 根据错误类型显示不同的提示\n    if (error.isNetworkError) {\n      this.showNetworkError();\n    } else if (error.isAuthError) {\n      this.showAuthError();\n    } else if (error.isServerError) {\n      this.showServerError(error);\n    } else {\n      this.showGeneralError(error);\n    }\n    \n    // 记录错误\n    this.logError(error);\n  }\n  \n  handleAuthRequired({ response, config }) {\n    // 显示登录提示\n    if (window.Components && window.Components.Toast) {\n      window.Components.Toast.warning('登录已过期，请重新登录');\n    }\n    \n    // 可以触发登录模态框等\n    window.dispatchEvent(new CustomEvent('app:showLogin'));\n  }\n  \n  showNetworkError() {\n    if (window.Components && window.Components.Toast) {\n      window.Components.Toast.error('网络连接失败，请检查网络设置');\n    }\n  }\n  \n  showAuthError() {\n    if (window.Components && window.Components.Toast) {\n      window.Components.Toast.warning('身份验证失败，请重新登录');\n    }\n  }\n  \n  showServerError(error) {\n    if (window.Components && window.Components.Toast) {\n      window.Components.Toast.error(`服务器错误: ${error.getUserFriendlyMessage()}`);\n    }\n  }\n  \n  showGeneralError(error) {\n    if (window.Components && window.Components.Toast) {\n      window.Components.Toast.error(error.getUserFriendlyMessage());\n    }\n  }\n  \n  logError(error) {\n    console.error('API Error:', {\n      message: error.message,\n      status: error.status,\n      code: error.code,\n      details: error.details,\n      timestamp: error.timestamp,\n      stack: error.stack\n    });\n    \n    // 在生产环境中可以发送错误到监控服务\n    if (process.env.NODE_ENV === 'production') {\n      // 发送错误报告\n      this.reportError(error);\n    }\n  }\n  \n  async reportError(error) {\n    try {\n      // 发送错误报告到监控服务\n      // await this.apiClient.post('/api/errors', {\n      //   error: error.message,\n      //   status: error.status,\n      //   code: error.code,\n      //   userAgent: navigator.userAgent,\n      //   url: window.location.href,\n      //   timestamp: error.timestamp\n      // });\n    } catch (reportingError) {\n      console.error('Failed to report error:', reportingError);\n    }\n  }\n}\n\n/* ===== 请求状态管理器 ===== */\nclass RequestStateManager {\n  constructor() {\n    this.pendingRequests = new Set();\n    this.requestStates = new Map();\n  }\n  \n  startRequest(requestId, config) {\n    this.pendingRequests.add(requestId);\n    this.requestStates.set(requestId, {\n      status: 'pending',\n      startTime: Date.now(),\n      config\n    });\n    \n    this.notifyStateChange();\n  }\n  \n  finishRequest(requestId, success, data) {\n    this.pendingRequests.delete(requestId);\n    const state = this.requestStates.get(requestId);\n    \n    if (state) {\n      state.status = success ? 'success' : 'error';\n      state.endTime = Date.now();\n      state.duration = state.endTime - state.startTime;\n      state.data = data;\n    }\n    \n    this.notifyStateChange();\n  }\n  \n  notifyStateChange() {\n    window.dispatchEvent(new CustomEvent('api:stateChange', {\n      detail: {\n        pendingCount: this.pendingRequests.size,\n        hasPending: this.pendingRequests.size > 0\n      }\n    }));\n  }\n  \n  hasPendingRequests() {\n    return this.pendingRequests.size > 0;\n  }\n  \n  getPendingCount() {\n    return this.pendingRequests.size;\n  }\n}\n\n/* ===== 导出和初始化 ===== */\nconst apiClient = new TencentDocAPI();\nconst errorHandler = new GlobalErrorHandler(apiClient);\nconst stateManager = new RequestStateManager();\n\n// 添加请求状态管理\napiClient.addRequestInterceptor((config) => {\n  const requestId = config.headers['X-Request-ID'];\n  stateManager.startRequest(requestId, config);\n  config.startTime = Date.now();\n  return config;\n});\n\napiClient.addResponseInterceptor((response, config) => {\n  const requestId = config.headers['X-Request-ID'];\n  stateManager.finishRequest(requestId, response.success, response.data);\n  return response;\n});\n\n// 导出到全局\nwindow.API = {\n  client: apiClient,\n  TencentDocAPI,\n  APIClient,\n  APIError,\n  HTTP_STATUS,\n  errorHandler,\n  stateManager\n};\n\n// 默认导出\nwindow.api = apiClient;