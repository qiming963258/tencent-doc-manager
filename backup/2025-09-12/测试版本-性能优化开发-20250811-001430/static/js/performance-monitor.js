/**
 * 性能监控模块 - Web Vitals 和应用性能追踪
 * 基于现代浏览器API，提供详细的性能指标监控
 */

class PerformanceMonitor {
  constructor(options = {}) {
    this.options = {
      enableVitals: true,
      enableResourceTiming: true,
      enableUserTiming: true,
      reportInterval: 30000, // 30秒
      maxEntries: 1000,
      onReport: options.onReport || this.defaultReportHandler,
      ...options
    };

    this.metrics = {
      vitals: {},
      resources: [],
      userTiming: [],
      memory: {},
      navigation: {}
    };

    this.observers = [];
    this.reportTimer = null;

    this.init();
  }

  init() {
    if (typeof window === 'undefined') return;

    this.setupVitalsMonitoring();
    this.setupResourceTimingMonitoring();
    this.setupUserTimingMonitoring();
    this.setupMemoryMonitoring();
    this.setupNavigationTiming();
    
    this.startReporting();
  }

  setupVitalsMonitoring() {
    if (!this.options.enableVitals) return;

    // 监控 Core Web Vitals
    this.measureCLS();
    this.measureFCP();
    this.measureLCP();
    this.measureFID();
    this.measureTTFB();
  }

  measureCLS() {
    if (!('LayoutShiftObserver' in window)) return;

    let clsValue = 0;
    let clsEntries = [];

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
          clsEntries.push(entry);
        }
      }
      
      this.metrics.vitals.CLS = {
        value: clsValue,
        entries: clsEntries.slice(-10) // 只保留最近10个条目
      };
    });

    observer.observe({ entryTypes: ['layout-shift'] });
    this.observers.push(observer);
  }

  measureFCP() {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          this.metrics.vitals.FCP = {
            value: entry.startTime,
            timestamp: Date.now()
          };
          observer.disconnect();
        }
      }
    });

    observer.observe({ entryTypes: ['paint'] });
    this.observers.push(observer);
  }

  measureLCP() {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      
      this.metrics.vitals.LCP = {
        value: lastEntry.startTime,
        element: lastEntry.element?.tagName || 'unknown',
        timestamp: Date.now()
      };
    });

    observer.observe({ entryTypes: ['largest-contentful-paint'] });
    this.observers.push(observer);
  }

  measureFID() {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        this.metrics.vitals.FID = {
          value: entry.processingStart - entry.startTime,
          eventType: entry.name,
          timestamp: Date.now()
        };
      }
    });

    observer.observe({ entryTypes: ['first-input'] });
    this.observers.push(observer);
  }

  measureTTFB() {
    const navigationEntry = performance.getEntriesByType('navigation')[0];
    if (navigationEntry) {
      this.metrics.vitals.TTFB = {
        value: navigationEntry.responseStart - navigationEntry.requestStart,
        timestamp: Date.now()
      };
    }
  }

  setupResourceTimingMonitoring() {
    if (!this.options.enableResourceTiming) return;

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        this.metrics.resources.push({
          name: entry.name,
          type: entry.initiatorType,
          size: entry.transferSize,
          duration: entry.duration,
          startTime: entry.startTime,
          timestamp: Date.now()
        });

        // 限制条目数量
        if (this.metrics.resources.length > this.options.maxEntries) {
          this.metrics.resources = this.metrics.resources.slice(-this.options.maxEntries);
        }
      }
    });

    observer.observe({ entryTypes: ['resource'] });
    this.observers.push(observer);
  }

  setupUserTimingMonitoring() {
    if (!this.options.enableUserTiming) return;

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        this.metrics.userTiming.push({
          name: entry.name,
          type: entry.entryType,
          duration: entry.duration,
          startTime: entry.startTime,
          timestamp: Date.now()
        });

        // 限制条目数量
        if (this.metrics.userTiming.length > this.options.maxEntries) {
          this.metrics.userTiming = this.metrics.userTiming.slice(-this.options.maxEntries);
        }
      }
    });

    observer.observe({ entryTypes: ['measure', 'mark'] });
    this.observers.push(observer);
  }

  setupMemoryMonitoring() {
    if (!performance.memory) return;

    const updateMemoryMetrics = () => {
      this.metrics.memory = {
        usedJSHeapSize: performance.memory.usedJSHeapSize,
        totalJSHeapSize: performance.memory.totalJSHeapSize,
        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
        timestamp: Date.now()
      };
    };

    updateMemoryMetrics();
    setInterval(updateMemoryMetrics, 5000); // 每5秒更新一次
  }

  setupNavigationTiming() {
    const navigationEntry = performance.getEntriesByType('navigation')[0];
    if (navigationEntry) {
      this.metrics.navigation = {
        domContentLoaded: navigationEntry.domContentLoadedEventEnd - navigationEntry.domContentLoadedEventStart,
        loadComplete: navigationEntry.loadEventEnd - navigationEntry.loadEventStart,
        domInteractive: navigationEntry.domInteractive - navigationEntry.navigationStart,
        redirect: navigationEntry.redirectEnd - navigationEntry.redirectStart,
        dns: navigationEntry.domainLookupEnd - navigationEntry.domainLookupStart,
        tcp: navigationEntry.connectEnd - navigationEntry.connectStart,
        request: navigationEntry.responseEnd - navigationEntry.requestStart,
        timestamp: Date.now()
      };
    }
  }

  startReporting() {
    if (this.reportTimer) {
      clearInterval(this.reportTimer);
    }

    this.reportTimer = setInterval(() => {
      this.generateReport();
    }, this.options.reportInterval);
  }

  stopReporting() {
    if (this.reportTimer) {
      clearInterval(this.reportTimer);
      this.reportTimer = null;
    }
  }

  generateReport() {
    const report = {
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      vitals: this.metrics.vitals,
      navigation: this.metrics.navigation,
      memory: this.metrics.memory,
      resourcesSummary: this.getResourcesSummary(),
      userTimingSummary: this.getUserTimingSummary(),
      performanceScore: this.calculatePerformanceScore()
    };

    this.options.onReport(report);
  }

  getResourcesSummary() {
    const resources = this.metrics.resources;
    if (resources.length === 0) return {};

    const byType = {};
    let totalSize = 0;
    let totalDuration = 0;

    resources.forEach(resource => {
      if (!byType[resource.type]) {
        byType[resource.type] = { count: 0, size: 0, duration: 0 };
      }
      
      byType[resource.type].count++;
      byType[resource.type].size += resource.size || 0;
      byType[resource.type].duration += resource.duration || 0;
      
      totalSize += resource.size || 0;
      totalDuration += resource.duration || 0;
    });

    return {
      total: { count: resources.length, size: totalSize, duration: totalDuration },
      byType
    };
  }

  getUserTimingSummary() {
    const timing = this.metrics.userTiming;
    if (timing.length === 0) return {};

    const marks = timing.filter(t => t.type === 'mark').length;
    const measures = timing.filter(t => t.type === 'measure');
    
    return {
      marksCount: marks,
      measuresCount: measures.length,
      averageMeasureDuration: measures.length > 0 
        ? measures.reduce((sum, m) => sum + m.duration, 0) / measures.length 
        : 0
    };
  }

  calculatePerformanceScore() {
    const vitals = this.metrics.vitals;
    let score = 100;

    // Core Web Vitals 评分规则
    if (vitals.LCP?.value > 4000) score -= 30;
    else if (vitals.LCP?.value > 2500) score -= 15;

    if (vitals.FID?.value > 300) score -= 30;
    else if (vitals.FID?.value > 100) score -= 15;

    if (vitals.CLS?.value > 0.25) score -= 30;
    else if (vitals.CLS?.value > 0.1) score -= 15;

    if (vitals.FCP?.value > 3000) score -= 10;
    else if (vitals.FCP?.value > 1800) score -= 5;

    return Math.max(0, score);
  }

  // 手动标记性能点
  mark(name) {
    performance.mark(name);
  }

  // 手动测量性能区间
  measure(name, startMark, endMark) {
    performance.measure(name, startMark, endMark);
  }

  // 测量函数执行时间
  async measureFunction(name, fn) {
    const startMark = `${name}-start`;
    const endMark = `${name}-end`;
    
    this.mark(startMark);
    
    try {
      const result = await fn();
      this.mark(endMark);
      this.measure(name, startMark, endMark);
      return result;
    } catch (error) {
      this.mark(endMark);
      this.measure(`${name}-error`, startMark, endMark);
      throw error;
    }
  }

  // 获取当前性能快照
  getSnapshot() {
    return {
      timestamp: Date.now(),
      vitals: { ...this.metrics.vitals },
      navigation: { ...this.metrics.navigation },
      memory: { ...this.metrics.memory },
      resourcesCount: this.metrics.resources.length,
      userTimingCount: this.metrics.userTiming.length
    };
  }

  defaultReportHandler(report) {
    // 发送到分析后端或本地存储
    console.group('Performance Report');
    console.log('Timestamp:', new Date(report.timestamp));
    console.log('Performance Score:', report.performanceScore);
    console.table(report.vitals);
    
    if (report.memory) {
      console.log('Memory Usage:', {
        used: `${(report.memory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
        total: `${(report.memory.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
        limit: `${(report.memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`
      });
    }
    
    console.groupEnd();

    // 可选：发送到后端分析服务
    // this.sendToAnalytics(report);
  }

  async sendToAnalytics(report) {
    try {
      await fetch('/api/performance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(report)
      });
    } catch (error) {
      console.warn('Failed to send performance report:', error);
    }
  }

  destroy() {
    this.stopReporting();
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
    this.metrics = { vitals: {}, resources: [], userTiming: [], memory: {}, navigation: {} };
  }
}

// 导出到全局
window.PerformanceMonitor = PerformanceMonitor;

// 自动初始化性能监控（生产环境）
if (typeof window !== 'undefined' && !window.location.hostname.includes('localhost')) {
  window.performanceMonitor = new PerformanceMonitor({
    onReport: (report) => {
      // 生产环境报告处理
      if (report.performanceScore < 70) {
        console.warn('Performance issue detected:', report);
      }
    }
  });
}

export default PerformanceMonitor;