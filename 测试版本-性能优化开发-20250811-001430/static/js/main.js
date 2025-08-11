/**
 * 腾讯文档导出工具 - 核心JavaScript类库
 * 提供主题管理、状态管理、UI组件等核心功能
 */

class TencentDocExporter {
    constructor() {
        this.config = {
            apiBase: '/api',
            themes: ['light', 'dark'],
            storageKeys: {
                theme: 'tencent_exporter_theme',
                cookies: 'tencent_exporter_cookies',
                history: 'tencent_exporter_history'
            }
        };
        
        this.state = {
            isExporting: false,
            currentTheme: 'light',
            exportProgress: 0,
            lastExportResult: null
        };
        
        this.elements = {};
        this.toastContainer = null;
        
        this.init();
    }
    
    /**
     * 初始化应用
     */
    init() {
        this.initializeElements();
        this.initializeTheme();
        this.initializeEventListeners();
        this.loadStoredData();
        this.createToastContainer();
        
        console.log('腾讯文档导出工具初始化完成');
    }
    
    /**
     * 初始化DOM元素引用
     */
    initializeElements() {
        this.elements = {
            themeToggle: document.querySelector('.theme-toggle'),
            exportForm: document.querySelector('.export-form'),
            urlInput: document.querySelector('#doc-url'),
            formatRadios: document.querySelectorAll('input[name="export-format"]'),
            exportButton: document.querySelector('#export-button'),
            cookieToggle: document.querySelector('.cookie-toggle'),
            cookieContent: document.querySelector('.cookie-content'),
            cookieInput: document.querySelector('#cookies'),
            exportStatus: document.querySelector('.export-status'),
            exportResult: document.querySelector('.export-result'),
            exportError: document.querySelector('.export-error'),
            progressBar: document.querySelector('.progress-bar'),
            progressText: document.querySelector('.export-progress-text span:last-child'),
            historyList: document.querySelector('.history-list')
        };
    }
    
    /**
     * 初始化主题系统
     */
    initializeTheme() {
        const savedTheme = localStorage.getItem(this.config.storageKeys.theme) || 'light';
        this.setTheme(savedTheme);
    }
    
    /**
     * 设置主题
     */
    setTheme(theme) {
        if (!this.config.themes.includes(theme)) {
            theme = 'light';
        }
        
        document.documentElement.setAttribute('data-theme', theme);
        this.state.currentTheme = theme;
        localStorage.setItem(this.config.storageKeys.theme, theme);
        
        // 更新主题切换按钮状态
        if (this.elements.themeToggle) {
            this.elements.themeToggle.setAttribute('aria-pressed', theme === 'dark');
        }
        
        this.showToast(`已切换到${theme === 'dark' ? '深色' : '浅色'}模式`, 'success');
    }
    
    /**
     * 切换主题
     */
    toggleTheme() {
        const newTheme = this.state.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }
    
    /**
     * 初始化事件监听器
     */
    initializeEventListeners() {
        // 主题切换
        if (this.elements.themeToggle) {
            this.elements.themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
        
        // Cookie设置折叠
        if (this.elements.cookieToggle) {
            this.elements.cookieToggle.addEventListener('click', () => {
                this.toggleCookieSection();
            });
        }
        
        // 表单提交
        if (this.elements.exportForm) {
            this.elements.exportForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.startExport();
            });
        }
        
        // URL输入验证
        if (this.elements.urlInput) {
            this.elements.urlInput.addEventListener('input', (e) => {
                this.validateUrl(e.target.value);
            });
        }
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (!this.state.isExporting) {
                        this.startExport();
                    }
                } else if (e.key === 'd') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            }
        });
    }
    
    /**
     * 创建Toast通知容器
     */
    createToastContainer() {
        this.toastContainer = document.createElement('div');
        this.toastContainer.className = 'toast-container';
        this.toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-width: 400px;
        `;
        document.body.appendChild(this.toastContainer);
    }
    
    /**
     * 显示Toast通知
     */
    showToast(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: '✓',
            warning: '⚠',
            error: '✕',
            info: 'ℹ'
        };
        
        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" type="button">✕</button>
        `;
        
        // 关闭按钮事件
        const closeButton = toast.querySelector('.toast-close');
        closeButton.addEventListener('click', () => {
            this.removeToast(toast);
        });
        
        // 添加到容器
        this.toastContainer.appendChild(toast);
        
        // 自动移除
        setTimeout(() => {
            this.removeToast(toast);
        }, duration);
        
        return toast;
    }
    
    /**
     * 移除Toast通知
     */
    removeToast(toast) {
        if (toast && toast.parentNode) {
            toast.style.animation = 'toast-exit 0.3s ease';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }
    }
    
    /**
     * 切换Cookie设置区域
     */
    toggleCookieSection() {
        if (this.elements.cookieContent) {
            const isExpanded = this.elements.cookieContent.classList.contains('expanded');
            if (isExpanded) {
                this.elements.cookieContent.classList.remove('expanded');
            } else {
                this.elements.cookieContent.classList.add('expanded');
            }
        }
    }
    
    /**
     * 验证URL格式
     */
    validateUrl(url) {
        const tencentDocPattern = /^https:\/\/docs\.qq\.com\/(sheet|doc|slide)\//;
        const input = this.elements.urlInput;
        
        if (!url) {
            this.setInputState(input, 'neutral');
            return false;
        }
        
        if (tencentDocPattern.test(url)) {
            this.setInputState(input, 'valid');
            return true;
        } else {
            this.setInputState(input, 'invalid');
            return false;
        }
    }
    
    /**
     * 设置输入框状态
     */
    setInputState(input, state) {
        input.classList.remove('valid', 'invalid');
        if (state !== 'neutral') {
            input.classList.add(state);
        }
    }
    
    /**
     * 获取当前导出格式
     */
    getSelectedFormat() {
        const checkedRadio = document.querySelector('input[name="export-format"]:checked');
        return checkedRadio ? checkedRadio.value : 'excel';
    }
    
    /**
     * 获取Cookie设置
     */
    getCookies() {
        return this.elements.cookieInput ? this.elements.cookieInput.value.trim() : '';
    }
    
    /**
     * 开始导出
     */
    async startExport() {
        if (this.state.isExporting) {
            return;
        }
        
        const url = this.elements.urlInput.value.trim();
        const format = this.getSelectedFormat();
        const cookies = this.getCookies();
        
        // 验证URL
        if (!url) {
            this.showToast('请输入腾讯文档URL', 'warning');
            this.elements.urlInput.focus();
            return;
        }
        
        if (!this.validateUrl(url)) {
            this.showToast('请输入有效的腾讯文档URL', 'error');
            this.elements.urlInput.focus();
            return;
        }
        
        // 设置导出状态
        this.state.isExporting = true;
        this.updateExportButton(true);
        this.showExportStatus();
        this.updateProgress(0, '准备导出...');
        
        try {
            // 调用API
            const response = await this.callExportAPI(url, format, cookies);
            
            if (response.success) {
                await this.handleExportSuccess(response);
            } else {
                throw new Error(response.error || '导出失败');
            }
        } catch (error) {
            this.handleExportError(error);
        } finally {
            this.state.isExporting = false;
            this.updateExportButton(false);
            this.hideExportStatus();
        }
    }
    
    /**
     * 调用导出API
     */
    async callExportAPI(url, format, cookies) {
        const response = await fetch(`${this.config.apiBase}/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                doc_url: url,
                format: format,
                cookies: cookies
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    /**
     * 处理导出成功
     */
    async handleExportSuccess(response) {
        this.updateProgress(100, '导出完成');
        
        // 保存到历史记录
        this.saveToHistory({
            url: this.elements.urlInput.value,
            format: this.getSelectedFormat(),
            fileName: response.file_name,
            timestamp: new Date().toISOString(),
            success: true
        });
        
        // 显示结果
        this.showExportResult(response);
        
        // 自动下载
        if (response.download_url) {
            await this.downloadFile(response.download_url, response.file_name);
        }
        
        this.showToast('文档导出成功!', 'success');
    }
    
    /**
     * 处理导出错误
     */
    handleExportError(error) {
        console.error('导出错误:', error);
        
        this.saveToHistory({
            url: this.elements.urlInput.value,
            format: this.getSelectedFormat(),
            error: error.message,
            timestamp: new Date().toISOString(),
            success: false
        });
        
        this.showExportError(error);
        this.showToast(`导出失败: ${error.message}`, 'error');
    }
    
    /**
     * 更新导出按钮状态
     */
    updateExportButton(isLoading) {
        if (this.elements.exportButton) {
            if (isLoading) {
                this.elements.exportButton.disabled = true;
                this.elements.exportButton.innerHTML = `
                    <div class="spinner spinner-sm"></div>
                    正在导出...
                `;
            } else {
                this.elements.exportButton.disabled = false;
                this.elements.exportButton.innerHTML = `
                    <i class="icon-download"></i>
                    开始导出
                `;
            }
        }
    }
    
    /**
     * 显示导出状态
     */
    showExportStatus() {
        if (this.elements.exportStatus) {
            this.elements.exportStatus.classList.add('active');
        }
    }
    
    /**
     * 隐藏导出状态
     */
    hideExportStatus() {
        if (this.elements.exportStatus) {
            this.elements.exportStatus.classList.remove('active');
        }
    }
    
    /**
     * 更新进度
     */
    updateProgress(percent, message) {
        if (this.elements.progressBar) {
            this.elements.progressBar.style.width = `${percent}%`;
        }
        
        if (this.elements.progressText) {
            this.elements.progressText.textContent = `${percent}%`;
        }
        
        // 模拟进度增长
        if (percent < 100 && this.state.isExporting) {
            setTimeout(() => {
                if (this.state.isExporting) {
                    this.updateProgress(Math.min(percent + 10, 90), message);
                }
            }, 500);
        }
    }
    
    /**
     * 显示导出结果
     */
    showExportResult(result) {
        if (this.elements.exportResult) {
            const resultCard = this.elements.exportResult.querySelector('.export-result-card');
            if (resultCard) {
                resultCard.innerHTML = `
                    <div class="export-result-header">
                        <div class="export-result-icon">✓</div>
                        <div class="export-result-title">导出成功</div>
                    </div>
                    <div class="export-result-details">
                        <div class="export-result-detail">
                            <span>文件名:</span>
                            <span>${result.file_name}</span>
                        </div>
                        <div class="export-result-detail">
                            <span>文件大小:</span>
                            <span>${this.formatFileSize(result.file_size || 0)}</span>
                        </div>
                        <div class="export-result-detail">
                            <span>导出格式:</span>
                            <span>${this.getSelectedFormat().toUpperCase()}</span>
                        </div>
                    </div>
                    <div class="export-result-actions">
                        <button class="btn btn-primary" onclick="window.exporterApp.downloadFile('${result.download_url}', '${result.file_name}')">
                            <i class="icon-download"></i>
                            下载文件
                        </button>
                        <button class="btn btn-outline" onclick="window.exporterApp.shareResult('${result.file_name}')">
                            <i class="icon-share"></i>
                            分享
                        </button>
                    </div>
                `;
            }
            
            this.elements.exportResult.classList.add('success');
        }
    }
    
    /**
     * 显示导出错误
     */
    showExportError(error) {
        if (this.elements.exportError) {
            this.elements.exportError.innerHTML = `
                <div class="export-error-header">
                    <div class="export-error-icon">✕</div>
                    <div class="export-error-title">导出失败</div>
                </div>
                <div class="export-error-message">${error.message}</div>
                ${error.details ? `<div class="export-error-details">${error.details}</div>` : ''}
            `;
            this.elements.exportError.classList.add('active');
        }
    }
    
    /**
     * 下载文件
     */
    async downloadFile(url, fileName) {
        try {
            const link = document.createElement('a');
            link.href = url;
            link.download = fileName;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('下载失败:', error);
            this.showToast('下载失败，请手动下载', 'error');
        }
    }
    
    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    /**
     * 保存到历史记录
     */
    saveToHistory(record) {
        try {
            const history = this.getHistory();
            history.unshift(record);
            
            // 只保留最近20条记录
            if (history.length > 20) {
                history.splice(20);
            }
            
            localStorage.setItem(this.config.storageKeys.history, JSON.stringify(history));
            this.updateHistoryDisplay();
        } catch (error) {
            console.error('保存历史记录失败:', error);
        }
    }
    
    /**
     * 获取历史记录
     */
    getHistory() {
        try {
            const stored = localStorage.getItem(this.config.storageKeys.history);
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.error('读取历史记录失败:', error);
            return [];
        }
    }
    
    /**
     * 更新历史记录显示
     */
    updateHistoryDisplay() {
        if (!this.elements.historyList) return;
        
        const history = this.getHistory();
        
        if (history.length === 0) {
            this.elements.historyList.innerHTML = '<div class="text-center text-muted">暂无历史记录</div>';
            return;
        }
        
        this.elements.historyList.innerHTML = history.map(record => `
            <div class="history-item">
                <div class="history-item-header">
                    <div class="history-item-title">
                        ${record.fileName || '导出记录'}
                        ${record.success ? '<span class="status-indicator success">成功</span>' : '<span class="status-indicator error">失败</span>'}
                    </div>
                    <div class="history-item-time">
                        ${new Date(record.timestamp).toLocaleString()}
                    </div>
                </div>
                <div class="history-item-url">${record.url}</div>
                <div class="history-item-actions">
                    <button class="btn btn-sm btn-outline" onclick="window.exporterApp.fillFromHistory('${record.url}', '${record.format}')">
                        重新导出
                    </button>
                    ${record.success && record.fileName ? `
                        <button class="btn btn-sm btn-ghost">
                            查看详情
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }
    
    /**
     * 从历史记录填充表单
     */
    fillFromHistory(url, format) {
        if (this.elements.urlInput) {
            this.elements.urlInput.value = url;
            this.validateUrl(url);
        }
        
        const formatRadio = document.querySelector(`input[name="export-format"][value="${format}"]`);
        if (formatRadio) {
            formatRadio.checked = true;
        }
        
        // 滚动到表单
        if (this.elements.exportForm) {
            this.elements.exportForm.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    /**
     * 加载存储的数据
     */
    loadStoredData() {
        // 加载Cookie设置
        const savedCookies = localStorage.getItem(this.config.storageKeys.cookies);
        if (savedCookies && this.elements.cookieInput) {
            this.elements.cookieInput.value = savedCookies;
        }
        
        // 更新历史记录显示
        this.updateHistoryDisplay();
    }
    
    /**
     * 保存Cookie设置
     */
    saveCookies() {
        const cookies = this.getCookies();
        if (cookies) {
            localStorage.setItem(this.config.storageKeys.cookies, cookies);
            this.showToast('Cookie设置已保存', 'success');
        }
    }
}

// 创建全局实例
window.exporterApp = new TencentDocExporter();

// 添加样式到文档头部
const style = document.createElement('style');
style.textContent = `
    @keyframes toast-exit {
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    .form-input.valid {
        border-color: var(--success);
    }
    
    .form-input.invalid {
        border-color: var(--error);
    }
    
    .icon-download::before { content: '⬇'; }
    .icon-share::before { content: '↗'; }
`;
document.head.appendChild(style);