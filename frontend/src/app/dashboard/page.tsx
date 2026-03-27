"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Plus,
  Users,
  TrendingUp,
  MessageSquare,
  LogOut,
  Upload,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/contexts/auth-context";
import { leadsApi, DashboardStats, Lead } from "@/lib/api";

export default function DashboardPage() {
  const { user, token, logout, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !token) {
      router.push("/login");
      return;
    }

    if (token) {
      loadDashboardData();
    }
  }, [token, authLoading, router]);

  const loadDashboardData = async () => {
    try {
      const data = await leadsApi.getDashboardStats(token!);
      setStats(data);
    } catch (error) {
      console.error("Failed to load dashboard:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      new: "secondary",
      contacted: "default",
      qualified: "default",
      proposal: "default",
      negotiation: "default",
      closed_won: "default",
      closed_lost: "destructive",
    };
    const labels: Record<string, string> = {
      new: "新线索",
      contacted: "已联系",
      qualified: "已确认",
      proposal: "提案中",
      negotiation: "谈判中",
      closed_won: "已成交",
      closed_lost: "已流失",
    };
    return <Badge variant={variants[status] || "default"}>{labels[status] || status}</Badge>;
  };

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (!user || !stats) {
    return null;
  }

  const quotaPercentage = (stats.quota.used / stats.quota.total) * 100;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-blue-600" />
              <h1 className="text-xl font-bold">SalesMind AI</h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{user.name}</span>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-2" />
                退出
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold">欢迎回来，{user.name}</h2>
          <p className="text-gray-500 mt-1">这是您今天的销售概览</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">总线索</CardTitle>
              <Users className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_leads}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">AI评分均值</CardTitle>
              <TrendingUp className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.average_ai_score}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">AI跟进中</CardTitle>
              <MessageSquare className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.status_distribution.contacted || 0}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">套餐</CardTitle>
              <span className="text-xs font-medium px-2 py-1 bg-blue-100 text-blue-700 rounded">
                {stats.plan}
              </span>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-gray-600">
                {stats.quota.used} / {stats.quota.total}
              </div>
              <Progress value={quotaPercentage} className="mt-2" />
            </CardContent>
          </Card>
        </div>

        {/* Actions */}
        <div className="flex gap-4 mb-8">
          <Link href="/leads/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              新增线索
            </Button>
          </Link>
          <Link href="/leads/import">
            <Button variant="outline">
              <Upload className="h-4 w-4 mr-2" />
              批量导入
            </Button>
          </Link>
          <Link href="/leads">
            <Button variant="outline">查看全部线索</Button>
          </Link>
        </div>

        {/* Recent Leads */}
        <Card>
          <CardHeader>
            <CardTitle>最近线索</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.recent_leads.length === 0 ? (
                <p className="text-gray-500 text-center py-8">暂无线索，点击上方按钮添加</p>
              ) : (
                stats.recent_leads.map((lead) => (
                  <div
                    key={lead.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-semibold">
                        {lead.name[0]}
                      </div>
                      <div>
                        <p className="font-medium">{lead.name}</p>
                        <p className="text-sm text-gray-500">
                          {lead.company} {lead.title && `· ${lead.title}`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {getStatusBadge(lead.status)}
                      <div className="text-sm text-gray-500">AI评分: {lead.ai_score}</div>
                      <Link href={`/leads/${lead.id}`}>
                        <Button variant="outline" size="sm">
                          详情
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
