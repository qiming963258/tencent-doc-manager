/**
 * 腾讯文档自动化服务 - 现代组件化架构
 * 原生JavaScript组件系统，支持生命周期、事件系统、状态管理
 * 模块化设计，易于扩展和维护
 */

/* ===== 核心组件基类 ===== */
class BaseComponent {
  constructor(element, options = {}) {
    this.element = element;
    this.options = { ...this.defaultOptions, ...options };
    this.state = { ...this.initialState };
    this.listeners = new Map();
    this.children = new Map();
    this.isDestroyed = false;
    
    this.init();
  }
  
  // 默认配置
  get defaultOptions() {
    return {};
  }
  
  // 初始状态
  get initialState() {
    return {};
  }
  
  // 初始化组件
  init() {
    this.createElement();
    this.bindEvents();
    this.render();
    this.onMounted();
  }
  
  // 创建元素结构
  createElement() {
    // 子类实现
  }
  
  // 绑定事件
  bindEvents() {
    // 子类实现
  }
  
  // 渲染组件
  render() {
    // 子类实现
  }
  
  // 挂载完成回调
  onMounted() {
    // 子类实现
  }
  
  // 状态更新
  setState(newState, callback) {
    const prevState = { ...this.state };
    this.state = { ...this.state, ...newState };
    
    // 触发状态变化事件
    this.emit('stateChange', {
      prevState,
      currentState: this.state,
      changedKeys: Object.keys(newState)
    });
    
    // 重新渲染
    this.render();
    
    // 执行回调
    if (callback && typeof callback === 'function') {
      callback(this.state, prevState);
    }
  }
  
  // 事件监听
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }
  
  // 触发事件
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data));
    }
  }
  
  // 移除事件监听
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }
  
  // 添加子组件
  addChild(name, component) {
    this.children.set(name, component);
  }
  
  // 获取子组件
  getChild(name) {
    return this.children.get(name);
  }
  
  // 销毁组件
  destroy() {
    if (this.isDestroyed) return;
    
    // 销毁子组件
    this.children.forEach(child => {
      if (child.destroy) {
        child.destroy();
      }
    });
    
    // 清除事件监听
    this.listeners.clear();
    
    // 移除DOM元素
    if (this.element && this.element.parentNode) {
      this.element.parentNode.removeChild(this.element);
    }
    
    this.isDestroyed = true;
    this.emit('destroyed');
  }
}

/* ===== 按钮组件 ===== */
class Button extends BaseComponent {
  get defaultOptions() {
    return {
      variant: 'primary', // primary, secondary, outline, ghost
      size: 'md', // sm, md, lg
      disabled: false,
      loading: false,
      icon: null,
      text: 'Button',
      onClick: null
    };
  }
  
  createElement() {
    if (!this.element) {
      this.element = document.createElement('button');
    }
    
    this.element.className = this.getClasses();
    this.element.type = 'button';
    this.element.disabled = this.options.disabled || this.options.loading;
  }
  
  getClasses() {
    const classes = ['btn'];
    
    // 变体样式
    const variantClasses = {
      primary: 'btn-primary',
      secondary: 'btn-secondary', 
      outline: 'btn-outline',
      ghost: 'btn-ghost'
    };
    classes.push(variantClasses[this.options.variant] || variantClasses.primary);
    
    // 尺寸样式
    const sizeClasses = {
      sm: 'btn-sm',
      md: '',
      lg: 'btn-lg'
    };
    const sizeClass = sizeClasses[this.options.size];
    if (sizeClass) classes.push(sizeClass);
    
    // 状态样式
    if (this.options.loading) classes.push('btn-loading');
    if (this.options.disabled) classes.push('btn-disabled');
    
    return classes.join(' ');
  }
  
  bindEvents() {
    this.element.addEventListener('click', (e) => {
      if (this.options.disabled || this.options.loading) {
        e.preventDefault();
        return;
      }
      
      this.emit('click', e);
      if (this.options.onClick) {
        this.options.onClick(e);
      }
    });
  }
  
  render() {
    let content = '';
    
    // 加载状态
    if (this.options.loading) {
      content += '<span class="spinner spinner-sm"></span>';
    }
    
    // 图标
    if (this.options.icon && !this.options.loading) {
      content += `<i class="${this.options.icon}"></i>`;
    }
    
    // 文本
    if (this.options.text) {
      content += `<span>${this.options.text}</span>`;
    }
    
    this.element.innerHTML = content;
    this.element.className = this.getClasses();
    this.element.disabled = this.options.disabled || this.options.loading;
  }
  
  // 设置加载状态
  setLoading(loading) {
    this.options.loading = loading;
    this.render();
  }
  
  // 设置禁用状态
  setDisabled(disabled) {
    this.options.disabled = disabled;
    this.render();
  }
  
  // 设置文本
  setText(text) {
    this.options.text = text;
    this.render();
  }
}

/* ===== 卡片组件 ===== */
class Card extends BaseComponent {
  get defaultOptions() {
    return {
      title: '',
      subtitle: '',
      content: '',
      actions: [],
      shadow: 'sm', // none, xs, sm, md, lg, xl
      padding: 'md', // sm, md, lg
      rounded: 'lg' // sm, md, lg, xl, 2xl
    };
  }
  
  createElement() {
    if (!this.element) {
      this.element = document.createElement('div');
    }
    
    this.element.className = this.getClasses();
  }
  
  getClasses() {
    const classes = ['card'];
    
    // 阴影
    if (this.options.shadow && this.options.shadow !== 'none') {
      classes.push(`shadow-${this.options.shadow}`);
    }
    
    // 圆角
    classes.push(`rounded-${this.options.rounded}`);
    
    return classes.join(' ');
  }
  
  render() {
    let html = '';
    
    // 标题区域
    if (this.options.title || this.options.subtitle) {
      html += '<div class="card-header">';
      if (this.options.title) {
        html += `<h3 class="card-title">${this.options.title}</h3>`;
      }
      if (this.options.subtitle) {
        html += `<p class="card-subtitle text-muted">${this.options.subtitle}</p>`;
      }
      html += '</div>';
    }
    
    // 内容区域
    if (this.options.content) {
      const paddingClass = this.options.padding === 'sm' ? 'p-4' : 
                          this.options.padding === 'lg' ? 'p-8' : 'p-6';
      html += `<div class="card-body ${paddingClass}">${this.options.content}</div>`;
    }
    
    // 操作区域
    if (this.options.actions && this.options.actions.length > 0) {
      html += '<div class="card-footer flex gap-2">';
      this.options.actions.forEach(action => {
        html += `<button class="btn btn-${action.variant || 'secondary'}" data-action="${action.key}">${action.text}</button>`;
      });
      html += '</div>';
    }
    
    this.element.innerHTML = html;
  }
  
  bindEvents() {
    // 绑定操作按钮事件
    this.element.addEventListener('click', (e) => {
      const actionBtn = e.target.closest('[data-action]');
      if (actionBtn) {
        const actionKey = actionBtn.dataset.action;
        const action = this.options.actions.find(a => a.key === actionKey);
        if (action && action.onClick) {
          action.onClick(e);
        }
        this.emit('action', { key: actionKey, event: e });
      }
    });
  }
}

/* ===== 模态框组件 ===== */
class Modal extends BaseComponent {
  get defaultOptions() {
    return {
      title: '',
      content: '',
      size: 'md', // sm, md, lg, xl
      closable: true,
      backdrop: true,
      keyboard: true,
      actions: []
    };
  }
  
  get initialState() {
    return {
      visible: false
    };
  }
  
  createElement() {
    // 创建模态框结构
    this.backdrop = document.createElement('div');
    this.backdrop.className = 'modal-backdrop fixed inset-0 bg-black bg-opacity-50 z-modal-backdrop transition-opacity';
    
    this.element = document.createElement('div');
    this.element.className = 'modal fixed inset-0 z-modal flex items-center justify-center p-4';
    
    this.dialog = document.createElement('div');
    this.dialog.className = this.getDialogClasses();
    
    this.element.appendChild(this.dialog);
    
    // 初始状态为隐藏
    this.backdrop.style.display = 'none';
    this.element.style.display = 'none';
  }
  
  getDialogClasses() {
    const classes = ['modal-dialog', 'bg-white', 'rounded-lg', 'shadow-xl', 'w-full'];
    
    // 尺寸
    const sizeClasses = {
      sm: 'max-w-sm',
      md: 'max-w-md',
      lg: 'max-w-lg',
      xl: 'max-w-2xl'
    };
    classes.push(sizeClasses[this.options.size] || sizeClasses.md);
    
    return classes.join(' ');
  }
  
  render() {
    let html = '';
    
    // 标题栏
    if (this.options.title || this.options.closable) {
      html += '<div class="modal-header flex items-center justify-between p-6 border-b">';
      if (this.options.title) {
        html += `<h2 class="modal-title text-lg font-semibold">${this.options.title}</h2>`;
      }
      if (this.options.closable) {
        html += '<button class="modal-close btn btn-ghost btn-sm" data-close><i class="bi bi-x-lg"></i></button>';
      }
      html += '</div>';
    }
    
    // 内容区域
    html += `<div class="modal-body p-6">${this.options.content}</div>`;
    
    // 操作区域
    if (this.options.actions && this.options.actions.length > 0) {
      html += '<div class="modal-footer flex gap-2 justify-end p-6 border-t">';
      this.options.actions.forEach(action => {
        html += `<button class="btn btn-${action.variant || 'secondary'}" data-action="${action.key}">${action.text}</button>`;
      });
      html += '</div>';
    }
    
    this.dialog.innerHTML = html;
  }
  
  bindEvents() {
    // 关闭按钮事件
    this.element.addEventListener('click', (e) => {
      if (e.target.closest('[data-close]')) {
        this.hide();
      }
      
      // 操作按钮事件
      const actionBtn = e.target.closest('[data-action]');
      if (actionBtn) {
        const actionKey = actionBtn.dataset.action;
        const action = this.options.actions.find(a => a.key === actionKey);
        if (action && action.onClick) {
          action.onClick(e);
        }
        this.emit('action', { key: actionKey, event: e });
      }
    });
    
    // 背景点击关闭
    if (this.options.backdrop) {
      this.backdrop.addEventListener('click', () => {
        this.hide();
      });
    }
    
    // ESC键关闭
    if (this.options.keyboard) {
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.state.visible) {
          this.hide();
        }
      });
    }
  }
  
  show() {
    if (this.state.visible) return;
    
    // 添加到DOM
    document.body.appendChild(this.backdrop);
    document.body.appendChild(this.element);
    
    // 显示
    this.backdrop.style.display = 'block';
    this.element.style.display = 'flex';
    
    // 触发动画
    requestAnimationFrame(() => {
      this.backdrop.style.opacity = '1';
      this.element.style.opacity = '1';
      this.dialog.style.transform = 'scale(1)';
    });
    
    // 更新状态
    this.setState({ visible: true });
    
    // 锁定滚动
    document.body.style.overflow = 'hidden';
    
    this.emit('show');
  }
  
  hide() {
    if (!this.state.visible) return;
    
    // 触发动画
    this.backdrop.style.opacity = '0';
    this.element.style.opacity = '0';
    this.dialog.style.transform = 'scale(0.95)';
    
    setTimeout(() => {
      this.backdrop.style.display = 'none';
      this.element.style.display = 'none';
      
      // 从DOM移除
      if (this.backdrop.parentNode) {
        document.body.removeChild(this.backdrop);
      }
      if (this.element.parentNode) {
        document.body.removeChild(this.element);
      }
    }, 200);
    
    // 更新状态
    this.setState({ visible: false });
    
    // 解锁滚动
    document.body.style.overflow = '';
    
    this.emit('hide');
  }
  
  toggle() {
    if (this.state.visible) {
      this.hide();
    } else {
      this.show();
    }
  }
}

/* ===== Toast通知组件 ===== */
class Toast extends BaseComponent {
  static container = null;
  
  static getContainer() {
    if (!Toast.container) {
      Toast.container = document.createElement('div');
      Toast.container.className = 'toast-container fixed top-4 right-4 z-toast flex flex-col gap-2';
      document.body.appendChild(Toast.container);
    }
    return Toast.container;
  }
  
  get defaultOptions() {
    return {
      type: 'info', // success, warning, error, info
      title: '',
      message: '',
      duration: 5000,
      closable: true
    };
  }
  
  get initialState() {
    return {
      visible: false
    };
  }
  
  createElement() {
    this.element = document.createElement('div');
    this.element.className = this.getClasses();
  }
  
  getClasses() {
    const classes = ['toast', 'p-4', 'rounded-lg', 'shadow-lg', 'border', 'bg-white', 'flex', 'items-start', 'gap-3', 'max-w-sm', 'transition-all'];
    
    // 类型样式
    const typeClasses = {
      success: 'border-green-200 bg-green-50',
      warning: 'border-yellow-200 bg-yellow-50',
      error: 'border-red-200 bg-red-50',
      info: 'border-blue-200 bg-blue-50'
    };
    const typeClass = typeClasses[this.options.type];
    if (typeClass) {
      classes.push(typeClass);
    }
    
    return classes.join(' ');
  }
  
  render() {
    const icons = {
      success: 'bi-check-circle-fill text-green-500',
      warning: 'bi-exclamation-triangle-fill text-yellow-500', 
      error: 'bi-x-circle-fill text-red-500',
      info: 'bi-info-circle-fill text-blue-500'
    };
    
    let html = '';
    
    // 图标
    const iconClass = icons[this.options.type] || icons.info;
    html += `<i class="${iconClass} text-lg flex-shrink-0 mt-0.5"></i>`;
    
    // 内容
    html += '<div class="flex-1">';
    if (this.options.title) {
      html += `<div class="font-semibold text-gray-900 mb-1">${this.options.title}</div>`;
    }
    if (this.options.message) {
      html += `<div class="text-sm text-gray-700">${this.options.message}</div>`;
    }
    html += '</div>';
    
    // 关闭按钮
    if (this.options.closable) {
      html += '<button class="toast-close flex-shrink-0 text-gray-400 hover:text-gray-600 text-sm p-1 rounded"><i class="bi bi-x"></i></button>';
    }
    
    this.element.innerHTML = html;
  }
  
  bindEvents() {
    // 关闭按钮
    if (this.options.closable) {
      const closeBtn = this.element.querySelector('.toast-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => {
          this.hide();
        });
      }
    }
  }
  
  show() {
    if (this.state.visible) return;
    
    // 添加到容器
    const container = Toast.getContainer();
    container.appendChild(this.element);
    
    // 触发入场动画
    this.element.style.opacity = '0';
    this.element.style.transform = 'translateX(100%)';
    
    requestAnimationFrame(() => {
      this.element.style.opacity = '1';
      this.element.style.transform = 'translateX(0)';
    });
    
    this.setState({ visible: true });
    
    // 自动隐藏
    if (this.options.duration > 0) {
      setTimeout(() => {
        this.hide();
      }, this.options.duration);
    }
    
    this.emit('show');
  }
  
  hide() {
    if (!this.state.visible) return;
    
    // 触发退场动画
    this.element.style.opacity = '0';
    this.element.style.transform = 'translateX(100%)';
    
    setTimeout(() => {
      if (this.element.parentNode) {
        this.element.parentNode.removeChild(this.element);
      }
    }, 200);
    
    this.setState({ visible: false });
    this.emit('hide');
  }
  
  // 静态方法：快捷创建Toast
  static show(options) {
    const toast = new Toast(null, options);
    toast.show();
    return toast;
  }
  
  static success(message, title = '成功') {
    return Toast.show({ type: 'success', title, message });
  }
  
  static warning(message, title = '警告') {
    return Toast.show({ type: 'warning', title, message });
  }
  
  static error(message, title = '错误') {
    return Toast.show({ type: 'error', title, message });
  }
  
  static info(message, title = '提示') {
    return Toast.show({ type: 'info', title, message });
  }
}

/* ===== 文件上传组件 ===== */
class FileUpload extends BaseComponent {
  get defaultOptions() {
    return {
      accept: '*',
      multiple: false,
      maxSize: 10 * 1024 * 1024, // 10MB
      dragDrop: true,
      preview: true,
      onFileSelect: null,
      onProgress: null,
      onComplete: null,
      onError: null
    };
  }
  
  get initialState() {
    return {
      files: [],
      uploading: false,
      progress: 0,
      dragOver: false
    };
  }
  
  createElement() {
    if (!this.element) {
      this.element = document.createElement('div');
    }
    
    this.element.className = 'file-upload';
    
    // 创建文件输入
    this.fileInput = document.createElement('input');
    this.fileInput.type = 'file';
    this.fileInput.accept = this.options.accept;
    this.fileInput.multiple = this.options.multiple;
    this.fileInput.style.display = 'none';
    
    this.element.appendChild(this.fileInput);
  }
  
  render() {
    const { files, uploading, progress, dragOver } = this.state;
    
    let html = '<input type="file" style="display: none;">';
    
    // 拖拽区域
    const dragOverClass = dragOver ? 'border-primary-500 bg-primary-50' : 'border-gray-300';
    html += `<div class="file-drop-zone border-2 border-dashed ${dragOverClass} rounded-lg p-8 text-center cursor-pointer transition-colors">`;
    
    if (uploading) {
      html += '<div class="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto mb-4"></div>';
      html += `<p class="text-gray-600">上传中... ${progress}%</p>`;
      html += `<div class="w-full bg-gray-200 rounded-full h-2 mt-2"><div class="bg-primary-500 h-2 rounded-full transition-all" style="width: ${progress}%"></div></div>`;
    } else if (files.length > 0) {
      html += '<i class="bi bi-file-earmark-check text-4xl text-green-500 mb-4"></i>';
      html += `<p class="text-gray-700 font-medium">已选择 ${files.length} 个文件</p>`;
      html += '<p class="text-sm text-gray-500 mt-1">点击重新选择</p>';
    } else {
      html += '<i class="bi bi-cloud-upload text-4xl text-gray-400 mb-4"></i>';
      html += '<p class="text-gray-700 font-medium">拖拽文件到这里或点击选择</p>';
      html += `<p class="text-sm text-gray-500 mt-1">支持 ${this.options.accept} 格式</p>`;
    }
    
    html += '</div>';
    
    // 文件列表
    if (files.length > 0 && this.options.preview) {
      html += '<div class="file-list mt-4 space-y-2">';
      files.forEach((file, index) => {
        const fileSize = this.formatFileSize(file.size);
        html += `<div class="file-item flex items-center justify-between p-3 bg-gray-50 rounded-lg">`;
        html += `<div class="flex items-center gap-3">`;
        html += `<i class="bi bi-file-earmark text-gray-400"></i>`;
        html += `<div><div class="font-medium text-sm">${file.name}</div><div class="text-xs text-gray-500">${fileSize}</div></div>`;
        html += `</div>`;
        html += `<button class="file-remove text-gray-400 hover:text-red-500 transition-colors" data-index="${index}"><i class="bi bi-x"></i></button>`;
        html += `</div>`;
      });
      html += '</div>';
    }
    
    this.element.innerHTML = html;
    
    // 重新获取文件输入引用
    this.fileInput = this.element.querySelector('input[type="file"]');
  }
  
  bindEvents() {
    // 点击选择文件
    const dropZone = this.element.querySelector('.file-drop-zone');
    dropZone.addEventListener('click', () => {
      if (!this.state.uploading) {
        this.fileInput.click();
      }
    });
    
    // 文件选择
    this.fileInput.addEventListener('change', (e) => {
      this.handleFileSelect(e.target.files);
    });
    
    // 拖拽事件
    if (this.options.dragDrop) {
      dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        this.setState({ dragOver: true });
      });
      
      dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        this.setState({ dragOver: false });
      });
      
      dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        this.setState({ dragOver: false });
        this.handleFileSelect(e.dataTransfer.files);
      });
    }
    
    // 移除文件
    this.element.addEventListener('click', (e) => {
      const removeBtn = e.target.closest('.file-remove');
      if (removeBtn) {
        const index = parseInt(removeBtn.dataset.index);
        const files = [...this.state.files];
        files.splice(index, 1);
        this.setState({ files });
        this.emit('fileRemove', { index, files });
      }
    });
  }
  
  handleFileSelect(fileList) {
    const files = Array.from(fileList);
    
    // 文件大小检查
    const oversizedFiles = files.filter(file => file.size > this.options.maxSize);
    if (oversizedFiles.length > 0) {
      const maxSizeText = this.formatFileSize(this.options.maxSize);
      Toast.error(`文件大小超出限制（最大 ${maxSizeText}）`);
      return;
    }
    
    const newFiles = this.options.multiple ? [...this.state.files, ...files] : files;
    this.setState({ files: newFiles });
    
    this.emit('fileSelect', { files: newFiles });
    if (this.options.onFileSelect) {
      this.options.onFileSelect(newFiles);
    }
  }
  
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
  
  // 上传文件
  async upload(url, formData = new FormData()) {
    const { files } = this.state;
    if (files.length === 0) return;
    
    this.setState({ uploading: true, progress: 0 });
    
    try {
      // 添加文件到表单
      files.forEach(file => {
        formData.append('files[]', file);
      });
      
      // 创建XMLHttpRequest以支持进度监控
      const xhr = new XMLHttpRequest();
      
      return new Promise((resolve, reject) => {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const progress = Math.round((e.loaded / e.total) * 100);
            this.setState({ progress });
            this.emit('progress', { progress });
            if (this.options.onProgress) {
              this.options.onProgress(progress);
            }
          }
        });
        
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            const response = JSON.parse(xhr.responseText);
            this.setState({ uploading: false, progress: 100 });
            this.emit('complete', { response, files });
            if (this.options.onComplete) {
              this.options.onComplete(response, files);
            }
            resolve(response);
          } else {
            reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
          }
        });
        
        xhr.addEventListener('error', () => {
          reject(new Error('Upload failed'));
        });
        
        xhr.open('POST', url);
        xhr.send(formData);
      });
      
    } catch (error) {
      this.setState({ uploading: false, progress: 0 });
      this.emit('error', { error });
      if (this.options.onError) {
        this.options.onError(error);
      }
      throw error;
    }
  }
  
  // 清空文件
  clear() {
    this.setState({ files: [], uploading: false, progress: 0 });
    this.fileInput.value = '';
  }
}

/* ===== 主题切换器组件 ===== */
class ThemeToggle extends BaseComponent {
  get defaultOptions() {
    return {
      storageKey: 'app-theme',
      defaultTheme: 'light' // light, dark, auto
    };
  }
  
  get initialState() {
    return {
      theme: this.getStoredTheme() || this.options.defaultTheme
    };
  }
  
  createElement() {
    if (!this.element) {
      this.element = document.createElement('button');
    }
    
    this.element.className = 'theme-toggle p-2 rounded-md transition-colors hover:bg-gray-100 dark:hover:bg-gray-700';
    this.element.setAttribute('aria-label', '切换主题');
  }
  
  render() {
    const { theme } = this.state;
    
    const icons = {
      light: 'bi-sun',
      dark: 'bi-moon',
      auto: 'bi-circle-half'
    };
    
    const icon = icons[theme] || icons.light;
    this.element.innerHTML = `<i class="${icon} text-lg"></i>`;
    
    // 应用主题
    this.applyTheme(theme);
  }
  
  bindEvents() {
    this.element.addEventListener('click', () => {
      this.toggleTheme();
    });
  }
  
  toggleTheme() {
    const themes = ['light', 'dark', 'auto'];
    const currentIndex = themes.indexOf(this.state.theme);
    const nextTheme = themes[(currentIndex + 1) % themes.length];
    
    this.setState({ theme: nextTheme });
    this.storeTheme(nextTheme);
    this.emit('themeChange', { theme: nextTheme });
  }
  
  applyTheme(theme) {
    const html = document.documentElement;
    
    if (theme === 'auto') {
      // 根据系统偏好设置主题
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      theme = prefersDark ? 'dark' : 'light';
    }
    
    if (theme === 'dark') {
      html.setAttribute('data-theme', 'dark');
    } else {
      html.removeAttribute('data-theme');
    }
  }
  
  getStoredTheme() {
    return localStorage.getItem(this.options.storageKey);
  }
  
  storeTheme(theme) {
    localStorage.setItem(this.options.storageKey, theme);
  }
  
  onMounted() {
    // 监听系统主题变化
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (this.state.theme === 'auto') {
          this.applyTheme('auto');
        }
      });
    }
  }
}

/* ===== 组件工厂 ===== */
class ComponentFactory {
  static components = new Map([
    ['Button', Button],
    ['Card', Card], 
    ['Modal', Modal],
    ['Toast', Toast],
    ['FileUpload', FileUpload],
    ['ThemeToggle', ThemeToggle]
  ]);
  
  static register(name, componentClass) {
    this.components.set(name, componentClass);
  }
  
  static create(name, element, options) {
    const ComponentClass = this.components.get(name);
    if (!ComponentClass) {
      throw new Error(`Component "${name}" not found`);
    }
    return new ComponentClass(element, options);
  }
  
  // 自动初始化页面中的组件
  static autoInit(selector = '[data-component]') {
    const elements = document.querySelectorAll(selector);
    const instances = [];
    
    elements.forEach(element => {
      const componentName = element.dataset.component;
      const options = element.dataset.options ? JSON.parse(element.dataset.options) : {};
      
      try {
        const instance = this.create(componentName, element, options);
        instances.push(instance);
      } catch (error) {
        console.error(`Failed to initialize component "${componentName}":`, error);
      }
    });
    
    return instances;
  }
}

/* ===== 导出 ===== */
window.Components = {
  BaseComponent,
  Button,
  Card,
  Modal,
  Toast,
  FileUpload,
  ThemeToggle,
  ComponentFactory
};

// 自动初始化
document.addEventListener('DOMContentLoaded', () => {
  ComponentFactory.autoInit();
});