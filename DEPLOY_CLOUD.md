# SalesMind AI - 云端部署指南

## 架构

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Vercel    │ ───▶ │   Railway   │ ───▶ │   Railway   │
│  (Next.js)  │      │  (FastAPI)  │      │ PostgreSQL  │
│  静态导出    │      │             │      │             │
└─────────────┘      └──────┬──────┘      └─────────────┘
                            │
                            ▼
                      ┌─────────────┐
                      │   Railway   │
                      │   Redis     │
                      └─────────────┘
```

## 前置要求

1. **Railway 账号**: https://railway.app (GitHub 登录)
2. **Vercel 账号**: https://vercel.com (GitHub 登录)
3. **Railway CLI**: `npm install -g @railway/cli`
4. **Vercel CLI**: `npm install -g vercel`

## 部署步骤

### 1. 部署后端到 Railway

```bash
# 方式1: 使用脚本
cd scripts
bash deploy-railway.sh

# 方式2: 手动部署
cd backend

# 登录 Railway
railway login

# 初始化项目
railway init --name salesmind-backend

# 添加数据库和 Redis
railway add --database postgres
railway add --plugin redis

# 设置环境变量
railway variables set \
    AI_PROVIDER=kimi \
    KIMI_MODEL=kimi-k2-5 \
    KIMI_API_KEY=sk-xxx \
    SECRET_KEY=$(openssl rand -hex 32) \
    ACCESS_TOKEN_EXPIRE_MINUTES=10080 \
    PYTHONUNBUFFERED=1

# 部署
railway up
```

### 2. 获取后端域名

部署完成后：

```bash
railway domain
# 输出: https://salesmind-backend.up.railway.app
```

### 3. 部署前端到 Vercel

```bash
# 方式1: 使用脚本
cd scripts
bash deploy-vercel.sh

# 方式2: 手动部署
cd frontend

# 登录 Vercel
vercel login

# 设置 API URL (替换为实际的后端域名)
vercel env add NEXT_PUBLIC_API_URL
# 输入: https://salesmind-backend.up.railway.app

# 部署
vercel --prod
```

## 环境变量清单

### Railway (后端)

| 变量 | 说明 | 来源 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 连接 | Railway 自动生成 |
| `REDIS_URL` | Redis 连接 | Railway 自动生成 |
| `KIMI_API_KEY` | Kimi API 密钥 | 手动设置 |
| `SECRET_KEY` | JWT 密钥 | 手动设置 (随机32字符) |
| `AI_PROVIDER` | AI 提供商 | 固定: kimi |
| `KIMI_MODEL` | 模型名称 | 固定: kimi-k2-5 |

### Vercel (前端)

| 变量 | 说明 | 值 |
|------|------|-----|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址 | Railway 域名 |

## 常用命令

```bash
# 查看后端日志
railway logs

# 重启后端
railway up

# 进入后端控制台
railway shell

# 查看前端部署状态
vercel list

# 前端本地预览
vercel --version
```

## 故障排查

### 后端启动失败

1. 检查环境变量是否全部设置
2. 查看日志: `railway logs`
3. 确认数据库迁移: `railway run alembic upgrade head`

### 前端无法连接后端

1. 确认 `NEXT_PUBLIC_API_URL` 设置正确
2. 检查后端健康端点: `https://your-domain.up.railway.app/health`
3. 确认 CORS 配置允许前端域名

### 数据库连接问题

1. Railway 会自动注入 `DATABASE_URL`
2. 如需手动连接: `railway connect postgres`

## 费用预估

| 服务 | 免费额度 | 超出费用 |
|------|----------|----------|
| Railway | $5/月 | 按需计费 |
| Vercel | 100GB 带宽/月 | $0.12/GB |
| PostgreSQL | 共享 CPU, 1GB | 升级 $5/月 |
| Redis | 共享 | 升级 $3/月 |

**注意**: 个人项目通常免费额度足够。

## 更新部署

### 更新后端

```bash
cd backend
git add .
git commit -m "更新功能"
git push
railway up
```

### 更新前端

```bash
cd frontend
git add .
git commit -m "更新功能"
git push
vercel --prod
```

## 监控

- **Railway Dashboard**: https://railway.app/dashboard
- **Vercel Dashboard**: https://vercel.com/dashboard

---

**部署时间**: 约 10-15 分钟
**维护**: 每次代码更新后重新部署
