import openai
import anthropic
from typing import List, Dict, Optional, AsyncGenerator
import json
import os

from app.core.config import settings


class AIEngine:
    """AI引擎 - 处理所有智能生成任务"""

    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        )
        self.anthropic_client = anthropic.AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")
        )

    async def generate_follow_up_message(
        self,
        lead_info: Dict,
        conversation_history: List[Dict],
        playbook_step: Dict,
        tone: str = "professional"
    ) -> str:
        """生成跟进消息"""

        system_prompt = f"""你是一个专业的B2B销售顾问。你的任务是与潜在客户进行自然、专业的沟通。

沟通风格: {tone}
关键原则:
1. 简短有力，不超过150字
2. 关注客户痛点，而非产品功能
3. 每封邮件只问一个明确的问题
4. 使用中文，礼貌但有紧迫感

当前跟进目标: {playbook_step.get('objective', '了解客户需求')}
"""

        messages = [{"role": "system", "content": system_prompt}]

        # 添加客户信息
        context = f"""
客户: {lead_info.get('name', '')}
公司: {lead_info.get('company', '')}
职位: {lead_info.get('title', '')}
"""
        messages.append({"role": "user", "content": f"客户信息:\n{context}\n\n请生成一条跟进消息。"})

        # 添加对话历史
        for msg in conversation_history[-5:]:  # 只取最近5条
            role = "assistant" if msg.get('ai_generated') else "user"
            messages.append({
                "role": role,
                "content": msg.get('content', '')
            })

        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=messages
            )
            return response.content[0].text.strip()
        except Exception as e:
            print(f"Claude API error: {e}")
            # Fallback to OpenAI
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()

    async def analyze_lead_intent(self, message: str) -> Dict:
        """分析客户意图"""

        prompt = f"""分析以下客户消息，判断其意图和情绪:

消息内容: {message}

请以JSON格式返回:
{{
    "intent": "interested|not_interested|question|objection|meeting_request|other",
    "sentiment": "positive|neutral|negative",
    "key_points": ["要点1", "要点2"],
    "recommended_action": "继续跟进|安排会议|发送资料|暂时搁置"
}}
"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Intent analysis error: {e}")
            return {
                "intent": "unknown",
                "sentiment": "neutral",
                "key_points": [],
                "recommended_action": "继续跟进"
            }

    async def generate_proposal(
        self,
        lead_info: Dict,
        requirements: str,
        product_catalog: List[Dict]
    ) -> Dict:
        """生成销售提案"""

        products_str = "\n".join([
            f"- {p['name']}: {p['description']} (¥{p['price']})"
            for p in product_catalog
        ])

        prompt = f"""基于以下信息生成一份专业的销售提案:

客户: {lead_info.get('name', '')}
公司: {lead_info.get('company', '')}
职位: {lead_info.get('title', '')}
需求: {requirements}

可选产品:
{products_str}

请生成包含以下内容的提案:
1. 标题
2. 客户痛点分析
3. 解决方案概述
4. 产品推荐及定价
5. 下一步行动建议
"""

        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.content[0].text

            return {
                "title": f"{lead_info.get('company', '贵公司')} - 解决方案提案",
                "content": content,
                "generated_at": "now"
            }
        except Exception as e:
            print(f"Proposal generation error: {e}")
            return {
                "title": "解决方案提案",
                "content": "生成失败，请稍后重试",
                "error": str(e)
            }

    async def score_lead(self, lead_info: Dict) -> int:
        """为线索评分 0-100"""

        prompt = f"""根据以下客户信息，评估其成交潜力(0-100分):

姓名: {lead_info.get('name', '未知')}
公司: {lead_info.get('company', '未知')}
职位: {lead_info.get('title', '未知')}
来源: {lead_info.get('source', '未知')}

评分标准:
- 80-100: 高意向，决策人，预算充足
- 50-79: 中等意向，需要培养
- 0-49: 低意向或信息不足

只返回数字分数。"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10
            )
            score_text = response.choices[0].message.content.strip()
            # Extract number
            import re
            match = re.search(r'\d+', score_text)
            if match:
                return min(100, max(0, int(match.group())))
            return 50
        except Exception as e:
            print(f"Lead scoring error: {e}")
            return 50


# Global instance
ai_engine = AIEngine()
