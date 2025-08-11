/**
 * 高级错误处理和用户反馈系统
 * 提供错误边界、自动重试、用户友好的错误提示和错误上报
 */

class ErrorBoundary {
  constructor(options = {}) {
    this.options = {
      maxRetries: 3,
      retryDelay: 1000,
      enableErrorReporting: true,
      enableUserFeedback: true,
      fallbackUI: null,
      onError: null,
      ...options
    };

    this.errorCount = 0;
    this.retryCount = new Map();
    this.errorHistory = [];
    this.setupGlobalHandlers();
  }

  setupGlobalHandlers() {
    // 捕获未处理的Promise拒绝
    window.addEventListener('unhandledrejection', (event) => {
      this.handleError(event.reason, 'unhandledrejection', {
        promise: event.promise,
        preventDefault: () => event.preventDefault()
      });
    });

    // 捕获JavaScript错误
    window.addEventListener('error', (event) => {
      this.handleError(event.error || event, 'javascript', {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        preventDefault: () => event.preventDefault()
      });
    });

    // 捕获资源加载错误
    window.addEventListener('error', (event) => {
      if (event.target !== window && event.target.tagName) {
        this.handleResourceError(event);
      }
    }, true);

    // 网络状态变化
    window.addEventListener('online', () => {
      this.handleNetworkStatusChange(true);
    });

    window.addEventListener('offline', () => {
      this.handleNetworkStatusChange(false);
    });
  }

  async handleError(error, type, context = {}) {
    this.errorCount++;
    
    const errorInfo = {
      id: this.generateErrorId(),
      timestamp: Date.now(),
      type,
      message: error.message || error.toString(),
      stack: error.stack,
      userAgent: navigator.userAgent,
      url: window.location.href,
      context,
      retryCount: this.retryCount.get(error.message) || 0
    };

    this.errorHistory.push(errorInfo);
    
    // 限制错误历史数量
    if (this.errorHistory.length > 100) {
      this.errorHistory = this.errorHistory.slice(-50);
    }

    // 调用用户定义的错误处理器
    if (this.options.onError) {
      try {
        await this.options.onError(errorInfo);
      } catch (handlerError) {
        console.error('Error in error handler:', handlerError);
      }
    }

    // 判断是否应该重试
    if (this.shouldRetry(errorInfo)) {
      return this.retryOperation(errorInfo);
    }

    // 显示用户友好的错误提示
    if (this.options.enableUserFeedback) {
      this.showUserFeedback(errorInfo);
    }

    // 上报错误
    if (this.options.enableErrorReporting) {
      this.reportError(errorInfo);
    }

    // 降级处理
    this.handleGracefulDegradation(errorInfo);
  }

  handleResourceError(event) {
    const element = event.target;
    const errorInfo = {
      id: this.generateErrorId(),
      timestamp: Date.now(),
      type: 'resource',
      message: `Failed to load ${element.tagName}: ${element.src || element.href}`,
      element: {
        tagName: element.tagName,
        src: element.src,
        href: element.href
      },
      retryCount: 0
    };

    this.errorHistory.push(errorInfo);

    // 尝试重新加载资源
    if (this.shouldRetryResource(element)) {
      this.retryResourceLoad(element, errorInfo);
    } else {
      this.handleResourceFallback(element, errorInfo);
    }
  }

  shouldRetry(errorInfo) {
    const retryableErrors = [
      'NetworkError',
      'TimeoutError',
      'AbortError',
      'fetch',
      'XMLHttpRequest'
    ];

    const isRetryable = retryableErrors.some(pattern => 
      errorInfo.message.includes(pattern) || 
      errorInfo.type.includes(pattern)
    );

    return isRetryable && errorInfo.retryCount < this.options.maxRetries;
  }

  async retryOperation(errorInfo) {
    const retryKey = errorInfo.message;
    const currentRetries = this.retryCount.get(retryKey) || 0;
    
    if (currentRetries >= this.options.maxRetries) {
      return false;
    }

    this.retryCount.set(retryKey, currentRetries + 1);

    // 指数退避延迟
    const delay = this.options.retryDelay * Math.pow(2, currentRetries);
    
    await this.sleep(delay);

    // 显示重试提示
    if (window.Components?.Toast) {
      window.Components.Toast.info(
        `正在重试操作... (${currentRetries + 1}/${this.options.maxRetries})`,
        '自动重试'
      );
    }

    return true;
  }

  shouldRetryResource(element) {
    return !element.dataset.retryAttempted && 
           (element.tagName === 'IMG' || element.tagName === 'SCRIPT' || element.tagName === 'LINK');
  }

  async retryResourceLoad(element, errorInfo) {
    element.dataset.retryAttempted = 'true';
    
    await this.sleep(2000);

    const newElement = element.cloneNode(true);
    newElement.removeAttribute('data-retry-attempted');
    
    // 添加时间戳避免缓存
    if (element.src) {
      const url = new URL(element.src);
      url.searchParams.set('retry', Date.now().toString());
      newElement.src = url.toString();
    }

    element.parentNode.replaceChild(newElement, element);
  }

  handleResourceFallback(element, errorInfo) {
    if (element.tagName === 'IMG') {
      // 图片加载失败，显示占位符
      element.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YwZjBmMCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5OTk5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5JbWFnZSBOb3QgRm91bmQ8L3RleHQ+PC9zdmc+';
      element.alt = '图片加载失败';
    } else if (element.tagName === 'SCRIPT') {
      // 脚本加载失败，移除元素避免阻塞
      element.remove();
    }
  }

  showUserFeedback(errorInfo) {
    const userMessage = this.generateUserFriendlyMessage(errorInfo);
    
    if (window.Components?.Toast) {
      const toastType = this.getErrorSeverity(errorInfo);
      window.Components.Toast[toastType](userMessage, '操作失败');
    } else {
      // 降级到原生alert
      if (this.getErrorSeverity(errorInfo) === 'error') {
        alert(userMessage);
      }
    }

    // 如果错误严重，显示详细的错误报告界面
    if (this.isSeviereError(errorInfo)) {
      this.showErrorReportDialog(errorInfo);
    }
  }

  generateUserFriendlyMessage(errorInfo) {
    const messageMap = {
      'NetworkError': '网络连接失败，请检查您的网络设置',
      'TimeoutError': '请求超时，请稍后重试',
      'AbortError': '操作被取消',
      'TypeError': '数据格式错误，请刷新页面重试',
      'SyntaxError': '页面资源加载异常，请刷新页面',
      'unhandledrejection': '操作执行失败，请重试',
      'resource': '资源加载失败，可能影响部分功能'
    };

    for (const [key, message] of Object.entries(messageMap)) {
      if (errorInfo.message.includes(key) || errorInfo.type.includes(key)) {
        return message;
      }
    }

    return '操作失败，请稍后重试';
  }

  getErrorSeverity(errorInfo) {
    const severePatterns = ['TypeError', 'ReferenceError', 'SyntaxError'];
    const isSefire = severePatterns.some(pattern => 
      errorInfo.message.includes(pattern)
    );

    if (isSefire || this.errorCount > 5) {
      return 'error';
    } else if (errorInfo.type === 'resource') {
      return 'warning';
    } else {
      return 'info';
    }
  }

  isSeviereError(errorInfo) {
    return this.getErrorSeverity(errorInfo) === 'error' || 
           this.errorCount > 10;
  }

  showErrorReportDialog(errorInfo) {
    // 创建错误报告对话框
    const modal = document.createElement('div');
    modal.className = 'error-report-modal fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
    
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div class="flex items-center mb-4">
          <div class="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center mr-3">
            <i class="bi bi-exclamation-triangle text-red-600"></i>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900">遇到了问题</h3>
            <p class="text-sm text-gray-600">应用运行时发生了异常</p>
          </div>
        </div>
        
        <div class="mb-6">
          <p class="text-sm text-gray-700 mb-2">${this.generateUserFriendlyMessage(errorInfo)}</p>
          <details class="text-xs text-gray-500">
            <summary class="cursor-pointer hover:text-gray-700">技术详情</summary>
            <pre class="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto max-h-32">${errorInfo.stack || errorInfo.message}</pre>
          </details>
        </div>
        
        <div class="flex gap-3 justify-end">
          <button id="dismissError" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors">
            忽略
          </button>
          <button id="reloadPage" class="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors">
            刷新页面
          </button>
          <button id="reportError" class="px-4 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors">
            报告问题
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // 绑定事件
    modal.querySelector('#dismissError').onclick = () => {
      document.body.removeChild(modal);
    };

    modal.querySelector('#reloadPage').onclick = () => {
      window.location.reload();
    };

    modal.querySelector('#reportError').onclick = () => {
      this.reportError(errorInfo, true);
      document.body.removeChild(modal);
    };

    // 点击背景关闭
    modal.onclick = (e) => {
      if (e.target === modal) {
        document.body.removeChild(modal);
      }
    };
  }

  async reportError(errorInfo, userTriggered = false) {
    try {
      const report = {
        ...errorInfo,
        userTriggered,
        sessionId: this.getSessionId(),
        errorCount: this.errorCount,
        recentErrors: this.errorHistory.slice(-5)
      };

      // 发送到错误监控服务
      await fetch('/api/error-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(report)
      });

      if (userTriggered && window.Components?.Toast) {
        window.Components.Toast.success('问题已报告，感谢您的反馈！', '报告成功');
      }
    } catch (reportError) {
      console.warn('Failed to report error:', reportError);
      
      // 降级到本地存储
      this.storeErrorLocally(errorInfo);
    }
  }

  storeErrorLocally(errorInfo) {
    try {
      const stored = JSON.parse(localStorage.getItem('error_reports') || '[]');
      stored.push(errorInfo);
      
      // 只保留最近20个错误
      if (stored.length > 20) {
        stored.splice(0, stored.length - 20);
      }
      
      localStorage.setItem('error_reports', JSON.stringify(stored));
    } catch (e) {
      // 本地存储也失败了，只能放弃
      console.warn('Failed to store error locally:', e);
    }
  }

  handleGracefulDegradation(errorInfo) {
    // 根据错误类型执行降级策略
    if (errorInfo.message.includes('API') || errorInfo.message.includes('fetch')) {
      this.enableOfflineMode();
    }
    
    if (errorInfo.type === 'javascript' && errorInfo.message.includes('Component')) {
      this.disableAdvancedFeatures();
    }

    // 如果错误过多，进入安全模式
    if (this.errorCount > 15) {
      this.enterSafeMode();
    }
  }

  enableOfflineMode() {
    if (!document.body.classList.contains('offline-mode')) {
      document.body.classList.add('offline-mode');
      
      if (window.Components?.Toast) {
        window.Components.Toast.warning(
          '网络连接异常，部分功能可能受限',
          '离线模式'
        );
      }
    }
  }

  disableAdvancedFeatures() {
    document.body.classList.add('basic-mode');
    
    // 隐藏高级功能
    document.querySelectorAll('[data-feature="advanced"]').forEach(el => {
      el.style.display = 'none';
    });
  }

  enterSafeMode() {
    document.body.classList.add('safe-mode');
    
    const safetyOverlay = document.createElement('div');
    safetyOverlay.className = 'safety-overlay fixed top-0 left-0 right-0 bg-yellow-100 border-b border-yellow-300 p-3 z-40';
    safetyOverlay.innerHTML = `
      <div class="container mx-auto flex items-center justify-between">
        <div class="flex items-center">
          <i class="bi bi-shield-exclamation text-yellow-600 mr-2"></i>
          <span class="text-yellow-800 text-sm">应用运行不稳定，已启用安全模式</span>
        </div>
        <button onclick="window.location.reload()" class="text-yellow-700 hover:text-yellow-900 text-sm underline">
          刷新页面
        </button>
      </div>
    `;
    
    document.body.insertBefore(safetyOverlay, document.body.firstChild);
  }

  handleNetworkStatusChange(online) {
    if (online) {
      document.body.classList.remove('offline-mode');
      
      // 尝试发送本地存储的错误报告
      this.syncLocalErrors();
      
      if (window.Components?.Toast) {
        window.Components.Toast.success('网络连接已恢复', '在线状态');
      }
    } else {
      this.enableOfflineMode();
    }
  }

  async syncLocalErrors() {
    try {
      const stored = JSON.parse(localStorage.getItem('error_reports') || '[]');
      if (stored.length === 0) return;

      for (const error of stored) {
        await this.reportError(error);
      }

      localStorage.removeItem('error_reports');
    } catch (e) {
      console.warn('Failed to sync local errors:', e);
    }
  }

  generateErrorId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  getSessionId() {
    let sessionId = sessionStorage.getItem('session_id');
    if (!sessionId) {
      sessionId = Date.now().toString(36) + Math.random().toString(36).substr(2);
      sessionStorage.setItem('session_id', sessionId);
    }
    return sessionId;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // 获取错误统计
  getErrorStats() {
    const now = Date.now();
    const last24h = this.errorHistory.filter(e => now - e.timestamp < 24 * 60 * 60 * 1000);
    const lastHour = this.errorHistory.filter(e => now - e.timestamp < 60 * 60 * 1000);

    return {
      total: this.errorHistory.length,
      last24Hours: last24h.length,
      lastHour: lastHour.length,
      currentSessionErrors: this.errorCount,
      mostCommonError: this.getMostCommonError()
    };
  }

  getMostCommonError() {
    const errorCounts = {};
    this.errorHistory.forEach(error => {
      const key = error.type + ':' + error.message;
      errorCounts[key] = (errorCounts[key] || 0) + 1;
    });

    let maxCount = 0;
    let mostCommon = null;
    
    Object.entries(errorCounts).forEach(([key, count]) => {
      if (count > maxCount) {
        maxCount = count;
        mostCommon = key;
      }
    });

    return { error: mostCommon, count: maxCount };
  }

  // 清理错误历史
  clearErrorHistory() {
    this.errorHistory = [];
    this.retryCount.clear();
    this.errorCount = 0;
    localStorage.removeItem('error_reports');
  }

  // 销毁错误边界
  destroy() {
    // 移除所有事件监听器
    window.removeEventListener('unhandledrejection', this.handleError);
    window.removeEventListener('error', this.handleError);
    window.removeEventListener('online', this.handleNetworkStatusChange);
    window.removeEventListener('offline', this.handleNetworkStatusChange);
    
    this.clearErrorHistory();
  }
}

// 创建全局错误边界实例
window.ErrorBoundary = ErrorBoundary;

// 自动初始化
if (typeof window !== 'undefined') {
  window.errorBoundary = new ErrorBoundary({
    enableErrorReporting: !window.location.hostname.includes('localhost'),
    onError: async (errorInfo) => {
      // 记录性能影响
      if (window.performanceMonitor) {
        window.performanceMonitor.mark(`error-${errorInfo.id}`);
      }
    }
  });
}

export default ErrorBoundary;