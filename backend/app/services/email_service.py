"""
Email service for sending notifications and AI-generated messages
"""
import os
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from jinja2 import Template

from app.core.config import settings


class EmailService:
    """Email service for sending notifications and follow-ups"""

    def __init__(self):
        self.sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@salesmind.ai')
        self.enabled = bool(os.getenv('SENDGRID_API_KEY'))

    async def send_follow_up(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        content: str,
        sender_name: Optional[str] = None
    ) -> bool:
        """Send AI-generated follow-up email"""
        if not self.enabled:
            print(f"[EMAIL MOCK] To: {to_email}, Subject: {subject}")
            return True

        try:
            # HTML template for follow-up emails
            html_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { border-bottom: 2px solid #0066cc; padding-bottom: 10px; margin-bottom: 20px; }
        .content { margin: 20px 0; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }
        .signature { margin-top: 20px; font-style: italic; color: #666; }
    </style>
</head>
<body>
    <div class="content">
        {{ content | safe }}
    </div>
    {% if sender_name %}
    <div class="signature">
        <p>— {{ sender_name }}</p>
    </div>
    {% endif %}
    <div class="footer">
        <p>此邮件由 SalesMind AI 智能生成</p>
        <p><a href="{{ unsubscribe_url }}">取消订阅</a></p>
    </div>
</body>
</html>
            """)

            html_content = html_template.render(
                content=content.replace('\n', '<br>'),
                sender_name=sender_name,
                unsubscribe_url=f"https://salesmind.ai/unsubscribe?email={to_email}"
            )

            message = Mail(
                from_email=Email(self.from_email, sender_name or "SalesMind AI"),
                to_emails=To(to_email, to_name),
                subject=subject,
                html_content=html_content
            )

            response = self.sg.send(message)
            return response.status_code in [200, 201, 202]

        except Exception as e:
            print(f"Email send failed: {e}")
            return False

    async def send_proposal(
        self,
        to_email: str,
        to_name: str,
        proposal_title: str,
        proposal_content: str,
        sender_name: Optional[str] = None
    ) -> bool:
        """Send proposal via email"""
        if not self.enabled:
            print(f"[PROPOSAL MOCK] To: {to_email}, Title: {proposal_title}")
            return True

        try:
            html_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; padding: 20px; }
        .proposal-header { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .proposal-title { font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 10px; }
        .proposal-content { white-space: pre-wrap; }
        .cta-button { display: inline-block; background: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="proposal-header">
        <div class="proposal-title">{{ title }}</div>
        <p>尊敬的客户，您好！</p>
    </div>
    <div class="proposal-content">
        {{ content | safe }}
    </div>
    <div style="text-align: center; margin-top: 30px;">
        <a href="{{ meeting_url }}" class="cta-button">预约会议讨论</a>
    </div>
</body>
</html>
            """)

            html_content = html_template.render(
                title=proposal_title,
                content=proposal_content.replace('\n', '<br>'),
                meeting_url="https://calendly.com/salesmind"
            )

            message = Mail(
                from_email=Email(self.from_email, sender_name or "SalesMind AI"),
                to_emails=To(to_email, to_name),
                subject=f"【提案】{proposal_title}",
                html_content=html_content
            )

            response = self.sg.send(message)
            return response.status_code in [200, 201, 202]

        except Exception as e:
            print(f"Proposal email failed: {e}")
            return False

    async def send_notification(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        template_data: dict
    ) -> bool:
        """Send notification email using template"""
        templates = {
            'welcome': self._welcome_template(),
            'daily_summary': self._daily_summary_template(),
            'lead_alert': self._lead_alert_template(),
        }

        if template_name not in templates:
            return False

        try:
            template = Template(templates[template_name])
            html_content = template.render(**template_data)

            message = Mail(
                from_email=Email(self.from_email, "SalesMind AI"),
                to_emails=To(to_email),
                subject=subject,
                html_content=html_content
            )

            response = self.sg.send(message)
            return response.status_code in [200, 201, 202]

        except Exception as e:
            print(f"Notification failed: {e}")
            return False

    def _welcome_template(self):
        return """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #0066cc;">欢迎使用 SalesMind AI！</h2>
    <p>您好 {{ name }}，</p>
    <p>感谢您注册 SalesMind AI。您现在可以：</p>
    <ul>
        <li>导入您的第一批线索</li>
        <li>配置AI跟进剧本</li>
        <li>让AI开始自动跟进</li>
    </ul>
    <a href="{{ dashboard_url }}" style="display: inline-block; background: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">进入仪表盘</a>
</body>
</html>
        """

    def _daily_summary_template(self):
        return """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #0066cc;">您的每日销售摘要</h2>
    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <p><strong>今日新增线索：</strong> {{ new_leads }}</p>
        <p><strong>AI跟进次数：</strong> {{ ai_followups }}</p>
        <p><strong>客户回复：</strong> {{ responses }}</p>
    </div>
    <a href="{{ dashboard_url }}" style="display: inline-block; background: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">查看详情</a>
</body>
</html>
        """

    def _lead_alert_template(self):
        return """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #0066cc;">🎯 高意向客户提醒</h2>
    <p>AI 检测到一位高价值客户需要您立即关注：</p>
    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <p><strong>姓名：</strong> {{ lead_name }}</p>
        <p><strong>公司：</strong> {{ lead_company }}</p>
        <p><strong>AI评分：</strong> {{ ai_score }}/100</p>
        <p><strong>最新动态：</strong> {{ latest_activity }}</p>
    </div>
    <a href="{{ lead_url }}" style="display: inline-block; background: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">立即跟进</a>
</body>
</html>
        """


# Global instance
email_service = EmailService()
