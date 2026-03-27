"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Plus, Trash2, Play, Copy, Sparkles } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";

interface PlaybookStep {
  order: number;
  delay_days: number;
  channel: string;
  tone: string;
  objective: string;
  template: string;
}

export default function NewPlaybookPage() {
  const { token } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    trigger_condition: "new_lead",
    is_active: true,
    steps: [
      {
        order: 1,
        delay_days: 0,
        channel: "email",
        tone: "professional",
        objective: "建立初次联系",
        template: "",
      },
    ] as PlaybookStep[],
  });

  const addStep = () => {
    setFormData({
      ...formData,
      steps: [
        ...formData.steps,
        {
          order: formData.steps.length + 1,
          delay_days: formData.steps[formData.steps.length - 1]?.delay_days + 2 || 2,
          channel: "email",
          tone: "professional",
          objective: "",
          template: "",
        },
      ],
    });
  };

  const removeStep = (index: number) => {
    const newSteps = formData.steps.filter((_, i) => i !== index);
    setFormData({
      ...formData,
      steps: newSteps.map((step, i) => ({ ...step, order: i + 1 })),
    });
  };

  const updateStep = (index: number, field: keyof PlaybookStep, value: any) => {
    const newSteps = [...formData.steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setFormData({ ...formData, steps: newSteps });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/playbooks/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!res.ok) throw new Error("创建失败");
      router.push("/playbooks");
    } catch (err: any) {
      setError(err.message || "创建失败");
    } finally {
      setIsLoading(false);
    }
  };

  const tones = [
    { value: "professional", label: "专业正式" },
    { value: "friendly", label: "友好亲和" },
    { value: "urgent", label: "紧迫促单" },
    { value: "casual", label: "轻松随意" },
  ];

  const channels = [
    { value: "email", label: "邮件" },
    { value: "sms", label: "短信" },
    { value: "wechat", label: "微信" },
  ];

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
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <Link href="/playbooks">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              返回剧本列表
            </Button>
          </Link>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>创建AI跟进剧本</CardTitle>
            <CardDescription>
              配置自动化的客户跟进流程，AI将根据步骤自动生成消息
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-6">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Info */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">剧本名称</Label>
                  <Input
                    id="name"
                    placeholder="例如：新线索7天培养计划"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">描述</Label>
                  <Textarea
                    id="description"
                    placeholder="简要描述这个剧本的用途和目标..."
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                    rows={2}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="trigger">触发条件</Label>
                  <select
                    id="trigger"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={formData.trigger_condition}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        trigger_condition: e.target.value,
                      })
                    }
                  >
                    <option value="new_lead">新线索创建时</option>
                    <option value="no_response_3days">3天未回复</option>
                    <option value="no_response_7days">7天未回复</option>
                    <option value="proposal_sent">发送提案后</option>
                    <option value="demo_requested">请求演示后</option>
                  </select>
                </div>
              </div>

              {/* Steps */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <Label>跟进步骤</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addStep}>
                    <Plus className="h-4 w-4 mr-2" />
                    添加步骤
                  </Button>
                </div>

                {formData.steps.map((step, index) => (
                  <Card key={index} className="bg-gray-50">
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-start mb-4">
                        <Badge variant="secondary">步骤 {step.order}</Badge>
                        {formData.steps.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeStep(index)}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        )}
                      </div>

                      <div className="grid grid-cols-3 gap-4 mb-4">
                        <div className="space-y-2">
                          <Label>等待天数</Label>
                          <Input
                            type="number"
                            min={0}
                            value={step.delay_days}
                            onChange={(e) =>
                              updateStep(index, "delay_days", parseInt(e.target.value))
                            }
                          />
                          <p className="text-xs text-gray-500">
                            相对于上一步
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label>渠道</Label>
                          <select
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            value={step.channel}
                            onChange={(e) =>
                              updateStep(index, "channel", e.target.value)
                            }
                          >
                            {channels.map((c) => (
                              <option key={c.value} value={c.value}>
                                {c.label}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div className="space-y-2">
                          <Label>语气</Label>
                          <select
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            value={step.tone}
                            onChange={(e) =>
                              updateStep(index, "tone", e.target.value)
                            }
                          >
                            {tones.map((t) => (
                              <option key={t.value} value={t.value}>
                                {t.label}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <div className="space-y-2 mb-4">
                        <Label>目标/主题</Label>
                        <Input
                          placeholder="例如：介绍产品价值主张"
                          value={step.objective}
                          onChange={(e) =>
                            updateStep(index, "objective", e.target.value)
                          }
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>消息模板（可选）</Label>
                        <Textarea
                          placeholder="留空让AI自动生成，或输入模板引导AI... 可用变量：{{name}}, {{company}}, {{title}}"
                          value={step.template}
                          onChange={(e) =>
                            updateStep(index, "template", e.target.value)
                          }
                          rows={3}
                        />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="flex justify-end gap-4">
                <Link href="/playbooks">
                  <Button variant="outline" type="button">
                    取消
                  </Button>
                </Link>
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? "创建中..." : "创建剧本"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
