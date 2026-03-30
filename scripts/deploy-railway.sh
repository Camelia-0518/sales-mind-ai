#!/bin/bash
# Railway 部署脚本

set -e

echo "🚄 SalesMind AI - Railway 部署脚本"
echo "====================================="
echo ""

# 检查 railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI 未安装"
    echo "正在安装..."
    npm install -g @railway/cli
fi

echo "✅ Railway CLI 已安装"
echo ""

# 登录 Railway
echo "🔐 请登录 Railway..."
railway login

# 进入后端目录
cd "$(dirname "$0")/../backend"

echo ""
echo "🚀 开始部署后端服务..."

# 初始化项目（如果没有）
railway init --name salesmind-backend

# 添加 PostgreSQL 数据库
echo "📦 检查 PostgreSQL 数据库..."
railway add --database postgres || echo "数据库已存在"

# 添加 Redis
echo "📦 检查 Redis..."
railway add --plugin redis || echo "Redis 已存在"

# 设置环境变量
echo "🔧 配置环境变量..."
railway variables set \
    AI_PROVIDER=kimi \
    KIMI_MODEL=kimi-k2-5 \
    SECRET_KEY="$(openssl rand -hex 32)" \
    ACCESS_TOKEN_EXPIRE_MINUTES=10080 \
    PYTHONUNBUFFERED=1

echo ""
echo "⚠️  请手动设置以下敏感环境变量："
echo "   railway variables set KIMI_API_KEY=your_kimi_api_key"
echo ""

# 部署
echo "🚀 部署中..."
railway up

echo ""
echo "✅ 后端部署完成！"
echo "📊 查看日志: railway logs"
echo "🌐 查看域名: railway domain"
