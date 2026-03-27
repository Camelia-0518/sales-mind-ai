# SalesMind AI - 生产部署指南

## 系统要求

- Docker & Docker Compose
- 2GB+ RAM
- 10GB+ 磁盘空间

## 快速部署 (推荐)

### 1. 环境准备

```bash
# 克隆项目
cd salesmind

# 创建环境文件
cp backend/.env.example backend/.env

# 编辑环境变量
nano backend/.env
```

### 2. 配置环境变量

编辑 `backend/.env`:

```env
# Database (Docker自动配置)
DATABASE_URL=postgresql://postgres:postgres@db:5432/salesmind
REDIS_URL=redis://redis:6379/0

# Security (必须修改)
SECRET_KEY=your-super-secret-key-here-min-32-chars-long

# AI APIs (必须配置)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Email (可选)
SENDGRID_API_KEY=SG.xxx
FROM_EMAIL=noreply@salesmind.ai
```

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 4. 访问应用

- **前端界面**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **API端点**: http://localhost:8000

## 手动部署

### 后端部署 (Railway)

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 启动
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端部署 (Vercel)

```bash
cd frontend

# 安装依赖
npm install

# 构建
npm run build

# 启动
npm start
```

## 监控与维护

### 查看日志

```bash
# 所有服务
docker-compose logs

# 特定服务
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery
```

### 数据库备份

```bash
# 备份
docker-compose exec db pg_dump -U postgres salesmind > backup.sql

# 恢复
cat backup.sql | docker-compose exec -T db psql -U postgres salesmind
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 重建并重启
docker-compose down
docker-compose up -d --build
```

## 性能优化

### 1. 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_leads_user_id ON leads(user_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_conversations_lead_id ON conversations(lead_id);
```

### 2. Redis缓存

- 用户会话缓存
- API响应缓存
- 频繁查询缓存

### 3. Celery任务队列

- 邮件发送
- AI生成任务
- 数据分析

## 安全配置

### 1. HTTPS (Nginx反向代理)

```nginx
server {
    listen 443 ssl;
    server_name salesmind.ai;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
    }
}
```

### 2. 防火墙规则

```bash
# 开放端口
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp

# 启用防火墙
ufw enable
```

## 故障排查

### 常见问题

**数据库连接失败**
```bash
# 检查数据库状态
docker-compose ps db
docker-compose logs db
```

**AI功能不工作**
```bash
# 检查API密钥
docker-compose exec backend python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

**前端无法访问**
```bash
# 检查前端日志
docker-compose logs frontend
```

## 扩展建议

### 1. 高可用架构

- 负载均衡器 (Nginx/HAProxy)
- 多后端实例
- 数据库主从复制
- Redis集群

### 2. 监控告警

- Prometheus + Grafana
- 日志收集 (ELK Stack)
- 错误追踪 (Sentry)
- 性能监控 (New Relic)

### 3. CI/CD流水线

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to server
        run: |
          ssh user@server "cd /opt/salesmind && git pull && docker-compose up -d --build"
```

## 成本估算

### 云服务部署 (月均)

| 组件 | 配置 | 价格 |
|-----|------|-----|
| 前端 | Vercel Pro | $20 |
| 后端 | Railway Pro | $50 |
| 数据库 | Railway PostgreSQL | $30 |
| Redis | Railway Redis | $10 |
| AI API | OpenAI + Claude | ~$50-100 |
| 邮件 | SendGrid | $15 |
| **总计** | | **~$175-225/月** |

### 自建服务器

| 配置 | 价格/月 |
|-----|--------|
| 4核8G云服务器 | ~$30 |
| AI API调用 | ~$50-100 |
| **总计** | **~$80-130/月** |

---

**文档版本**: v1.0
**更新日期**: 2026-03-27
