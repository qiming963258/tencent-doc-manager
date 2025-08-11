/**
 * 渐进式Web应用(PWA) Service Worker
 * 提供离线功能、缓存策略、后台同步、推送通知等
 */

const CACHE_NAME = 'tencent-doc-exporter-v1.0.0';
const RUNTIME_CACHE = 'runtime-cache-v1';
const API_CACHE = 'api-cache-v1';

// 静态资源缓存列表
const STATIC_ASSETS = [
  '/',
  '/static/css/main.css',
  '/static/css/components.css',
  '/static/js/app.js',
  '/static/js/components.js',
  '/static/js/api-client.js',
  '/static/js/performance-monitor.js',
  '/static/js/error-boundary.js',
  '/static/js/main.js',
  '/manifest.json'
];

// API缓存策略配置
const CACHE_STRATEGIES = {
  // 静态资源：缓存优先
  static: {
    pattern: /\.(css|js|html|png|jpg|jpeg|gif|svg|woff|woff2)$/,
    strategy: 'CacheFirst',
    maxAge: 24 * 60 * 60 * 1000 // 24小时
  },
  
  // API请求：网络优先，缓存降级
  api: {
    pattern: /\/api\//,
    strategy: 'NetworkFirst',
    maxAge: 5 * 60 * 1000, // 5分钟
    networkTimeout: 5000
  },
  
  // 文档下载：仅网络
  download: {
    pattern: /\/api\/(download|upload)/,
    strategy: 'NetworkOnly'
  }
};

self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    Promise.all([
      // 预缓存静态资源
      caches.open(CACHE_NAME).then((cache) => {
        return cache.addAll(STATIC_ASSETS.map(url => new Request(url, { cache: 'reload' })));
      }),
      
      // 跳过等待，立即激活
      self.skipWaiting()
    ])
  );
});

self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    Promise.all([
      // 清理旧缓存
      cleanupOldCaches(),
      
      // 立即接管所有页面
      self.clients.claim()
    ])
  );
});

self.addEventListener('fetch', (event) => {
  // 只处理GET请求
  if (event.request.method !== 'GET') {
    return;
  }

  const url = new URL(event.request.url);
  
  // 跳过Chrome扩展和其他协议
  if (url.protocol !== 'http:' && url.protocol !== 'https:') {
    return;
  }

  // 选择缓存策略
  const strategy = selectCacheStrategy(event.request);
  
  if (strategy) {
    event.respondWith(strategy(event.request));
  }
});

// 后台同步
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(handleBackgroundSync());
  }
});

// 推送通知
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    event.waitUntil(handlePushNotification(data));
  }
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow(event.notification.data?.url || '/')
  );
});

// 缓存策略实现
function selectCacheStrategy(request) {
  const url = request.url;
  
  for (const [name, config] of Object.entries(CACHE_STRATEGIES)) {
    if (config.pattern.test(url)) {
      switch (config.strategy) {
        case 'CacheFirst':
          return (req) => cacheFirst(req, config);
        case 'NetworkFirst':
          return (req) => networkFirst(req, config);
        case 'NetworkOnly':
          return (req) => networkOnly(req);
        default:
          return null;
      }
    }
  }
  
  // 默认策略：对同域请求使用网络优先
  if (url.startsWith(self.location.origin)) {
    return (req) => networkFirst(req, { maxAge: 60000 });
  }
  
  return null;
}

async function cacheFirst(request, config) {
  try {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);
    
    if (cached && !isExpired(cached, config.maxAge)) {
      // 后台更新缓存
      updateCacheInBackground(request, cache);
      return cached;
    }
    
    const response = await fetch(request);
    
    if (response.ok) {
      const responseClone = response.clone();
      await cache.put(request, responseClone);
    }
    
    return response;
  } catch (error) {
    console.error('CacheFirst strategy failed:', error);
    
    // 降级到缓存（即使过期）
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);
    
    if (cached) {
      return cached;
    }
    
    // 返回离线页面
    return createOfflineResponse(request);
  }
}

async function networkFirst(request, config) {
  const cache = await caches.open(config.pattern.test(request.url) ? API_CACHE : RUNTIME_CACHE);
  
  try {
    // 设置网络超时
    const timeoutPromise = config.networkTimeout 
      ? new Promise((_, reject) => setTimeout(() => reject(new Error('Network timeout')), config.networkTimeout))
      : null;
    
    const networkPromise = fetch(request);
    
    const response = timeoutPromise 
      ? await Promise.race([networkPromise, timeoutPromise])
      : await networkPromise;
    
    if (response.ok) {
      const responseClone = response.clone();
      await cache.put(request, responseClone);
    }
    
    return response;
  } catch (error) {
    console.warn('Network request failed, falling back to cache:', error);
    
    const cached = await cache.match(request);
    
    if (cached && !isExpired(cached, config.maxAge)) {
      return cached;
    }
    
    // 如果是API请求失败，返回错误响应
    if (config.pattern && config.pattern.test(request.url)) {
      return new Response(JSON.stringify({
        success: false,
        error: 'Network unavailable',
        offline: true,
        timestamp: Date.now()
      }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    return createOfflineResponse(request);
  }
}

async function networkOnly(request) {
  return fetch(request);
}

function isExpired(response, maxAge) {
  if (!maxAge) return false;
  
  const date = response.headers.get('date');
  if (!date) return false;
  
  const responseTime = new Date(date).getTime();
  const now = Date.now();
  
  return (now - responseTime) > maxAge;
}

async function updateCacheInBackground(request, cache) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      await cache.put(request, response.clone());
    }
  } catch (error) {
    console.warn('Background cache update failed:', error);
  }
}

function createOfflineResponse(request) {
  const url = new URL(request.url);
  
  if (url.pathname.endsWith('.html') || url.pathname === '/') {
    return new Response(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>离线模式 - 腾讯文档导出工具</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            text-align: center; 
            padding: 50px; 
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .offline-container {
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 400px;
          }
          .offline-icon {
            font-size: 64px;
            margin-bottom: 24px;
            color: #667eea;
          }
          h1 { color: #333; margin-bottom: 16px; }
          p { color: #666; margin-bottom: 24px; line-height: 1.6; }
          button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
          }
          button:hover { background: #5a67d8; }
          .status { 
            margin-top: 20px; 
            font-size: 14px; 
            color: #888; 
          }
        </style>
      </head>
      <body>
        <div class="offline-container">
          <div class="offline-icon">📶</div>
          <h1>当前处于离线状态</h1>
          <p>无法连接到服务器。请检查网络连接后重试。</p>
          <button onclick="window.location.reload()">重新连接</button>
          <div class="status" id="status">检查网络连接中...</div>
        </div>
        
        <script>
          // 检查网络状态
          function checkOnline() {
            const status = document.getElementById('status');
            if (navigator.onLine) {
              status.textContent = '网络已连接，点击重新连接按钮';
              status.style.color = '#10b981';
            } else {
              status.textContent = '网络未连接';
              status.style.color = '#ef4444';
            }
          }
          
          checkOnline();
          window.addEventListener('online', checkOnline);
          window.addEventListener('offline', checkOnline);
          
          // 定期检查网络
          setInterval(() => {
            if (navigator.onLine) {
              window.location.reload();
            }
          }, 5000);
        </script>
      </body>
      </html>
    `, {
      status: 200,
      headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
  }
  
  return new Response('Offline', {
    status: 503,
    headers: { 'Content-Type': 'text/plain' }
  });
}

async function cleanupOldCaches() {
  const cacheNames = await caches.keys();
  const currentCaches = [CACHE_NAME, RUNTIME_CACHE, API_CACHE];
  
  return Promise.all(
    cacheNames
      .filter(name => !currentCaches.includes(name))
      .map(name => caches.delete(name))
  );
}

async function handleBackgroundSync() {
  console.log('Handling background sync...');
  
  try {
    // 获取待同步的数据
    const syncData = await getSyncData();
    
    for (const item of syncData) {
      await syncItem(item);
    }
    
    // 通知主线程同步完成
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'SYNC_COMPLETE',
        timestamp: Date.now()
      });
    });
    
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

async function getSyncData() {
  // 从IndexedDB或其他存储获取待同步数据
  // 这里简化为空数组
  return [];
}

async function syncItem(item) {
  // 同步单个数据项
  try {
    const response = await fetch('/api/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item)
    });
    
    if (response.ok) {
      console.log('Sync item success:', item.id);
    }
  } catch (error) {
    console.error('Sync item failed:', error);
    throw error;
  }
}

async function handlePushNotification(data) {
  const options = {
    body: data.body,
    icon: '/static/images/icon-192x192.png',
    badge: '/static/images/badge-72x72.png',
    tag: data.tag || 'general',
    data: data.data || {},
    actions: data.actions || [],
    requireInteraction: data.requireInteraction || false,
    silent: data.silent || false
  };

  return self.registration.showNotification(data.title, options);
}

// 消息处理
self.addEventListener('message', (event) => {
  const { type, data } = event.data;
  
  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
      
    case 'GET_CACHE_STATUS':
      event.ports[0].postMessage({
        caches: [CACHE_NAME, RUNTIME_CACHE, API_CACHE],
        timestamp: Date.now()
      });
      break;
      
    case 'CLEAR_CACHE':
      clearAllCaches().then(() => {
        event.ports[0].postMessage({ success: true });
      });
      break;
      
    case 'FORCE_UPDATE':
      forceUpdate().then(() => {
        event.ports[0].postMessage({ success: true });
      });
      break;
  }
});

async function clearAllCaches() {
  const cacheNames = await caches.keys();
  return Promise.all(cacheNames.map(name => caches.delete(name)));
}

async function forceUpdate() {
  // 清除所有缓存并重新预缓存静态资源
  await clearAllCaches();
  
  const cache = await caches.open(CACHE_NAME);
  await cache.addAll(STATIC_ASSETS.map(url => new Request(url, { cache: 'reload' })));
  
  // 通知所有客户端刷新
  const clients = await self.clients.matchAll();
  clients.forEach(client => {
    client.postMessage({ type: 'FORCE_RELOAD' });
  });
}