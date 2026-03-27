#!/usr/bin/env node
/**
 * Jarvis Project Detector
 * 自动检测项目类型和状态
 */

const fs = require('fs');
const path = require('path');

const PROJECT_SIGNATURES = {
  'nextjs': ['next.config.js', 'next.config.ts', 'next.config.mjs'],
  'react': ['src/App.jsx', 'src/App.tsx', 'vite.config.ts', 'vite.config.js'],
  'vue': ['vue.config.js', 'vite.config.ts', 'src/App.vue'],
  'nuxt': ['nuxt.config.ts', 'nuxt.config.js'],
  'fastapi': ['main.py', 'app/main.py', 'requirements.txt'],
  'django': ['manage.py', 'requirements.txt', 'settings.py'],
  'nodejs': ['package.json'],
  'python': ['requirements.txt', 'setup.py', 'pyproject.toml'],
  'rust': ['Cargo.toml'],
  'go': ['go.mod'],
  'flutter': ['pubspec.yaml'],
  'react-native': ['ios/', 'android/', 'App.js']
};

const TECH_STACK_SIGNATURES = {
  'typescript': ['tsconfig.json'],
  'prisma': ['prisma/schema.prisma', 'schema.prisma'],
  'tailwind': ['tailwind.config.js', 'tailwind.config.ts'],
  'jest': ['jest.config.js', 'jest.config.ts'],
  'vitest': ['vitest.config.ts'],
  'docker': ['Dockerfile', 'docker-compose.yml'],
  'graphql': ['schema.graphql', 'apollo.config.js'],
  'nextauth': ['auth.ts', 'auth.config.ts', '[...nextauth]'],
  'stripe': ['stripe.ts', 'stripe.js'],
  'supabase': ['supabase/']
};

function findFiles(dir, signatures) {
  const found = [];
  for (const sig of signatures) {
    const fullPath = path.join(dir, sig);
    if (fs.existsSync(fullPath)) {
      found.push(sig);
    }
  }
  return found;
}

function detectProjectType(dir = process.cwd()) {
  for (const [type, signatures] of Object.entries(PROJECT_SIGNATURES)) {
    if (findFiles(dir, signatures).length > 0) {
      return type;
    }
  }
  return 'unknown';
}

function detectTechStack(dir = process.cwd()) {
  const stack = [];
  for (const [tech, signatures] of Object.entries(TECH_STACK_SIGNATURES)) {
    if (findFiles(dir, signatures).length > 0) {
      stack.push(tech);
    }
  }

  // 读取package.json获取更多信息
  const pkgPath = path.join(dir, 'package.json');
  if (fs.existsSync(pkgPath)) {
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
    const deps = { ...pkg.dependencies, ...pkg.devDependencies };

    if (deps.zustand) stack.push('zustand');
    if (deps.redux || deps['@reduxjs/toolkit']) stack.push('redux');
    if (deps['react-query'] || deps['@tanstack/react-query']) stack.push('react-query');
    if (deps.axios) stack.push('axios');
    if (deps.trpc) stack.push('trpc');
  }

  return stack;
}

function detectProjectStage(dir = process.cwd()) {
  // 检查Git状态
  const gitDir = path.join(dir, '.git');
  if (!fs.existsSync(gitDir)) {
    return 'init';
  }

  // 检查测试覆盖率
  const coverageDir = path.join(dir, 'coverage');
  if (fs.existsSync(coverageDir)) {
    return 'testing';
  }

  // 检查CI配置
  const ciDir = path.join(dir, '.github/workflows');
  if (fs.existsSync(ciDir)) {
    return 'deploy-ready';
  }

  // 检查src目录大小
  const srcDir = path.join(dir, 'src');
  if (fs.existsSync(srcDir)) {
    const files = fs.readdirSync(srcDir, { recursive: true });
    if (files.length > 20) {
      return 'development';
    }
  }

  return 'setup';
}

function generateProjectDNA(dir = process.cwd()) {
  const type = detectProjectType(dir);
  const stack = detectTechStack(dir);
  const stage = detectProjectStage(dir);

  return {
    detected_at: new Date().toISOString(),
    project_type: type,
    tech_stack: stack,
    stage: stage,
    recommendations: generateRecommendations(type, stack, stage)
  };
}

function generateRecommendations(type, stack, stage) {
  const recs = [];

  // 根据阶段推荐
  if (stage === 'init') {
    recs.push({
      type: 'setup',
      priority: 'high',
      message: '项目刚初始化，建议配置开发环境',
      actions: ['配置ESLint/Prettier', '设置Git hooks', '创建基础目录结构']
    });
  }

  // 根据技术栈推荐
  if (type === 'nextjs' && !stack.includes('typescript')) {
    recs.push({
      type: 'tech',
      priority: 'medium',
      message: 'Next.js项目建议启用TypeScript',
      actions: ['迁移到TypeScript']
    });
  }

  if (!stack.includes('testing')) {
    recs.push({
      type: 'quality',
      priority: 'medium',
      message: '尚未配置测试框架',
      actions: ['安装Vitest/Jest', '配置React Testing Library']
    });
  }

  return recs;
}

// CLI模式
if (require.main === module) {
  const dna = generateProjectDNA();
  console.log(JSON.stringify(dna, null, 2));
}

module.exports = {
  detectProjectType,
  detectTechStack,
  detectProjectStage,
  generateProjectDNA
};
