/**
 * PWA管理器 - 管理Service Worker注册、更新提示、安装提示等
 */

class PWAManager {
  constructor(options = {}) {
    this.options = {
      swPath: '/static/js/sw.js',
      enableAutoUpdate: true,
      enableInstallPrompt: true,
      updateCheckInterval: 60000, // 1分钟检查一次更新
      ...options
    };

    this.registration = null;
    this.updateAvailable = false;
    this.installPrompt = null;
    this.isOnline = navigator.onLine;
    
    this.init();
  }

  async init() {
    if (!('serviceWorker' in navigator)) {
      console.warn('Service Worker not supported');
      return;
    }

    try {
      await this.registerServiceWorker();
      this.setupEventListeners();
      this.setupPeriodicUpdateCheck();
      this.checkForInstallPrompt();
    } catch (error) {
      console.error('PWA initialization failed:', error);
    }
  }

  async registerServiceWorker() {
    try {
      this.registration = await navigator.serviceWorker.register(this.options.swPath);
      
      console.log('Service Worker registered successfully');

      // 监听更新
      this.registration.addEventListener('updatefound', () => {
        this.handleUpdateFound();
      });

      // 检查是否有等待中的Service Worker
      if (this.registration.waiting) {
        this.showUpdatePrompt();
      }

      // 监听控制器变化
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        window.location.reload();
      });

    } catch (error) {
      console.error('Service Worker registration failed:', error);
      throw error;
    }
  }

  setupEventListeners() {
    // 网络状态变化
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.handleOnlineStatusChange(true);
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.handleOnlineStatusChange(false);
    });

    // 安装提示
    window.addEventListener('beforeinstallprompt', (event) => {
      event.preventDefault();
      this.installPrompt = event;
      this.showInstallPrompt();
    });

    // 应用安装完成
    window.addEventListener('appinstalled', () => {
      this.handleAppInstalled();
    });

    // 接收Service Worker消息
    navigator.serviceWorker.addEventListener('message', (event) => {
      this.handleServiceWorkerMessage(event);
    });
  }

  handleUpdateFound() {
    const newWorker = this.registration.installing;
    
    newWorker.addEventListener('statechange', () => {
      if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
        this.updateAvailable = true;
        this.showUpdatePrompt();
      }
    });
  }

  showUpdatePrompt() {
    if (!window.Components?.Modal) {
      // 降级到原生confirm
      if (confirm('发现应用更新，是否立即更新？')) {
        this.applyUpdate();
      }
      return;
    }

    const updateModal = new window.Components.Modal(null, {
      title: '应用更新',
      content: `
        <div class="text-center">
          <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <i class="bi bi-arrow-clockwise text-blue-600 text-2xl"></i>
          </div>
          <h3 class="text-lg font-semibold mb-2">发现新版本</h3>
          <p class="text-gray-600 mb-4">新版本包含功能改进和问题修复</p>
          <div class="bg-gray-50 rounded-lg p-3 text-sm text-left mb-4">
            <h4 class="font-medium mb-2">更新内容：</h4>
            <ul class="space-y-1 text-gray-600">
              <li>• 性能优化和稳定性提升</li>
              <li>• 用户体验改进</li>
              <li>• 问题修复和安全更新</li>
            </ul>
          </div>
        </div>
      `,
      actions: [
        {
          key: 'later',
          text: '稍后更新',
          variant: 'outline',
          onClick: () => {
            updateModal.hide();
            this.scheduleUpdateReminder();
          }
        },
        {
          key: 'update',
          text: '立即更新',
          variant: 'primary',
          onClick: () => {
            updateModal.hide();
            this.applyUpdate();
          }
        }
      ],
      backdrop: false,
      keyboard: false
    });

    updateModal.show();
  }

  async applyUpdate() {
    if (!this.registration || !this.registration.waiting) {
      console.warn('No pending service worker to activate');
      return;
    }

    // 显示更新进度
    this.showUpdateProgress();

    try {
      // 告诉等待中的Service Worker跳过等待
      this.registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      
      // 等待控制器变化，然后刷新页面
      await new Promise((resolve) => {
        navigator.serviceWorker.addEventListener('controllerchange', resolve, { once: true });
      });

    } catch (error) {
      console.error('Update failed:', error);
      this.hideUpdateProgress();
      
      if (window.Components?.Toast) {
        window.Components.Toast.error('更新失败，请刷新页面重试');
      }
    }
  }

  showUpdateProgress() {
    const progressOverlay = document.createElement('div');
    progressOverlay.id = 'updateProgress';
    progressOverlay.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
    progressOverlay.innerHTML = `
      <div class="bg-white rounded-lg p-8 text-center max-w-sm">
        <div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <h3 class="text-lg font-semibold mb-2">正在更新应用</h3>
        <p class="text-gray-600">请稍候，应用将自动重启</p>
      </div>
    `;
    
    document.body.appendChild(progressOverlay);
  }

  hideUpdateProgress() {
    const progressOverlay = document.getElementById('updateProgress');
    if (progressOverlay) {
      document.body.removeChild(progressOverlay);
    }
  }

  scheduleUpdateReminder() {
    // 30分钟后再次提醒
    setTimeout(() => {
      if (this.updateAvailable) {
        this.showUpdatePrompt();
      }
    }, 30 * 60 * 1000);
  }

  showInstallPrompt() {
    if (!this.options.enableInstallPrompt || !this.installPrompt) {
      return;
    }

    // 检查是否已经安装或已经显示过提示
    if (window.matchMedia('(display-mode: standalone)').matches || 
        localStorage.getItem('pwa-install-dismissed') === 'true') {
      return;
    }

    // 延迟显示，避免打断用户
    setTimeout(() => {
      this.createInstallBanner();
    }, 3000);
  }

  createInstallBanner() {
    if (document.getElementById('installBanner')) {
      return; // 已经存在
    }

    const banner = document.createElement('div');
    banner.id = 'installBanner';
    banner.className = 'fixed bottom-4 left-4 right-4 bg-white border border-gray-200 rounded-lg shadow-lg p-4 z-40 transition-transform transform translate-y-full';
    banner.innerHTML = `
      <div class="flex items-center justify-between">
        <div class="flex items-center flex-1">
          <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
            <i class="bi bi-download text-blue-600"></i>
          </div>
          <div class="flex-1">
            <h4 class="font-semibold text-gray-900 mb-1">安装应用</h4>
            <p class="text-sm text-gray-600">获得更好的使用体验</p>
          </div>
        </div>
        <div class="flex gap-2 ml-4">
          <button id="dismissInstall" class="text-gray-400 hover:text-gray-600 p-1">
            <i class="bi bi-x text-lg"></i>
          </button>
          <button id="installApp" class="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 transition-colors">
            安装
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(banner);

    // 显示动画
    requestAnimationFrame(() => {
      banner.classList.remove('translate-y-full');
    });

    // 绑定事件
    banner.querySelector('#installApp').onclick = () => {
      this.triggerInstall();
    };

    banner.querySelector('#dismissInstall').onclick = () => {
      this.dismissInstallBanner();
    };

    // 自动隐藏
    setTimeout(() => {
      if (banner.parentNode) {
        this.dismissInstallBanner();
      }
    }, 30000);
  }

  async triggerInstall() {
    if (!this.installPrompt) {
      return;
    }

    try {
      const result = await this.installPrompt.prompt();
      console.log('Install prompt result:', result.outcome);

      // 清理引用
      this.installPrompt = null;
      this.dismissInstallBanner();

      if (result.outcome === 'accepted') {
        if (window.Components?.Toast) {
          window.Components.Toast.success('应用安装中，请查看浏览器提示');
        }
      }
    } catch (error) {
      console.error('Install failed:', error);
    }
  }

  dismissInstallBanner() {
    const banner = document.getElementById('installBanner');
    if (banner) {
      banner.classList.add('translate-y-full');
      setTimeout(() => {
        if (banner.parentNode) {
          document.body.removeChild(banner);
        }
      }, 300);
    }

    // 记住用户选择
    localStorage.setItem('pwa-install-dismissed', 'true');
  }

  handleAppInstalled() {
    console.log('PWA installed successfully');
    
    if (window.Components?.Toast) {
      window.Components.Toast.success('应用安装成功！', '欢迎使用');
    }

    // 移除安装横幅
    this.dismissInstallBanner();
    
    // 清除本地标记
    localStorage.removeItem('pwa-install-dismissed');
  }

  handleOnlineStatusChange(isOnline) {
    if (isOnline) {
      // 网络恢复，尝试同步
      this.triggerBackgroundSync();
      
      if (window.Components?.Toast) {
        window.Components.Toast.success('网络已恢复', '在线状态');
      }
    } else {
      if (window.Components?.Toast) {
        window.Components.Toast.warning('网络已断开，部分功能可能受限', '离线状态');
      }
    }

    // 更新UI状态
    document.body.classList.toggle('offline', !isOnline);
  }

  async triggerBackgroundSync() {
    if (!this.registration || !this.registration.sync) {
      return;
    }

    try {
      await this.registration.sync.register('background-sync');
      console.log('Background sync registered');
    } catch (error) {
      console.error('Background sync registration failed:', error);
    }
  }

  setupPeriodicUpdateCheck() {
    if (!this.options.enableAutoUpdate) {
      return;
    }

    setInterval(async () => {
      try {
        await this.registration.update();
        console.log('Checked for service worker updates');
      } catch (error) {
        console.warn('Update check failed:', error);
      }
    }, this.options.updateCheckInterval);
  }

  handleServiceWorkerMessage(event) {
    const { type, data } = event.data;

    switch (type) {
      case 'SYNC_COMPLETE':
        if (window.Components?.Toast) {
          window.Components.Toast.info('数据同步完成');
        }
        break;

      case 'FORCE_RELOAD':
        window.location.reload();
        break;

      case 'CACHE_UPDATED':
        console.log('Cache updated:', data);
        break;
    }
  }

  // 获取安装状态
  getInstallStatus() {
    return {
      isInstalled: window.matchMedia('(display-mode: standalone)').matches,
      isInstallable: !!this.installPrompt,
      isOnline: this.isOnline,
      hasServiceWorker: !!this.registration,
      updateAvailable: this.updateAvailable
    };
  }

  // 手动检查更新
  async checkForUpdate() {
    if (!this.registration) {
      throw new Error('Service Worker not registered');
    }

    try {
      await this.registration.update();
      
      if (window.Components?.Toast) {
        window.Components.Toast.info('已检查最新版本');
      }
    } catch (error) {
      console.error('Manual update check failed:', error);
      throw error;
    }
  }

  // 获取缓存状态
  async getCacheStatus() {
    if (!this.registration) {
      return null;
    }

    return new Promise((resolve) => {
      const messageChannel = new MessageChannel();
      
      messageChannel.port1.onmessage = (event) => {
        resolve(event.data);
      };

      this.registration.active.postMessage({
        type: 'GET_CACHE_STATUS'
      }, [messageChannel.port2]);
    });
  }

  // 清除缓存
  async clearCache() {
    if (!this.registration) {
      throw new Error('Service Worker not registered');
    }

    return new Promise((resolve, reject) => {
      const messageChannel = new MessageChannel();
      
      messageChannel.port1.onmessage = (event) => {
        if (event.data.success) {
          resolve();
        } else {
          reject(new Error('Clear cache failed'));
        }
      };

      this.registration.active.postMessage({
        type: 'CLEAR_CACHE'
      }, [messageChannel.port2]);
    });
  }

  // 强制更新
  async forceUpdate() {
    if (!this.registration) {
      throw new Error('Service Worker not registered');
    }

    return new Promise((resolve, reject) => {
      const messageChannel = new MessageChannel();
      
      messageChannel.port1.onmessage = (event) => {
        if (event.data.success) {
          resolve();
        } else {
          reject(new Error('Force update failed'));
        }
      };

      this.registration.active.postMessage({
        type: 'FORCE_UPDATE'
      }, [messageChannel.port2]);
    });
  }

  // 销毁PWA管理器
  async destroy() {
    if (this.registration) {
      try {
        await this.registration.unregister();
        console.log('Service Worker unregistered');
      } catch (error) {
        console.error('Failed to unregister service worker:', error);
      }
    }

    // 移除安装横幅
    this.dismissInstallBanner();
    
    // 清理引用
    this.registration = null;
    this.installPrompt = null;
  }
}

// 导出到全局
window.PWAManager = PWAManager;

// 自动初始化PWA管理器
if (typeof window !== 'undefined') {
  window.pwaManager = new PWAManager();
}

export default PWAManager;