"""
AI Engine with free tier providers
Supports: Gemini Flash (free), Groq (free), local Ollama
"""
import os
import json
from typing import List, Dict, Optional
import httpx

from app.core.config import settings


class FreeAIEngine:
    """AI Engine optimized for free tiers"""

    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "gemini")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.kimi_key = os.getenv("KIMI_API_KEY")
        self.kimi_model = os.getenv("KIMI_MODEL", "moonshot-v1-8k")  # 可选: kimi-k2-5, moonshot-v1-32k, moonshot-v1-128k

    async def generate_follow_up_message(
        self,
        lead_info: Dict,
        conversation_history: List[Dict],
        playbook_step: Dict,
        tone: str = "professional"
    ) -> str:
        """Generate follow-up using free AI"""

        prompt = f"""你是一个专业的B2B销售顾问。请写一条{tone}风格的跟进消息。

客户信息:
- 姓名: {lead_info.get('name', '')}
- 公司: {lead_info.get('company', '')}
- 职位: {lead_info.get('title', '')}

目标: {playbook_step.get('objective', '建立联系')}

要求:
1. 简短有力，不超过150字
2. 使用中文
3. 关注客户痛点
4. 只有一个明确的行动号召

直接返回消息内容，不要其他解释。"""

        if self.provider == "gemini":
            return await self._call_gemini(prompt)
        elif self.provider == "groq":
            return await self._call_groq(prompt)
        elif self.provider == "kimi":
            return await self._call_kimi(prompt)
        else:
            return await self._call_gemini(prompt)  # fallback

    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini Flash (free 1500 requests/day)"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.gemini_key}"

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 500
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            data = response.json()

            if "candidates" in data:
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            else:
                print(f"Gemini error: {data}")
                return "您好，想了解更多详情，请回复此邮件。"

    async def _call_groq(self, prompt: str) -> str:
        """Call Groq (free 20 requests/min)"""
        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama3-70b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

            if "choices" in data:
                return data["choices"][0]["message"]["content"].strip()
            else:
                print(f"Groq error: {data}")
                return "您好，想了解更多详情，请回复此邮件。"

    async def _call_kimi(self, prompt: str) -> str:
        """Call Kimi/Moonshot AI (支持 K2.5)"""
        from app.core.config import settings
        url = f"{settings.KIMI_API_URL}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.kimi_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.kimi_model,  # 可以是 kimi-k2-5, moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

            if "choices" in data:
                return data["choices"][0]["message"]["content"].strip()
            else:
                print(f"Kimi error: {data}")
                return "您好，想了解更多详情，请回复此邮件。"

    async def analyze_lead_intent(self, message: str) -> Dict:
        """Analyze intent using free AI"""
        prompt = f"""分析这条客户消息，返回JSON格式：

消息: {message}

返回格式:
{{
    "intent": "interested|not_interested|question|objection|meeting_request|other",
    "sentiment": "positive|neutral|negative",
    "urgency": "high|medium|low",
    "key_points": ["要点1", "要点2"]
}}

只返回JSON，不要有其他内容。"""

        try:
            if self.provider == "gemini":
                response = await self._call_gemini(prompt)
            elif self.provider == "kimi":
                response = await self._call_kimi(prompt)
            else:
                response = await self._call_groq(prompt)

            # Parse JSON
            import re
            json_match = re.search(r'\{.*?\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Intent analysis error: {e}")

        return {
            "intent": "unknown",
            "sentiment": "neutral",
            "urgency": "low",
            "key_points": []
        }

    async def score_lead(self, lead_info: Dict) -> int:
        """Score lead using free AI"""
        prompt = f"""评估这个线索的质量，只返回0-100的数字:

线索信息:
- 姓名: {lead_info.get('name', '未知')}
- 公司: {lead_info.get('company', '未知')}
- 职位: {lead_info.get('title', '未知')}
- 来源: {lead_info.get('source', '未知')}

评分标准:
- 80-100: 高管/决策者/大公司
- 50-79: 中层管理/一般公司
- 0-49: 信息不全/小客户

只返回数字，不要有其他内容。"""

        try:
            if self.provider == "gemini":
                response = await self._call_gemini(prompt)
            elif self.provider == "kimi":
                response = await self._call_kimi(prompt)
            else:
                response = await self._call_groq(prompt)

            import re
            match = re.search(r'\d+', response)
            if match:
                score = int(match.group())
                return min(100, max(0, score))
        except Exception as e:
            print(f"Lead scoring error: {e}")

        return 50


# Global instance
free_ai_engine = FreeAIEngine()
