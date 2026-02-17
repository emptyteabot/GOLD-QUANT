#!/bin/bash

# ==========================================
# AURUM Railway 部署脚本
# ==========================================
# 功能：自动化部署AURUM到Railway平台
# 使用：./deploy-to-railway.sh
# ==========================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Railway CLI是否安装
check_railway_cli() {
    print_info "检查Railway CLI..."
    if ! command -v railway &> /dev/null; then
        print_error "Railway CLI未安装"
        print_info "请运行以下命令安装："
        echo "  npm install -g @railway/cli"
        echo "  或访问: https://docs.railway.app/develop/cli"
        exit 1
    fi
    print_success "Railway CLI已安装"
}

# 检查是否已登录Railway
check_railway_login() {
    print_info "检查Railway登录状态..."
    if ! railway whoami &> /dev/null; then
        print_error "未登录Railway"
        print_info "正在启动登录流程..."
        railway login
    fi
    print_success "已登录Railway"
}

# 检查必要文件
check_required_files() {
    print_info "检查必要文件..."

    local required_files=(
        "main.py"
        "config.py"
        "requirements.txt"
        "railway.json"
        "nixpacks.toml"
        "Procfile"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "缺少必要文件: $file"
            exit 1
        fi
    done

    print_success "所有必要文件存在"
}

# 检查环境变量配置
check_env_config() {
    print_info "检查环境变量配置..."

    if [ ! -f ".env.trading" ]; then
        print_warning ".env.trading文件不存在"
        print_info "请确保在Railway上配置了所有必要的环境变量"
        read -p "是否继续？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success ".env.trading文件存在"
    fi
}

# 初始化Railway项目
init_railway_project() {
    print_info "初始化Railway项目..."

    if [ ! -f ".railway" ]; then
        print_info "未检测到Railway项目，正在创建..."
        railway init
    else
        print_success "Railway项目已存在"
    fi
}

# 设置环境变量
setup_env_variables() {
    print_info "设置环境变量..."

    if [ -f ".env.railway" ]; then
        print_warning "检测到.env.railway模板文件"
        print_info "请手动在Railway Dashboard中配置环境变量"
        print_info "访问: https://railway.app/dashboard"
        read -p "环境变量已配置完成？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "请先配置环境变量"
            exit 1
        fi
    fi

    print_success "环境变量配置确认"
}

# 部署到Railway
deploy_to_railway() {
    print_info "开始部署到Railway..."

    # 添加所有文件到git
    print_info "准备文件..."
    git add .

    # 提交更改
    print_info "提交更改..."
    git commit -m "Deploy AURUM to Railway - $(date '+%Y-%m-%d %H:%M:%S')" || true

    # 部署
    print_info "执行部署..."
    railway up

    print_success "部署完成！"
}

# 显示部署信息
show_deployment_info() {
    print_info "获取部署信息..."

    echo ""
    echo "=========================================="
    echo "  AURUM Railway 部署信息"
    echo "=========================================="

    # 获取项目信息
    railway status

    echo ""
    print_info "查看日志："
    echo "  railway logs"

    print_info "打开Dashboard："
    echo "  railway open"

    print_info "查看环境变量："
    echo "  railway variables"

    echo "=========================================="
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  AURUM Railway 自动部署脚本"
    echo "=========================================="
    echo ""

    # 执行检查
    check_railway_cli
    check_railway_login
    check_required_files
    check_env_config

    # 初始化和部署
    init_railway_project
    setup_env_variables
    deploy_to_railway

    # 显示信息
    show_deployment_info

    echo ""
    print_success "🎉 部署流程完成！"
    echo ""
}

# 运行主函数
main
