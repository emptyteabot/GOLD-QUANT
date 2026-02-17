# AURUM后端完整部署指南

## 📋 目录
1. [开发环境部署](#开发环境部署)
2. [生产环境部署](#生产环境部署)
3. [Docker部署](#docker部署)
4. [常见问题](#常见问题)

---

## 开发环境部署

### 前置要求
- Python 3.8+
- PostgreSQL 15+
- Git

### 步骤1: 克隆项目
```bash
cd backend
```

### 步骤2: 创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 步骤3: 安装依赖
```bash
pip install -r requirements.txt
```

### 步骤4: 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件
# Windows: notepad .env
# Linux/Mac: nano .env
```

必须修改的配置：
```env
DATABASE_URL=postgresql://用户名:密码@localhost:5432/aurum_db
SECRET_KEY=生成的随机密钥
ENCRYPTION_KEY=生成的加密密钥
```

生成密钥：
```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# ENCRYPTION_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 步骤5: 初始化数据库

#### 方式1: 使用SQL脚本（推荐）
```bash
# 确保PostgreSQL已启动
# Windows: net start postgresql-x64-15
# Linux: sudo systemctl start postgresql

# 执行初始化脚本
psql -U postgres -f init_database.sql
```

#### 方式2: 使用Python脚本
```bash
python init_db.py
```

### 步骤6: 启动服务
```bash
# Windows
启动后端服务.bat

# Linux/Mac
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 步骤7: 验证安装
```bash
# 运行完整性测试
python test_complete.py

# 或访问
# http://localhost:8000/docs
# http://localhost:8000/health
```

---

## 生产环境部署

### 步骤1: 服务器准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install -y python3.10 python3-pip postgresql nginx
```

### 步骤2: 配置PostgreSQL
```bash
# 创建数据库用户
sudo -u postgres psql
CREATE USER aurum WITH PASSWORD 'your_secure_password';
CREATE DATABASE aurum_db OWNER aurum;
GRANT ALL PRIVILEGES ON DATABASE aurum_db TO aurum;
\q

# 初始化数据库
psql -U aurum -d aurum_db -f init_database.sql
```

### 步骤3: 部署应用
```bash
# 创建应用目录
sudo mkdir -p /var/www/aurum
cd /var/www/aurum

# 克隆代码
git clone <your-repo> .

# 安装依赖
pip3 install -r requirements.txt

# 配置环境变量
sudo nano .env
```

生产环境配置：
```env
DEBUG=False
DATABASE_URL=postgresql://aurum:password@localhost:5432/aurum_db
SECRET_KEY=生产环境随机密钥
ENCRYPTION_KEY=生产环境加密密钥
CORS_ORIGINS=["https://yourdomain.com"]
```

### 步骤4: 使用Gunicorn部署
```bash
# 安装Gunicorn
pip3 install gunicorn

# 创建systemd服务
sudo nano /etc/systemd/system/aurum.service
```

服务配置：
```ini
[Unit]
Description=AURUM API Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/aurum
Environment="PATH=/var/www/aurum/venv/bin"
ExecStart=/var/www/aurum/venv/bin/gunicorn app.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile /var/log/aurum/access.log \
    --error-logfile /var/log/aurum/error.log

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
# 创建日志目录
sudo mkdir -p /var/log/aurum
sudo chown www-data:www-data /var/log/aurum

# 启动服务
sudo systemctl daemon-reload
sudo systemctl start aurum
sudo systemctl enable aurum

# 查看状态
sudo systemctl status aurum
```

### 步骤5: 配置Nginx反向代理
```bash
sudo nano /etc/nginx/sites-available/aurum
```

Nginx配置：
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/aurum /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 步骤6: 配置SSL证书（Let's Encrypt）
```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d api.yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## Docker部署

### Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: aurum_db
      POSTGRES_USER: aurum
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init_database.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://aurum:your_password@db:5432/aurum_db
      SECRET_KEY: your_secret_key
      ENCRYPTION_KEY: your_encryption_key
    depends_on:
      - db
    volumes:
      - .:/app

volumes:
  postgres_data:
```

### 启动Docker
```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

---

## 常见问题

### 1. 数据库连接失败
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 检查端口
sudo netstat -tlnp | grep 5432

# 测试连接
psql -U aurum -d aurum_db -h localhost
```

### 2. 端口被占用
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux
lsof -i :8000
kill -9 <PID>
```

### 3. 依赖安装失败
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 升级pip
pip install --upgrade pip
```

### 4. 权限问题
```bash
# Linux
sudo chown -R $USER:$USER /var/www/aurum
chmod -R 755 /var/www/aurum
```

### 5. 查看日志
```bash
# Gunicorn日志
tail -f /var/log/aurum/error.log

# Nginx日志
tail -f /var/log/nginx/error.log

# systemd日志
journalctl -u aurum -f
```

---

## 性能优化

### 1. 数据库优化
```sql
-- 创建索引
CREATE INDEX CONCURRENTLY idx_orders_user_symbol
    ON orders(user_id, symbol, created_at DESC);

-- 分析表
ANALYZE users;
ANALYZE orders;
ANALYZE positions;

-- 清理
VACUUM ANALYZE;
```

### 2. 应用优化
```python
# 增加worker数量
gunicorn app.main:app -w 8 -k uvicorn.workers.UvicornWorker

# 配置连接池
# 在config.py中
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 40
```

### 3. Nginx优化
```nginx
# 启用gzip压缩
gzip on;
gzip_types application/json;

# 缓存静态文件
location /static {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

---

## 监控和维护

### 1. 健康检查
```bash
# 添加到crontab
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart aurum
```

### 2. 备份数据库
```bash
# 每日备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -U aurum aurum_db | gzip > /backup/aurum_db_$DATE.sql.gz
find /backup -name "*.gz" -mtime +30 -delete
```

### 3. 日志轮转
```bash
# /etc/logrotate.d/aurum
/var/log/aurum/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload aurum
    endscript
}
```

---

## 安全建议

1. **使用强密码**: 数据库和JWT密钥使用随机生成的强密码
2. **启用HTTPS**: 生产环境必须使用SSL证书
3. **限制访问**: 配置防火墙，只开放必要端口
4. **定期更新**: 及时更新依赖包和系统补丁
5. **备份数据**: 定期备份数据库和配置文件
6. **监控日志**: 定期检查错误日志和访问日志

---

## 支持

如有问题，请查看：
- API文档: http://localhost:8000/docs
- 项目README: README.md
- 快速开始: QUICKSTART.md

---

**部署完成后，记得运行测试验证所有功能正常！**

```bash
python test_complete.py
```
