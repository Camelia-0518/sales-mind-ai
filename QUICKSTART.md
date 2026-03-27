# SalesMind AI - 0成本快速参考

## 🚀 5分钟启动 (本地开发)

```bash
# 1. 克隆项目
git clone https://github.com/yourname/salesmind.git
cd salesmind

# 2. 运行启动脚本
chmod +x start.sh
./start.sh
# 选择选项 1 (本地开发)

# 3. 填入 API Key
nano backend/.env
# 添加: GEMINI_API_KEY=your-key-from-ai.google.dev

# 4. 重启服务
docker-compose -f docker-compose.free.yml restart backend
```

访问: http://localhost:3000

---

## ☁️ 0成本云服务部署

### 1. 注册免费账号 (10分钟)

| 服务 | 链接 | 免费额度 |
|-----|------|---------|
| **Railway** | railway.app | $5/月 |
| **Vercel** | vercel.com | 100GB |
| **Supabase** | supabase.com | 500MB |
| **Resend** | resend.com | 3000/月 |
| **Gemini** | ai.google.dev | 1500/天 |

### 2. 获取API Keys

```bash
# Gemini (免费AI)
访问: https://ai.google.dev
点击 "Get API key"
复制 Key

# Supabase (免费数据库)
创建项目 → Settings → Database → Connection string
复制 PostgreSQL URL

# Resend (免费邮件)
创建 API Key
验证域名 (或用默认测试域名)
```

### 3. 一键部署

```bash
# 安装 CLI
npm install -g @railway/cli vercel

# 部署后端
railway login
railway init
railway up

# 部署前端
vercel --prod
```

---

## 💰 成本对比

| 方案 | 月费 | 适用场景 |
|-----|-----|---------|
| **完全免费** | $0 | < 500用户 |
| **VPS自托管** | $5 | < 2000用户 |
| **混合方案** | $20 | < 5000用户 |
| **全托管** | $100 | > 5000用户 |

### 免费层限制

```yaml
Supabase:
  - 数据库: 500MB
  - 带宽: 2GB/月
  - 请求: 无限

Railway:
  - 运行时间: 500小时/月
  - 内存: 512MB
  - CPU: 共享

Vercel:
  - 带宽: 100GB/月
  - 构建: 6000分钟/月
  - 函数: 无限

Gemini Flash:
  - 请求: 1500/天
  - 速度: 快速
  - 质量: 中上
```

---

## 📊 监控用量

```bash
# 检查数据库大小
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('postgres'));"

# 检查Redis内存
docker-compose exec redis redis-cli INFO memory

# 查看日志
docker-compose logs -f backend
```

### 告警阈值

| 指标 | 黄色警告 | 红色警告 |
|-----|---------|---------|
| 数据库 | 400MB | 480MB |
| AI调用 | 1200/天 | 1450/天 |
| 邮件发送 | 2500/月 | 2900/月 |
| 带宽 | 1.5GB | 1.9GB |

---

## 🔧 常见问题

### Q: 免费额度不够怎么办？
A: 启用缓存，减少AI调用:
```python
# 在 backend/.env
ENABLE_AI_CACHE=true
AI_CACHE_TTL=3600  # 1小时
```

### Q: 如何备份数据？
A: 自动备份脚本:
```bash
# 每天自动备份到本地
0 2 * * * docker-compose exec -T db pg_dump -U salesmind salesmind > backup/$(date +%Y%m%d).sql
```

### Q: 想换到付费服务？
A: 一键迁移:
```bash
# 导出数据
pg_dump $SUPABASE_URL > backup.sql

# 导入到新服务
psql $NEW_DATABASE_URL < backup.sql
```

### Q: 如何监控成本？
A: 成本监控端点:
```bash
curl http://localhost:8000/api/v1/admin/cost-report
```

---

## 🎯 盈利路径

### 免费用户 → 付费用户

```
0-500用户: 完全免费 (成本$0)
    ↓
收入: $0

500-1000用户: 开始收费 $29/月
    ↓
收入: ~$7,250/月
成本: ~$50
利润: ~$7,200/月

1000+用户: 规模化
    ↓
收入: ~$29,000/月 (1000×$29)
成本: ~$200
利润: ~$28,800/月
```

### 快速达到500用户

1. **Product Hunt 发布** → 100-200用户
2. **小红书/即刻分享** → 100-150用户
3. **销售社群推广** → 50-100用户
4. **免费工具引流** → 50-100用户

---

## 📞 获取帮助

- 文档: https://docs.salesmind.ai
- 社区: https://discord.gg/salesmind
- 问题: https://github.com/yourname/salesmind/issues

---

**当前版本**: v1.0.0
**最后更新**: 2026-03-27
**维护者**: SalesMind AI Team
