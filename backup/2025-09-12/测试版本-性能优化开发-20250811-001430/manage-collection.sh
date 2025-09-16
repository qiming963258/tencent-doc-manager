#!/bin/bash
# Ubuntu 定时采集系统 管理脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 系统配置
SYSTEM_DIR="/opt/tencent-collection"
PYTHON_CMD="python3"
MAIN_SCRIPT="main.py"
PID_FILE="/var/run/tencent-collection.pid"

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    echo_info "检查系统要求..."
    
    # 检查Python
    if ! command -v $PYTHON_CMD &> /dev/null; then
        echo_error "Python3 未安装"
        exit 1
    fi
    
    # 检查必要的Python包
    required_packages=("playwright" "croniter" "pytz" "pandas" "psutil")
    for package in "${required_packages[@]}"; do
        if ! $PYTHON_CMD -c "import $package" 2>/dev/null; then
            echo_warning "Python包 $package 未安装，正在安装..."
            pip3 install $package
        fi
    done
    
    echo_success "系统要求检查完成"
}

install_service() {
    echo_info "安装系统服务..."
    
    # 创建systemd服务文件
    cat > /etc/systemd/system/tencent-collection.service << EOF
[Unit]
Description=Tencent Document Collection System
After=network.target

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=$SYSTEM_DIR
ExecStart=$PYTHON_CMD $MAIN_SCRIPT start --daemon
ExecStop=$PYTHON_CMD $MAIN_SCRIPT stop
PIDFile=$PID_FILE
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # 重载systemd
    systemctl daemon-reload
    systemctl enable tencent-collection
    
    echo_success "系统服务安装完成"
}

start_service() {
    echo_info "启动采集系统..."
    
    if is_running; then
        echo_warning "系统已在运行中"
        return 0
    fi
    
    cd $SYSTEM_DIR
    nohup $PYTHON_CMD $MAIN_SCRIPT start --daemon > /dev/null 2>&1 &
    echo $! > $PID_FILE
    
    sleep 3
    
    if is_running; then
        echo_success "采集系统启动成功"
    else
        echo_error "采集系统启动失败"
        exit 1
    fi
}

stop_service() {
    echo_info "停止采集系统..."
    
    if [[ -f $PID_FILE ]]; then
        PID=$(cat $PID_FILE)
        if kill -0 $PID 2>/dev/null; then
            kill -TERM $PID
            sleep 5
            
            if kill -0 $PID 2>/dev/null; then
                echo_warning "进程未响应，强制终止..."
                kill -KILL $PID
            fi
        fi
        rm -f $PID_FILE
    fi
    
    # 确保所有相关进程都停止
    pkill -f "$MAIN_SCRIPT"
    
    echo_success "采集系统已停止"
}

restart_service() {
    echo_info "重启采集系统..."
    stop_service
    sleep 2
    start_service
}

is_running() {
    if [[ -f $PID_FILE ]]; then
        PID=$(cat $PID_FILE)
        if kill -0 $PID 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

show_status() {
    echo_info "系统状态："
    
    if is_running; then
        PID=$(cat $PID_FILE)
        echo_success "采集系统正在运行 (PID: $PID)"
        
        # 显示系统资源使用
        if command -v ps &> /dev/null; then
            echo_info "资源使用："
            ps -p $PID -o pid,ppid,pcpu,pmem,etime,cmd --no-headers
        fi
        
        # 显示任务状态
        cd $SYSTEM_DIR
        echo_info "任务状态："
        $PYTHON_CMD $MAIN_SCRIPT status 2>/dev/null | head -20
    else
        echo_warning "采集系统未运行"
    fi
}

show_logs() {
    local lines=${1:-50}
    echo_info "系统日志 (最近 $lines 行)："
    
    if [[ -f "$SYSTEM_DIR/data/system.log" ]]; then
        tail -n $lines "$SYSTEM_DIR/data/system.log"
    else
        echo_warning "日志文件不存在"
    fi
}

add_task() {
    local task_file=$1
    
    if [[ -z "$task_file" ]]; then
        echo_error "请指定任务配置文件"
        echo "用法: $0 add-task <task_file>"
        exit 1
    fi
    
    if [[ ! -f "$task_file" ]]; then
        echo_error "任务配置文件不存在: $task_file"
        exit 1
    fi
    
    echo_info "添加任务: $task_file"
    cd $SYSTEM_DIR
    $PYTHON_CMD $MAIN_SCRIPT add-task --task-file "$task_file"
    
    if [[ $? -eq 0 ]]; then
        echo_success "任务添加成功"
    else
        echo_error "任务添加失败"
        exit 1
    fi
}

remove_task() {
    local task_id=$1
    
    if [[ -z "$task_id" ]]; then
        echo_error "请指定任务ID"
        echo "用法: $0 remove-task <task_id>"
        exit 1
    fi
    
    echo_info "删除任务: $task_id"
    cd $SYSTEM_DIR
    $PYTHON_CMD $MAIN_SCRIPT remove-task --task-id "$task_id"
    
    if [[ $? -eq 0 ]]; then
        echo_success "任务删除成功"
    else
        echo_error "任务删除失败"
        exit 1
    fi
}

list_tasks() {
    echo_info "任务列表："
    cd $SYSTEM_DIR
    $PYTHON_CMD $MAIN_SCRIPT list-tasks | jq . 2>/dev/null || $PYTHON_CMD $MAIN_SCRIPT list-tasks
}

execute_task() {
    local task_id=$1
    
    if [[ -z "$task_id" ]]; then
        echo_error "请指定任务ID"
        echo "用法: $0 execute-task <task_id>"
        exit 1
    fi
    
    echo_info "执行任务: $task_id"
    cd $SYSTEM_DIR
    $PYTHON_CMD $MAIN_SCRIPT execute --task-id "$task_id"
}

cleanup_data() {
    local days=${1:-30}
    
    echo_info "清理 $days 天前的历史数据..."
    cd $SYSTEM_DIR
    $PYTHON_CMD $MAIN_SCRIPT cleanup --days $days
    
    if [[ $? -eq 0 ]]; then
        echo_success "数据清理完成"
    else
        echo_error "数据清理失败"
    fi
}

backup_data() {
    local backup_dir="./backups/$(date +%Y%m%d_%H%M%S)"
    
    echo_info "备份数据到: $backup_dir"
    mkdir -p "$backup_dir"
    
    # 备份数据目录
    if [[ -d "$SYSTEM_DIR/data" ]]; then
        cp -r "$SYSTEM_DIR/data" "$backup_dir/"
    fi
    
    # 备份配置文件
    if [[ -d "$SYSTEM_DIR/config" ]]; then
        cp -r "$SYSTEM_DIR/config" "$backup_dir/"
    fi
    
    # 创建备份信息文件
    cat > "$backup_dir/backup_info.txt" << EOF
备份时间: $(date)
系统版本: 1.0.0
备份路径: $backup_dir
EOF
    
    echo_success "数据备份完成: $backup_dir"
}

show_help() {
    echo "Ubuntu 定时采集系统管理脚本"
    echo ""
    echo "用法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  install         安装系统服务"
    echo "  start           启动采集系统"
    echo "  stop            停止采集系统" 
    echo "  restart         重启采集系统"
    echo "  status          显示系统状态"
    echo "  logs [lines]    显示日志 (默认50行)"
    echo "  add-task <file> 添加任务"
    echo "  remove-task <id> 删除任务"
    echo "  list-tasks      列出所有任务"
    echo "  execute-task <id> 手动执行任务"
    echo "  cleanup [days]  清理历史数据 (默认30天)"
    echo "  backup          备份数据"
    echo "  check           检查系统要求"
    echo "  help            显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start                           # 启动系统"
    echo "  $0 add-task ./config/daily.json   # 添加日常任务"
    echo "  $0 logs 100                       # 显示最近100行日志"
    echo "  $0 cleanup 7                      # 清理7天前的数据"
}

# 主函数
main() {
    case "$1" in
        "install")
            check_requirements
            install_service
            ;;
        "start")
            start_service
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            restart_service
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs $2
            ;;
        "add-task")
            add_task $2
            ;;
        "remove-task")
            remove_task $2
            ;;
        "list-tasks")
            list_tasks
            ;;
        "execute-task")
            execute_task $2
            ;;
        "cleanup")
            cleanup_data $2
            ;;
        "backup")
            backup_data
            ;;
        "check")
            check_requirements
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            echo_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 检查是否以root权限运行
if [[ $EUID -ne 0 ]] && [[ "$1" == "install" ]]; then
    echo_error "安装系统服务需要root权限"
    echo "请使用: sudo $0 install"
    exit 1
fi

# 执行主函数
main "$@"