# AURUM后端快速开始指南

## 前置要求

- Python 3.8+
- PostgreSQL 15+
- Redis 7+ (可选)

## 安装步骤

### 1. 安装Python依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境变量模板：
```bash
cp .env.example .env
```

编辑`.env`文件，修改数据库连接信息：
```env
DATABASE_URL=postgresql://用户名:密码@localhost:5432/aurum_db
SECRET_KEY=你的随机密钥
ENCRYPTION_KEY=你的加密密钥
```

生成随机密钥：
```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# ENCRYPTION_KEY (需要32字节)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. 初始化数据库

#### 方式1: 使用SQL脚本（推荐）

```bash
# 连接PostgreSQL并执行初始化脚本
psql -U postgres -f init_database.sql
```

#### 方式2: 使用Python脚本

```bash
python init_db.py
```

### 4. 启动服务

#### Windows:
```bash
启动后端服务.bat
```

#### Linux/Mac:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 验证安装

访问以下地址：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 测试API

运行测试脚本：
```bash
python test_api.py
```

或使用curl测试：

### 注册用户
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "test123456",
    "full_name": "测试用户"
  }'
```

### 登录
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123456"
  }'
```

### 获取用户信息（需要token）
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 常见问题

### 1. 数据库连接失败

检查PostgreSQL是否运行：
```bash
# Windows
net start postgresql-x64-15

# Linux
sudo systemctl start postgresql
```

### 2. 端口被占用

修改`.env`中的端口或停止占用8000端口的程序：
```bash
# Windows
netstat -ano | findstr :8000

# Linux
lsof -i :8000
```

### 3. 依赖安装失败

使用国内镜像源：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 开发模式

启用调试模式，修改`.env`：
```env
DEBUG=True
```

## 生产部署

1. 关闭调试模式：`DEBUG=False`
2. 修改密钥为随机值
3. 使用Gunicorn部署：
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 下一步

- 查看完整API文档: http://localhost:8000/docs
- 阅读`README.md`了解更多功能
- 查看`docs/06_后端API详细设计.md`了解API设计
