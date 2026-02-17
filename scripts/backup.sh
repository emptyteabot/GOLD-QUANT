#!/bin/bash
# AURUM数据备份脚本

set -e

# 配置
BACKUP_DIR="/opt/aurum/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   AURUM 数据备份脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份PostgreSQL数据库
backup_postgres() {
    echo -e "\n${YELLOW}[1/4] 备份PostgreSQL数据库...${NC}"

    docker exec aurum-postgres pg_dump -U aurum_user aurum | gzip > "$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz"

    echo -e "${GREEN}✓ PostgreSQL备份完成: postgres_$TIMESTAMP.sql.gz${NC}"
}

# 备份Redis数据
backup_redis() {
    echo -e "\n${YELLOW}[2/4] 备份Redis数据...${NC}"

    docker exec aurum-redis redis-cli --rdb /data/dump.rdb save
    docker cp aurum-redis:/data/dump.rdb "$BACKUP_DIR/redis_$TIMESTAMP.rdb"

    echo -e "${GREEN}✓ Redis备份完成: redis_$TIMESTAMP.rdb${NC}"
}

# 备份配置文件
backup_configs() {
    echo -e "\n${YELLOW}[3/4] 备份配置文件...${NC}"

    tar -czf "$BACKUP_DIR/configs_$TIMESTAMP.tar.gz" \
        .env \
        docker-compose.yml \
        monitoring/ \
        scripts/ \
        2>/dev/null || true

    echo -e "${GREEN}✓ 配置文件备份完成: configs_$TIMESTAMP.tar.gz${NC}"
}

# 清理旧备份
cleanup_old_backups() {
    echo -e "\n${YELLOW}[4/4] 清理旧备份（保留${RETENTION_DAYS}天）...${NC}"

    find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete

    echo -e "${GREEN}✓ 旧备份清理完成${NC}"
}

# 显示备份信息
show_backup_info() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}   备份完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "\n备份文件："
    ls -lh "$BACKUP_DIR"/*_$TIMESTAMP.* 2>/dev/null || echo "无备份文件"

    echo -e "\n备份目录大小："
    du -sh "$BACKUP_DIR"
}

# 主流程
main() {
    backup_postgres
    backup_redis
    backup_configs
    cleanup_old_backups
    show_backup_info
}

# 执行备份
main
