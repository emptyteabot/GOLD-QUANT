#!/bin/bash
# AURUM系统监控脚本

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查服务状态
check_services() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   AURUM 服务状态${NC}"
    echo -e "${GREEN}========================================${NC}\n"

    services=("postgres" "redis" "rabbitmq" "backend" "frontend" "prometheus" "grafana")

    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "aurum-$service.*Up"; then
            echo -e "${GREEN}✓${NC} $service: 运行中"
        else
            echo -e "${RED}✗${NC} $service: 已停止"
        fi
    done
}

# 检查资源使用
check_resources() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}   系统资源使用${NC}"
    echo -e "${GREEN}========================================${NC}\n"

    # CPU使用率
    cpu_usage=$(docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}" | grep aurum)
    echo -e "${YELLOW}CPU使用率：${NC}"
    echo "$cpu_usage"

    # 内存使用
    echo -e "\n${YELLOW}内存使用：${NC}"
    docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}" | grep aurum

    # 磁盘使用
    echo -e "\n${YELLOW}磁盘使用：${NC}"
    df -h | grep -E "/$|/opt"
}

# 检查日志错误
check_logs() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}   最近错误日志${NC}"
    echo -e "${GREEN}========================================${NC}\n"

    docker-compose logs --tail=50 backend | grep -i error || echo "无错误日志"
}

# 检查交易状态
check_trading() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}   交易系统状态${NC}"
    echo -e "${GREEN}========================================${NC}\n"

    # 调用后端API获取状态
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} 后端API正常"

        # 获取交易统计
        stats=$(curl -s http://localhost:8000/api/stats 2>/dev/null || echo "{}")
        echo -e "\n交易统计："
        echo "$stats" | python3 -m json.tool 2>/dev/null || echo "无法获取统计数据"
    else
        echo -e "${RED}✗${NC} 后端API无响应"
    fi
}

# 主流程
main() {
    clear
    check_services
    check_resources
    check_logs
    check_trading

    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}   监控完成 - $(date)${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# 循环监控模式
if [ "$1" == "--watch" ]; then
    while true; do
        main
        sleep 30
    done
else
    main
fi
