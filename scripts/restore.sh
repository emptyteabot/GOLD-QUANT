#!/bin/bash
# AURUM系统恢复脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKUP_DIR="/opt/aurum/backups"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   AURUM 数据恢复脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 列出可用备份
list_backups() {
    echo -e "\n${YELLOW}可用备份：${NC}"
    ls -lh "$BACKUP_DIR" | grep -E "postgres_|redis_|configs_"
}

# 恢复PostgreSQL
restore_postgres() {
    local backup_file=$1

    echo -e "\n${YELLOW}恢复PostgreSQL数据库...${NC}"

    # 停止后端服务
    docker-compose stop backend

    # 恢复数据库
    gunzip -c "$backup_file" | docker exec -i aurum-postgres psql -U aurum_user aurum

    # 重启服务
    docker-compose start backend

    echo -e "${GREEN}✓ PostgreSQL恢复完成${NC}"
}

# 恢复Redis
restore_redis() {
    local backup_file=$1

    echo -e "\n${YELLOW}恢复Redis数据...${NC}"

    # 停止Redis
    docker-compose stop redis

    # 复制备份文件
    docker cp "$backup_file" aurum-redis:/data/dump.rdb

    # 启动Redis
    docker-compose start redis

    echo -e "${GREEN}✓ Redis恢复完成${NC}"
}

# 主流程
main() {
    list_backups

    echo -e "\n${YELLOW}请输入要恢复的备份时间戳（格式：YYYYMMDD_HHMMSS）：${NC}"
    read -r timestamp

    if [ -z "$timestamp" ]; then
        echo -e "${RED}错误：未输入时间戳${NC}"
        exit 1
    fi

    # 确认恢复
    echo -e "\n${RED}警告：恢复操作将覆盖当前数据！${NC}"
    echo -e "${YELLOW}是否继续？(yes/no)${NC}"
    read -r confirm

    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}已取消恢复操作${NC}"
        exit 0
    fi

    # 执行恢复
    restore_postgres "$BACKUP_DIR/postgres_$timestamp.sql.gz"
    restore_redis "$BACKUP_DIR/redis_$timestamp.rdb"

    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}   恢复完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
}

main
