"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectItem,
} from "@/components/ui/select";
import { Plus, Search, Sparkles, LogOut } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";
import { leadsApi, Lead } from "@/lib/api";

const statusLabels: Record<string, string> = {
  new: "新线索",
  contacted: "已联系",
  qualified: "已确认",
  proposal: "提案中",
  negotiation: "谈判中",
  closed_won: "已成交",
  closed_lost: "已流失",
};

export default function LeadsPage() {
  const { user, token, logout } = useAuth();
  const router = useRouter();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<string>("all");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }
    loadLeads();
  }, [token, router]);

  const loadLeads = async () => {
    try {
      const data = await leadsApi.getLeads(token!, {
        search: search || undefined,
        status: status !== "all" ? status : undefined,
      });
      setLeads(data);
    } catch (error) {
      console.error("Failed to load leads:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = () => {
    loadLeads();
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const handleDelete = async (id: number) => {
    if (!confirm("确定要删除这个线索吗？")) return;
    try {
      await leadsApi.deleteLead(token!, id);
      loadLeads();
    } catch (error) {
      alert("删除失败");
    }
  };

  if (!token || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-blue-600" />
              <Link href="/dashboard" className="text-xl font-bold">
                SalesMind AI
              </Link>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{user?.name}</span>
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
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold">线索管理</h1>
          <Link href="/leads/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              新增线索
            </Button>
          </Link>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="搜索姓名、邮箱、公司..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    className="pl-10"
                  />
                </div>
              </div>
              <Select value={status} onChange={(e) => setStatus(e.target.value)}>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(statusLabels).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </Select>
              <Button onClick={handleSearch}>搜索</Button>
            </div>
          </CardContent>
        </Card>

        {/* Leads List */}
        <Card>
          <CardHeader>
            <CardTitle>线索列表 ({leads.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {leads.length === 0 ? (
                <p className="text-gray-500 text-center py-8">没有找到线索</p>
              ) : (
                leads.map((lead) => (
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
                          {lead.email} {lead.phone && `· ${lead.phone}`}
                        </p>
                        <p className="text-sm text-gray-400">
                          {lead.company} {lead.title && `· ${lead.title}`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge
                        variant={
                          lead.status === "closed_lost"
                            ? "destructive"
                            : lead.status === "new"
                            ? "secondary"
                            : "default"
                        }
                      >
                        {statusLabels[lead.status] || lead.status}
                      </Badge>
                      <div className="text-sm">
                        <span className="text-gray-500">AI评分: </span>
                        <span
                          className={`font-semibold ${
                            lead.ai_score >= 80
                              ? "text-green-600"
                              : lead.ai_score >= 50
                              ? "text-yellow-600"
                              : "text-gray-600"
                          }`}
                        >
                          {lead.ai_score}
                        </span>
                      </div>
                      <Link href={`/leads/${lead.id}`}>
                        <Button variant="outline" size="sm">
                          详情
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(lead.id)}
                      >
                        删除
                      </Button>
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
