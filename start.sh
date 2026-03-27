#!/bin/bash
# SalesMind AI - 0成本快速启动脚本
# 支持: Linux, macOS, Windows(WSL)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           🚀 SalesMind AI - 0成本快速启动                  ║"
echo "║                                                            ║"
echo "║   免费服务: Supabase + Railway + Vercel + Gemini          ║"
echo "║   预计月费: $0                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装${NC}"
    echo "请安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker检查通过${NC}"

# 选择部署模式
echo ""
echo "选择部署模式:"
echo "1) 本地开发 (使用docker-compose.free.yml)"
echo "2) 云端部署 (使用免费服务)"
echo "3) 混合模式 (本地DB + 云端AI)"
echo ""
read -p "请输入选项 (1-3): " DEPLOY_MODE

# 模式1: 本地开发
if [ "$DEPLOY_MODE" = "1" ]; then
    echo -e "${BLUE}🛠️ 启动本地开发环境...${NC}"

    # 创建本地环境文件
    if [ ! -f backend/.env ]; then
        echo -e "${YELLOW}📝 创建本地环境配置...${NC}"
        cat > backend/.env <<EOF
# 本地开发配置
DATABASE_URL=postgresql://salesmind:salesmind_local@db:5432/salesmind
REDIS_URL=redis://redis:6379/0
SECRET_KEY=local-dev-key-$(openssl rand -hex 16)
DEBUG=true

# AI配置 - 需要填入免费API Key
# 获取免费Key: https://ai.google.dev (Gemini)
GEMINI_API_KEY=your-gemini-api-key-here
AI_PROVIDER=gemini

# 邮件配置 - 本地开发使用控制台输出
EMAIL_BACKEND=console
FROM_EMAIL=noreply@localhost

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF
        echo -e "${YELLOW}⚠️ 请编辑 backend/.env 填入你的 Gemini API Key${NC}"
    fi

    # 启动服务
    echo -e "${BLUE}🐳 启动Docker服务...${NC}"
    docker-compose -f docker-compose.free.yml up -d db redis

    # 等待数据库就绪
    echo -e "${BLUE}⏳ 等待数据库启动...${NC}"
    sleep 5

    # 启动后端
    docker-compose -f docker-compose.free.yml up -d backend

    # 启动前端
    docker-compose -f docker-compose.free.yml up -d frontend

    echo ""
    echo -e "${GREEN}✅ 本地开发环境已启动!${NC}"
    echo ""
    echo "访问地址:"
    echo "  🌐 前端: http://localhost:3000"
    echo "  🔌 后端: http://localhost:8000"
    echo "  📚 文档: http://localhost:8000/docs"
    echo ""
    echo "常用命令:"
    echo "  查看日志: docker-compose -f docker-compose.free.yml logs -f"
    echo "  停止服务: docker-compose -f docker-compose.free.yml down"
    echo "  重启服务: docker-compose -f docker-compose.free.yml restart"

# 模式2: 云端部署
elif [ "$DEPLOY_MODE" = "2" ]; then
    echo -e "${BLUE}☁️ 准备云端部署...${NC}"

    echo ""
    echo -e "${YELLOW}📋 部署前准备:${NC}"
    echo "1. 注册以下免费服务账号:"
    echo "   • Railway: https://railway.app"
    echo "   • Vercel: https://vercel.com"
    echo "   • Supabase: https://supabase.com"
    echo "   • Resend: https://resend.com"
    echo "   • Gemini: https://ai.google.dev"
    echo ""
    echo "2. 安装 CLI 工具:"

    # 检查并安装 Railway CLI
    if ! command -v railway &> /dev/null; then
        echo -e "${BLUE}📦 安装 Railway CLI...${NC}"
        npm install -g @railway/cli
    fi

    # 检查并安装 Vercel CLI
    if ! command -v vercel &> /dev/null; then
        echo -e "${BLUE}📦 安装 Vercel CLI...${NC}"
        npm install -g vercel
    fi

    echo ""
    echo -e "${GREEN}✅ CLI工具安装完成${NC}"
    echo ""
    echo "下一步操作:"
    echo "1. 登录 Railway: railway login"
    echo "2. 在 Railway 创建项目并添加 Supabase 数据库"
    echo "3. 复制数据库连接字符串"
    echo "4. 运行: ./scripts/deploy-cloud.sh"
    echo ""
    echo -e "${YELLOW}详细步骤请参考 ZERO_COST.md${NC}"

# 模式3: 混合模式
elif [ "$DEPLOY_MODE" = "3" ]; then
    echo -e "${BLUE}🔀 启动混合模式...${NC}"
    echo "本地数据库 + 云端AI服务"

    # 只启动本地DB和Redis
    docker-compose -f docker-compose.free.yml up -d db redis

    echo -e "${YELLOW}⚠️ 请在 backend/.env 中配置:${NC}"
    echo "  DATABASE_URL=postgresql://salesmind:salesmind_local@localhost:5432/salesmind"
    echo "  GEMINI_API_KEY=your-key-here"
    echo ""
    echo "然后运行后端: cd backend && python -m uvicorn app.main:app --reload"

else
    echo -e "${RED}❌ 无效选项${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 完成!${NC}"
