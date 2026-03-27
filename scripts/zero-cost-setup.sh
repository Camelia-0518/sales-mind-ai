#!/bin/bash
# 0成本部署脚本 - 一键部署到免费服务

set -e

echo "🚀 SalesMind AI - 0成本部署"
echo "================================"

# 检查依赖
command -v git >/dev/null 2>&1 || { echo "❌ 需要安装 git"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ 需要安装 npm"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ 需要安装 python3"; exit 1; }

echo "✅ 依赖检查通过"

# 配置
read -p "请输入项目名称 (默认: salesmind): " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-salesmind}

read -p "选择AI提供商 (1=Gemini[免费], 2=Groq[免费], 3=OpenAI[付费]): " AI_CHOICE

# 创建配置
echo "📝 创建配置文件..."

# 后端配置
cat > backend/.env <<EOF
# 0成本配置 - 使用免费服务

# 数据库 - Supabase免费层
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres

# Redis - Supabase或本地
REDIS_URL=redis://localhost:6379/0

# AI配置
EOF

if [ "$AI_CHOICE" = "1" ]; then
    echo "选择: Gemini (免费1500请求/天)"
    read -p "请输入Gemini API Key: " GEMINI_KEY
    cat >> backend/.env <<EOF
GEMINI_API_KEY=$GEMINI_KEY
AI_PROVIDER=gemini
EOF
elif [ "$AI_CHOICE" = "2" ]; then
    echo "选择: Groq (免费20请求/分钟)"
    read -p "请输入Groq API Key: " GROQ_KEY
    cat >> backend/.env <<EOF
GROQ_API_KEY=$GROQ_KEY
AI_PROVIDER=groq
EOF
else
    read -p "请输入OpenAI API Key: " OPENAI_KEY
    cat >> backend/.env <<EOF
OPENAI_API_KEY=$OPENAI_KEY
AI_PROVIDER=openai
EOF
fi

# 邮件配置
cat >> backend/.env <<EOF

# 邮件 - Resend免费层
RESEND_API_KEY=your-resend-key
FROM_EMAIL=noreply@yourdomain.com

# 安全
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=false
EOF

echo "✅ 后端配置完成"

# 前端配置
cat > frontend/.env.local <<EOF
# 前端环境变量
NEXT_PUBLIC_API_URL=https://$PROJECT_NAME-api.up.railway.app
NEXT_PUBLIC_APP_NAME=SalesMind AI
EOF

echo "✅ 前端配置完成"

# 创建部署脚本
cat > deploy.sh <<'EOF'
#!/bin/bash
# 部署脚本

echo "🚀 开始部署..."

# 部署后端到Railway
echo "📦 部署后端到Railway..."
cd backend
if ! command -v railway &> /dev/null; then
    npm install -g @railway/cli
fi

railway login
railway init
railway up

BACKEND_URL=$(railway domain)
echo "✅ 后端部署完成: $BACKEND_URL"

# 更新前端API地址
cd ../frontend
sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=https://$BACKEND_URL|" .env.local

# 部署前端到Vercel
echo "🌐 部署前端到Vercel..."
if ! command -v vercel &> /dev/null; then
    npm install -g vercel
fi

vercel --prod

echo "✅ 部署完成!"
echo ""
echo "🎉 SalesMind AI 已上线"
echo "前端: https://$PROJECT_NAME.vercel.app"
echo "后端: https://$BACKEND_URL"
EOF

chmod +x deploy.sh

echo ""
echo "================================"
echo "✅ 配置完成!"
echo ""
echo "下一步:"
echo "1. 注册免费服务账号:"
echo "   - Supabase: https://supabase.com"
echo "   - Railway: https://railway.app"
echo "   - Vercel: https://vercel.com"
echo "   - Resend: https://resend.com"
echo ""
echo "2. 获取API Keys并填入 backend/.env"
echo ""
echo "3. 运行部署脚本:"
echo "   ./deploy.sh"
echo ""
echo "💰 预计月费: $0"
echo "================================"
