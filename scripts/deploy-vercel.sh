#!/bin/bash
# Vercel 部署脚本

set -e

echo "▲ SalesMind AI - Vercel 部署脚本"
echo "=================================="
echo ""

# 检查 vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI 未安装"
    echo "正在安装..."
    npm install -g vercel
fi

echo "✅ Vercel CLI 已安装"
echo ""

# 进入前端目录
cd "$(dirname "$0")/../frontend"

echo "🔧 安装依赖..."
npm install

echo ""
echo "🔐 请登录 Vercel..."
vercel login

echo ""
echo "🚀 开始部署前端..."

# 首次部署
vercel --prod

echo ""
echo "✅ 前端部署完成！"
echo ""
echo "⚠️  重要：请设置环境变量 NEXT_PUBLIC_API_URL"
echo "   vercel env add NEXT_PUBLIC_API_URL"
echo "   值为你的 Railway 后端域名，例如: https://salesmind-backend.up.railway.app"
