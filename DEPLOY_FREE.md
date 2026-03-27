# SalesMind AI 免费部署指南

## 架构
- **前端**: Vercel (免费)
- **后端**: Railway (免费额度 $5/月)
- **数据库**: Railway PostgreSQL (免费)
- **缓存/队列**: Railway Redis (免费)

---

## 1. 准备工作

### 需要的账号
1. GitHub 账号
2. Vercel 账号（用 GitHub 登录）
3. Railway 账号（用 GitHub 登录）

### 准备 API Key
- Kimi API Key (已提供)

---

## 2. 部署后端 (Railway)

### 步骤

1. **登录 Railway**
   - 访问 https://railway.app
   - 用 GitHub 账号登录

2. **创建项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 连接你的 GitHub 仓库

3. **添加数据库**
   - 在项目面板点击 "New"
   - 选择 "Database" → "Add PostgreSQL"
   - 再添加 "Add Redis"

4. **配置环境变量**
   在后端服务 Settings → Variables 中添加：
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   REDIS_URL=${{Redis.REDIS_URL}}
   KIMI_API_KEY=你的Kimi API Key
   AI_PROVIDER=kimi
   KIMI_MODEL=kimi-k2-5
   SECRET_KEY=随便生成一个长字符串
   EMAIL_BACKEND=console
   FROM_EMAIL=noreply@localhost
   ```

5. **部署**
   - Railway 会自动检测 `railway.toml` 并部署
   - 等待部署完成，记下域名（如 `https://salesmind-api.up.railway.app`）

---

## 3. 部署前端 (Vercel)

### 步骤

1. **准备代码**
   ```bash
   cd frontend
   npm install
   ```

2. **部署到 Vercel**
   ```bash
   npm i -g vercel
   vercel
   ```

3. **配置环境变量**
   在 Vercel Dashboard → Project Settings → Environment Variables 添加：
   ```
   NEXT_PUBLIC_API_URL=https://你的后端域名.railway.app
   ```

4. **重新部署**
   ```bash
   vercel --prod
   ```

---

## 4. 验证部署

访问你的 Vercel 域名，测试：
1. 注册/登录功能
2. 创建线索
3. AI 生成功能

---

## 5. 免费额度说明

### Railway 免费额度
- $5/月 计算资源
- 500MB PostgreSQL
- 每月 100 小时运行时间（不 sleep）

### Vercel 免费额度
- 100GB 带宽/月
- 6000 分钟构建时间/月
- 无限制请求数

**注意**：Railway 免费项目会在不活跃时 sleep，首次访问可能需要 10-30 秒唤醒。

---

## 6. 问题排查

### 后端无法连接数据库
检查 `DATABASE_URL` 环境变量是否正确设置

### 前端无法连接后端
检查 `NEXT_PUBLIC_API_URL` 是否指向正确的后端地址

### AI 功能不工作
检查 `KIMI_API_KEY` 是否正确

---

## 7. 升级付费方案

如果免费额度不够用：
- Railway Hobby: $5/月（永远在线）
- 或迁移到 Hetzner: €4.51/月

需要升级时告诉我，可以帮你迁移。
