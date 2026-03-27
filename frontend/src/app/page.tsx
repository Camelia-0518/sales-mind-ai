import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  Zap,
  Target,
  BarChart3,
  MessageSquare,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

export default function LandingPage() {
  const features = [
    {
      icon: MessageSquare,
      title: "AI自动跟进",
      description: "智能生成个性化跟进消息，自动执行多轮对话，让您的销售永不掉线",
    },
    {
      icon: Target,
      title: "智能线索评分",
      description: "AI分析客户潜力，自动打分排序，帮您聚焦高价值线索",
    },
    {
      icon: Zap,
      title: "提案自动生成",
      description: "根据客户需求一键生成专业提案，节省80%文案时间",
    },
    {
      icon: BarChart3,
      title: "数据驱动决策",
      description: "实时追踪转化漏斗，洞察销售瓶颈，持续优化策略",
    },
  ];

  const pricing = [
    {
      name: "Free",
      price: "¥0",
      description: "适合个人销售",
      features: ["50个线索/月", "基础AI跟进", "邮件支持", "基础报表"],
    },
    {
      name: "Pro",
      price: "¥299",
      period: "/月",
      description: "适合专业销售",
      popular: true,
      features: [
        "无限线索",
        "高级AI剧本",
        "提案生成",
        "优先级支持",
        "数据分析",
      ],
    },
    {
      name: "Team",
      price: "¥199",
      period: "/月/人",
      description: "适合销售团队（5人起）",
      features: [
        "团队协作",
        "管理员面板",
        "API访问",
        "专属客户经理",
        "定制培训",
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-blue-600" />
              <span className="text-xl font-bold">SalesMind AI</span>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/login">
                <Button variant="ghost">登录</Button>
              </Link>
              <Link href="/register">
                <Button>免费开始</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-full text-sm font-medium mb-6">
            <Sparkles className="h-4 w-4" />
            AI驱动的销售自动化平台
          </div>
          <h1 className="text-5xl font-bold mb-6 leading-tight">
            让 AI 成为您的
            <br />
            <span className="text-blue-600">超级销售助理</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            自动化跟进、智能评分、一键提案。SalesMind 帮助销售团队提升 3 倍效率，
            让您专注于真正重要的成交环节。
          </p>
          <div className="flex justify-center gap-4">
            <Link href="/register">
              <Button size="lg" className="text-lg px-8">
                免费开始使用
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="text-lg px-8">
              观看演示
            </Button>
          </div>
          <p className="text-sm text-gray-500 mt-4">
            无需信用卡，免费版永久可用
          </p>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">强大功能，简单上手</h2>
            <p className="text-gray-600">专为中文销售场景优化的AI能力</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="bg-white p-6 rounded-xl shadow-sm"
              >
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-600 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">简单透明的定价</h2>
            <p className="text-gray-600">选择适合您的方案，随时升级或降级</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {pricing.map((plan) => (
              <div
                key={plan.name}
                className={`p-6 rounded-xl border ${
                  plan.popular
                    ? "border-blue-500 ring-2 ring-blue-500 ring-opacity-20"
                    : "border-gray-200"
                }`}
              >
                {plan.popular && (
                  <div className="text-sm font-medium text-blue-600 mb-2">
                    最受欢迎
                  </div>
                )}
                <h3 className="text-xl font-semibold mb-2">{plan.name}</h3>
                <div className="flex items-baseline mb-4">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  <span className="text-gray-500 ml-1">{plan.period}</span>
                </div>
                <p className="text-gray-600 text-sm mb-6">{plan.description}</p>
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Link href="/register">
                  <Button
                    className="w-full"
                    variant={plan.popular ? "default" : "outline"}
                  >
                    选择方案
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-blue-600 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            准备好提升销售效率了吗？
          </h2>
          <p className="text-blue-100 mb-8">
            加入数千名销售专家，让 AI 成为您的得力助手
          </p>
          <Link href="/register">
            <Button size="lg" variant="secondary" className="text-lg px-8">
              立即免费开始
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="h-5 w-5 text-blue-600" />
            <span className="font-semibold">SalesMind AI</span>
          </div>
          <p className="text-gray-500 text-sm">
            © 2026 SalesMind AI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
