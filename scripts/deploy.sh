#!/bin/bash
# AURUM一键部署脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   AURUM 黄金量化交易系统 - 部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查环境
check_requirements() {
    echo -e "\n${YELLOW}[1/7] 检查系统环境...${NC}"

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: 未安装Docker${NC}"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}错误: 未安装Docker Compose${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ 环境检查通过${NC}"
}

# 配置环境变量
setup_env() {
    echo -e "\n${YELLOW}[2/7] 配置环境变量...${NC}"

    if [ ! -f .env ]; then
        echo -e "${YELLOW}未找到.env文件，创建默认配置...${NC}"
        cat > .env << EOF
# 数据库配置
POSTGRES_PASSWORD=aurum_pass_2026
REDIS_PASSWORD=redis_pass_2026
RABBITMQ_PASSWORD=rabbitmq_pass_2026

# Grafana配置
GRAFANA_PASSWORD=admin_2026

# OKX API配置（请填写真实密钥）
OKX_API_KEY=your_api_key_here
OKX_SECRET_KEY=your_secret_key_here
OKX_PASSPHRASE=your_passphrase_here

# 环境
ENVIRONMENT=production
EOF
        echo -e "${YELLOW}请编辑.env文件，填入真实的API密钥${NC}"
        read -p "按Enter继续..."
    fi

    echo -e "${GREEN}✓ 环境变量配置完成${NC}"
}

# 创建必要目录
create_directories() {
    echo -e "\n${YELLOW}[3/7] 创建目录结构...${NC}"

    mkdir -p logs data backups monitoring/grafana/{dashboards,datasources}

    echo -e "${GREEN}✓ 目录创建完成${NC}"
}

# 初始化数据库
init_database() {
    echo -e "\n${YELLOW}[4/7] 初始化数据库...${NC}"

    # 创建数据库初始化脚本
    cat > scripts/init-db.sql << 'EOF'
-- 创建TimescaleDB扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 创建表
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    price DECIMAL(18, 8) NOT NULL,
    quantity DECIMAL(18, 8) NOT NULL,
    pnl DECIMAL(18, 8),
    strategy VARCHAR(50)
);

-- 转换为时序表
SELECT create_hypertable('trades', 'timestamp', if_not_exists => TRUE);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades (symbol);

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建策略配置表
CREATE TABLE IF NOT EXISTS strategy_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    strategy_name VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
EOF

    echo -e "${GREEN}✓ 数据库脚本准备完成${NC}"
}

# 拉取镜像
pull_images() {
    echo -e "\n${YELLOW}[5/7] 拉取Docker镜像...${NC}"

    docker-compose pull

    echo -e "${GREEN}✓ 镜像拉取完成${NC}"
}

# 启动服务
start_services() {
    echo -e "\n${YELLOW}[6/7] 启动服务...${NC}"

    docker-compose up -d

    echo -e "${GREEN}✓ 服务启动完成${NC}"
}

# 健康检查
health_check() {
    echo -e "\n${YELLOW}[7/7] 健康检查...${NC}"

    sleep 10

    # 检查各服务状态
    services=("postgres" "redis" "rabbitmq" "backend" "frontend" "prometheus" "grafana")

    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "$service.*Up"; then
            echo -e "${GREEN}✓ $service 运行正常${NC}"
        else
            echo -e "${RED}✗ $service 启动失败${NC}"
        fi
    done

    # 检查后端API
    echo -e "\n检查后端API..."
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo -e "${GREEN}✓ 后端API正常${NC}"
    else
        echo -e "${YELLOW}⚠ 后端API未响应（可能还在启动中）${NC}"
    fi
}

# 显示访问信息
show_info() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}   部署完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "\n访问地址："
    echo -e "  前端界面: ${GREEN}http://localhost:3000${NC}"
    echo -e "  后端API:  ${GREEN}http://localhost:8000${NC}"
    echo -e "  Grafana:  ${GREEN}http://localhost:3001${NC} (admin/admin_2026)"
    echo -e "  Prometheus: ${GREEN}http://localhost:9090${NC}"
    echo -e "  RabbitMQ: ${GREEN}http://localhost:15672${NC} (aurum/rabbitmq_pass_2026)"
    echo -e "\n常用命令："
    echo -e "  查看日志: ${YELLOW}docker-compose logs -f [service]${NC}"
    echo -e "  停止服务: ${YELLOW}docker-compose down${NC}"
    echo -e "  重启服务: ${YELLOW}docker-compose restart${NC}"
    echo -e "  查看状态: ${YELLOW}docker-compose ps${NC}"
    echo -e "\n${RED}⚠ 警告: 请确保已在.env中配置真实的OKX API密钥${NC}"
}

# 主流程
main() {
    check_requirements
    setup_env
    create_directories
    init_database
    pull_images
    start_services
    health_check
    show_info
}

# 执行部署
main
