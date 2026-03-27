# SalesMind AI 免费一键部署脚本 (Windows)
# 部署到 Vercel + Railway

param(
    [string]$GithubRepo = "",
    [string]$KimiApiKey = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SalesMind AI 免费部署脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 颜色定义
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"

# 检查命令是否存在
function Test-Command($Command) {
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# 步骤 1: 环境检查
Write-Host "[1/6] 检查环境..." -ForegroundColor $Cyan

$checks = @{
    "Git" = Test-Command "git"
    "Node.js" = Test-Command "node"
    "NPM" = Test-Command "npm"
}

$allPassed = $true
foreach ($check in $checks.GetEnumerator()) {
    if ($check.Value) {
        Write-Host "  ✓ $($check.Key) 已安装" -ForegroundColor $Green
    } else {
        Write-Host "  ✗ $($check.Key) 未安装" -ForegroundColor $Red
        $allPassed = $false
    }
}

if (-not $allPassed) {
    Write-Host ""
    Write-Host "请先安装缺少的工具：" -ForegroundColor $Red
    Write-Host "- Git: https://git-scm.com/download/win" -ForegroundColor $Yellow
    Write-Host "- Node.js: https://nodejs.org (建议 LTS 版本)" -ForegroundColor $Yellow
    exit 1
}

# 步骤 2: 获取必要信息
Write-Host ""
Write-Host "[2/6] 配置信息..." -ForegroundColor $Cyan

if ([string]::IsNullOrWhiteSpace($GithubRepo)) {
    $GithubRepo = Read-Host "请输入 GitHub 仓库地址 (如: https://github.com/username/salesmind.git)"
}

if ([string]::IsNullOrWhiteSpace($KimiApiKey)) {
    $KimiApiKey = Read-Host "请输入 Kimi API Key"
}

# 验证输入
if ([string]::IsNullOrWhiteSpace($GithubRepo) -or [string]::IsNullOrWhiteSpace($KimiApiKey)) {
    Write-Host "错误: GitHub 仓库和 API Key 不能为空" -ForegroundColor $Red
    exit 1
}

# 步骤 3: 推送代码到 GitHub
Write-Host ""
Write-Host "[3/6] 推送代码到 GitHub..." -ForegroundColor $Cyan

# 检查是否在 git 仓库中
if (-not (Test-Path ".git")) {
    Write-Host "  初始化 Git 仓库..." -ForegroundColor $Yellow
    git init
    git add .
    git commit -m "Initial commit for deployment"
} else {
    Write-Host "  Git 仓库已存在" -ForegroundColor $Green
    # 检查是否有未提交的更改
    $status = git status --porcelain
    if ($status) {
        Write-Host "  提交未保存的更改..." -ForegroundColor $Yellow
        git add .
        git commit -m "Update for deployment"
    }
}

# 设置远程仓库
git remote remove origin 2>$null
git remote add origin $GithubRepo

Write-Host "  推送到 GitHub..." -ForegroundColor $Yellow
try {
    git push -u origin main 2>$null
} catch {
    try {
        git push -u origin master 2>$null
    } catch {
        Write-Host "  推送失败，请手动执行: git push -u origin main" -ForegroundColor $Red
    }
}

Write-Host "  ✓ 代码已推送到 GitHub" -ForegroundColor $Green

# 步骤 4: 安装 Vercel CLI
Write-Host ""
Write-Host "[4/6] 安装 Vercel CLI..." -ForegroundColor $Cyan

if (-not (Test-Command "vercel")) {
    Write-Host "  正在安装 Vercel CLI..." -ForegroundColor $Yellow
    npm install -g vercel
    if (-not $?) {
        Write-Host "  安装失败，请手动运行: npm install -g vercel" -ForegroundColor $Red
        exit 1
    }
} else {
    Write-Host "  Vercel CLI 已安装" -ForegroundColor $Green
}

# 步骤 5: 部署前端到 Vercel
Write-Host ""
Write-Host "[5/6] 部署前端到 Vercel..." -ForegroundColor $Cyan
Write-Host "  提示: 如果是第一次使用，会打开浏览器让你登录 Vercel" -ForegroundColor $Yellow
Write-Host "  请使用 GitHub 账号登录" -ForegroundColor $Yellow
Write-Host ""

# 先设置环境变量
$env:KIMI_API_KEY = $KimiApiKey

Set-Location frontend

Write-Host "  安装依赖..." -ForegroundColor $Yellow
npm install

Write-Host ""
Write-Host "  开始部署..." -ForegroundColor $Yellow
Write-Host "  ====================================" -ForegroundColor $Cyan
vercel --prod
Write-Host "  ====================================" -ForegroundColor $Cyan

Set-Location ..

Write-Host ""
Write-Host "  ✓ 前端部署完成!" -ForegroundColor $Green

# 步骤 6: Railway 后端部署指导
Write-Host ""
Write-Host "[6/6] 后端部署 (Railway)..." -ForegroundColor $Cyan
Write-Host ""
Write-Host "  ============================================" -ForegroundColor $Yellow
Write-Host "  Railway 后端需要手动部署，请按以下步骤操作：" -ForegroundColor $Yellow
Write-Host "  ============================================" -ForegroundColor $Yellow
Write-Host ""
Write-Host "  1. 访问 https://railway.app" -ForegroundColor $Cyan
Write-Host "     使用 GitHub 账号登录" -ForegroundColor White
Write-Host ""
Write-Host "  2. 点击 'New Project' → 'Deploy from GitHub repo'" -ForegroundColor $Cyan
Write-Host "     选择你的 salesmind 仓库" -ForegroundColor White
Write-Host ""
Write-Host "  3. 添加数据库：" -ForegroundColor $Cyan
Write-Host "     - 点击 'New' → 'Database' → 'Add PostgreSQL'" -ForegroundColor White
Write-Host "     - 再次点击 'New' → 'Database' → 'Add Redis'" -ForegroundColor White
Write-Host ""
Write-Host "  4. 配置环境变量 (Project Settings → Variables)：" -ForegroundColor $Cyan
Write-Host "     复制以下变量：" -ForegroundColor White
Write-Host "     ----------------------------------------" -ForegroundColor Gray
Write-Host "     DATABASE_URL="`${{Postgres.DATABASE_URL}}" -ForegroundColor White
Write-Host "     REDIS_URL="`${{Redis.REDIS_URL}}" -ForegroundColor White
Write-Host "     KIMI_API_KEY=$KimiApiKey" -ForegroundColor White
Write-Host "     AI_PROVIDER=kimi" -ForegroundColor White
Write-Host "     KIMI_MODEL=kimi-k2-5" -ForegroundColor White
Write-Host "     SECRET_KEY=$(-join ((65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ }))" -ForegroundColor White
Write-Host "     EMAIL_BACKEND=console" -ForegroundColor White
Write-Host "     FROM_EMAIL=noreply@localhost" -ForegroundColor White
Write-Host "     ----------------------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Railway 会自动检测 railway.toml 并部署" -ForegroundColor $Cyan
Write-Host "     部署完成后，记下域名 (如 xxx.up.railway.app)" -ForegroundColor White
Write-Host ""
Write-Host "  6. 回到 Vercel 设置前端环境变量：" -ForegroundColor $Cyan
Write-Host "     Project Settings → Environment Variables" -ForegroundColor White
Write-Host "     NEXT_PUBLIC_API_URL=https://你的railway域名" -ForegroundColor White
Write-Host "     然后 Redeploy" -ForegroundColor White
Write-Host ""

# 保存配置到文件
$config = @{
    github_repo = $GithubRepo
    kimi_api_key = $KimiApiKey
    deployed_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json

$config | Out-File -FilePath ".deploy-config.json" -Encoding UTF8

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  部署脚本执行完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "配置已保存到: .deploy-config.json" -ForegroundColor $Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor $Yellow
Write-Host "1. 完成 Railway 后端部署 (见上文步骤)" -ForegroundColor White
Write-Host "2. 在 Vercel 添加 NEXT_PUBLIC_API_URL 环境变量" -ForegroundColor White
Write-Host "3. 访问你的 Vercel 域名开始使用" -ForegroundColor White
Write-Host ""
Write-Host "遇到问题查看 DEPLOY_FREE.md 文件" -ForegroundColor $Cyan
Write-Host ""

Read-Host "按 Enter 键退出"
