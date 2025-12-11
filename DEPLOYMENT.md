# VMAF-Video-QCTest 部署文档

## 系统要求

### 硬件要求
- CPU: 4 核心以上 (VMAF 计算为 CPU 密集型)
- 内存: 8GB 以上
- 存储: 50GB 以上 (视频文件存储)

### 软件要求
- Docker 20.10+
- Docker Compose 2.0+

## 快速部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd vmaf-video-qctest
```

### 2. 配置环境变量

复制示例配置文件并根据需要修改：

```bash
cp backend/.env.example backend/.env
```

主要配置项：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| DEBUG | 调试模式 | true |
| HOST | 服务监听地址 | 0.0.0.0 |
| PORT | 服务端口 | 8000 |
| CORS_ORIGINS | 允许的前端源 | ["http://localhost:5173"] |
| MAX_FILE_SIZE | 最大文件大小 (字节) | 4294967296 (4GB) |
| MAX_CONCURRENT_TASKS | 最大并发任务数 | 3 |
| DATABASE_URL | 数据库连接 | sqlite+aiosqlite:///./vmaf_qctest.db |

### 3. 启动服务

```bash
docker-compose up -d --build
```

### 4. 访问服务

- 前端界面: http://localhost
- API 文档: http://localhost/api/docs

## 开发环境部署

### 后端开发

```bash
cd backend

# 安装依赖
poetry install

# 创建环境变量文件
cp .env.example .env

# 启动开发服务器
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 运行测试

```bash
# 后端测试
cd backend
poetry run pytest -v

# 前端测试
cd frontend
npm run test
```

## 生产环境部署

### 1. 配置生产环境变量

```bash
# backend/.env
DEBUG=false
CORS_ORIGINS=["https://your-domain.com"]
MAX_CONCURRENT_TASKS=5
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/vmaf_qctest
```

### 2. 修改 docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    restart: always
    environment:
      - DEBUG=false
    volumes:
      - uploads:/app/uploads
      - reports:/app/reports
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

  frontend:
    build: ./frontend
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - /etc/letsencrypt:/etc/letsencrypt:ro

volumes:
  uploads:
  reports:
```

### 3. HTTPS 配置

使用 Let's Encrypt 获取 SSL 证书：

```bash
# 安装 certbot
apt install certbot

# 获取证书
certbot certonly --standalone -d your-domain.com

# 配置 nginx
# 参考 frontend/nginx.conf
```

### 4. 数据库迁移 (可选)

如果使用 PostgreSQL：

```bash
# 安装 PostgreSQL 驱动
poetry add asyncpg

# 创建数据库
docker-compose exec db psql -U postgres -c "CREATE DATABASE vmaf_qctest;"
```

## 架构说明

```
┌──────────────────────────────────────────────────┐
│                   Nginx                          │
│              (反向代理 + 静态文件)                  │
└──────────────────┬───────────────────────────────┘
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│    Frontend     │  │    Backend      │
│  (React SPA)    │  │   (FastAPI)     │
└─────────────────┘  └────────┬────────┘
                              │
                     ┌────────┴────────┐
                     │                 │
                     ▼                 ▼
              ┌───────────┐    ┌───────────┐
              │  SQLite/  │    │  FFmpeg   │
              │PostgreSQL │    │ (libvmaf) │
              └───────────┘    └───────────┘
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 80/443 | Web 界面 |
| Backend | 8000 | API 服务 (内部) |

## 目录结构

```
/app
├── uploads/          # 上传的视频文件
│   └── chunks/       # 分片临时目录
├── reports/          # 生成的报告文件
└── vmaf_qctest.db    # SQLite 数据库
```

## 健康检查

```bash
# 检查后端服务
curl http://localhost:8000/api/health

# 检查前端服务
curl http://localhost/
```

## 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 只查看后端日志
docker-compose logs -f backend

# 只查看前端日志
docker-compose logs -f frontend
```

## 备份与恢复

### 备份数据

```bash
# 备份数据库
docker-compose exec backend cp /app/vmaf_qctest.db /app/backups/

# 备份上传文件
tar -czf uploads_backup.tar.gz uploads/

# 备份报告文件
tar -czf reports_backup.tar.gz reports/
```

### 恢复数据

```bash
# 恢复数据库
docker cp vmaf_qctest.db vmaf-backend:/app/

# 恢复上传文件
tar -xzf uploads_backup.tar.gz -C /path/to/uploads/

# 恢复报告文件
tar -xzf reports_backup.tar.gz -C /path/to/reports/
```

## 常见问题

### 1. FFmpeg 找不到 libvmaf

确保 Docker 镜像正确构建了 FFmpeg：

```bash
docker-compose exec backend ffmpeg -filters | grep vmaf
```

### 2. 上传大文件超时

调整 Nginx 配置：

```nginx
client_max_body_size 4G;
proxy_read_timeout 3600;
proxy_send_timeout 3600;
```

### 3. VMAF 计算慢

- 增加 `MAX_CONCURRENT_TASKS` 限制并发
- 考虑使用更多 CPU 核心
- 对于 4K 视频，评估时间可能需要数小时

### 4. 磁盘空间不足

定期清理:

```bash
# 清理超过 30 天的报告
find /app/reports -mtime +30 -delete

# 清理未完成的上传分片
find /app/uploads/chunks -mtime +1 -delete
```

## 性能调优

### CPU 优化

```bash
# 设置 FFmpeg 线程数
VMAF_THREADS=4
```

### 内存优化

```bash
# 限制容器内存
docker-compose up -d --scale backend=1 -m 4g
```

### 存储优化

- 使用 SSD 存储视频文件
- 配置适当的文件系统 (ext4/xfs)
- 考虑使用对象存储 (S3/MinIO)

## 监控

### Prometheus 指标 (可选)

```python
# 在 main.py 添加
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

### 健康检查端点

```bash
curl http://localhost:8000/api/health
# {"status": "healthy", "version": "0.1.0"}
```

## 联系支持

如有问题，请提交 Issue 或联系开发团队。
