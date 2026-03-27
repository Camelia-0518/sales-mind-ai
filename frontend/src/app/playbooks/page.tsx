"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Play, Edit, Trash2, Sparkles, LogOut } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";

interface Playbook {
  id: number;
  name: string;
  description: string;
  trigger_condition: string;
  is_active: boolean;
  steps: any[];
  created_at: string;
}

const triggerLabels: Record<string, string> = {
  new_lead: "新线索",
  no_response_3days: "3天未回复",
  no_response_7days: "7天未回复",
  proposal_sent: "发送提案后",
  demo_requested: "请求演示后",
};

export default function PlaybooksPage() {
  const { token, logout } = useAuth();
  const router = useRouter();
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [templates, setTemplates] = useState<Record<string, any>>({});

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }
    loadData();
  }, [token, router]);

  const loadData = async () => {
    try {
      const [playbooksRes, templatesRes] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/playbooks/`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/playbooks/templates`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (playbooksRes.ok) setPlaybooks(await playbooksRes.json());
      if (templatesRes.ok) setTemplates(await templatesRes.json());
    } catch (error) {
      console.error("Failed to load playbooks:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const handleDelete = async (id: number) => {
    if (!confirm("确定要删除这个剧本吗？")) return;
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/playbooks/${id}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      loadData();
    } catch (error) {
      alert("删除失败");
    }
  };

  const createFromTemplate = async (templateId: string) => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/playbooks/from-template/${templateId}`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (res.ok) {
        loadData();
      }
    } catch (error) {
      alert("创建失败");
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
          <div>
            <h1 className="text-2xl font-bold">AI跟进剧本</h1>
            <p className="text-gray-500">配置自动化的客户跟进流程</p>
          </div>
          <Link href="/playbooks/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              创建剧本
            </Button>
          </Link>
        </div>

        {/* Templates */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>快速开始模板</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(templates).map(([id, template]: [string, any]) => (
                <div
                  key={id}
                  className="border rounded-lg p-4 hover:border-blue-500 cursor-pointer transition-colors"
                  onClick={() => createFromTemplate(id)}
                >
                  <h3 className="font-medium mb-1">{template.name}</h3>
                  <p className="text-sm text-gray-500">{template.description}</p>
                  <div className="mt-2 text-xs text-blue-600">
                    点击使用此模板
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Playbooks List */}
        <Card>
          <CardHeader>
            <CardTitle>我的剧本 ({playbooks.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {playbooks.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  还没有创建剧本，点击上方按钮开始创建或使用模板
                </p>
              ) : (
                playbooks.map((playbook) => (
                  <div
                    key={playbook.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium">{playbook.name}</h3>
                        <Badge
                          variant={playbook.is_active ? "default" : "secondary"}
                        >
                          {playbook.is_active ? "启用" : "禁用"}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-500">
                        {playbook.description}
                      </p>
                      <div className="flex gap-2 mt-2">
                        <Badge variant="outline">
                          {triggerLabels[playbook.trigger_condition] ||
                            playbook.trigger_condition}
                        </Badge>
                        <span className="text-sm text-gray-400">
                          {playbook.steps?.length || 0} 个步骤
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <Play className="h-4 w-4 mr-1" />
                        预览
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(playbook.id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
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
