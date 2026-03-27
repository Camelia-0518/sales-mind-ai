from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import Playbook, User, Lead
from app.services.ai_engine import ai_engine

router = APIRouter(prefix="/playbooks", tags=["playbooks"])


# Schemas
class PlaybookStep(BaseModel):
    order: int
    delay_days: int  # Days to wait before this step
    channel: str  # email, sms, call
    tone: str  # professional, friendly, urgent
    objective: str
    template: Optional[str] = None


class PlaybookCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_condition: str  # new_lead, no_response_3days, no_response_7days, etc.
    is_active: bool = True
    steps: List[PlaybookStep]


class PlaybookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_condition: Optional[str] = None
    is_active: Optional[bool] = None
    steps: Optional[List[PlaybookStep]] = None


class PlaybookResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    trigger_condition: str
    is_active: bool
    steps: List[PlaybookStep]
    created_at: str
    updated_at: Optional[str]
    execution_count: int = 0
    conversion_rate: float = 0.0

    class Config:
        from_attributes = True


# Pre-built playbook templates
PLAYBOOK_TEMPLATES = {
    "new_lead_nurture": {
        "name": "新线索培养",
        "description": "针对新线索的7天培养流程",
        "trigger_condition": "new_lead",
        "steps": [
            {
                "order": 1,
                "delay_days": 0,
                "channel": "email",
                "tone": "friendly",
                "objective": "建立联系，介绍价值主张",
                "template": "您好{{name}}，感谢您对{{company}}的关注。我是{{sender_name}}，想了解一下您目前的{{pain_point}}挑战..."
            },
            {
                "order": 2,
                "delay_days": 2,
                "channel": "email",
                "tone": "professional",
                "objective": "分享案例研究",
                "template": "{{name}}您好，想和您分享一个类似{{industry}}客户如何使用我们的方案提升{{metric}}30%的案例..."
            },
            {
                "order": 3,
                "delay_days": 5,
                "channel": "email",
                "tone": "urgent",
                "objective": "制造紧迫感，推动行动",
                "template": "{{name}}，很多{{industry}}公司已经开始使用AI工具提升效率。不知道您这边是否有15分钟聊聊？"
            }
        ]
    },
    "silent_reactivation": {
        "name": "沉默客户激活",
        "description": "重新激活7天未回复的客户",
        "trigger_condition": "no_response_7days",
        "steps": [
            {
                "order": 1,
                "delay_days": 0,
                "channel": "email",
                "tone": "friendly",
                "objective": "温和提醒，重新建立联系",
                "template": "{{name}}您好，之前发的邮件可能没看到。这里简单总结一下我们能帮您的3个点：1)... 2)... 3)..."
            },
            {
                "order": 2,
                "delay_days": 3,
                "channel": "email",
                "tone": "professional",
                "objective": "提供价值，降低门槛",
                "template": "{{name}}，我整理了一份{{industry}}行业{{topic}}报告，也许对您有参考价值。附件发送给您。"
            }
        ]
    },
    "post_proposal_followup": {
        "name": "提案后跟进",
        "description": "发送提案后的跟进流程",
        "trigger_condition": "proposal_sent",
        "steps": [
            {
                "order": 1,
                "delay_days": 2,
                "channel": "email",
                "tone": "professional",
                "objective": "确认收到，询问反馈",
                "template": "{{name}}，想确认一下您收到上周发送的提案了吗？有任何问题我可以解答。"
            },
            {
                "order": 2,
                "delay_days": 5,
                "channel": "email",
                "tone": "urgent",
                "objective": "推动决策",
                "template": "{{name}}，这个方案帮您解决了{{pain_point}}问题。如果您这周确认，我们可以优先安排实施。"
            },
            {
                "order": 3,
                "delay_days": 7,
                "channel": "email",
                "tone": "friendly",
                "objective": "最后尝试，保持关系",
                "template": "{{name}}，理解您可能需要更多时间考虑。无论如何，希望保持联系。如果以后有需要随时找我。"
            }
        ]
    },
    "demo_request": {
        "name": "演示请求跟进",
        "description": "请求演示后的跟进流程",
        "trigger_condition": "demo_requested",
        "steps": [
            {
                "order": 1,
                "delay_days": 0,
                "channel": "email",
                "tone": "friendly",
                "objective": "确认演示时间",
                "template": "{{name}}，感谢您申请演示！为了给您最佳体验，请告诉我您最关注哪些功能？"
            },
            {
                "order": 2,
                "delay_days": 1,
                "channel": "email",
                "tone": "professional",
                "objective": "发送日历邀请",
                "template": "{{name}}，演示时间已确认。这是会议链接：{{meeting_link}}。建议提前5分钟进入测试设备。"
            },
            {
                "order": 3,
                "delay_days": 0,
                "channel": "email",
                "tone": "friendly",
                "objective": "演示后跟进",
                "template": "{{name}}，感谢您的宝贵时间。根据刚才的交流，我整理了个性化方案供您参考。"
            }
        ]
    }
}


@router.get("/templates")
async def get_playbook_templates(
    current_user: User = Depends(get_current_active_user)
):
    """Get pre-built playbook templates"""
    return PLAYBOOK_TEMPLATES


@router.post("/from-template/{template_id}")
async def create_from_template(
    template_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create playbook from template"""
    if template_id not in PLAYBOOK_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    template = PLAYBOOK_TEMPLATES[template_id]

    playbook = Playbook(
        user_id=current_user.id,
        name=template["name"],
        description=template["description"],
        trigger_condition=template["trigger_condition"],
        is_active=True,
        steps=template["steps"]
    )

    db.add(playbook)
    db.commit()
    db.refresh(playbook)

    return playbook


@router.get("/", response_model=List[PlaybookResponse])
async def list_playbooks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all playbooks for current user"""
    playbooks = db.query(Playbook).filter(
        Playbook.user_id == current_user.id
    ).order_by(Playbook.created_at.desc()).all()

    return playbooks


@router.post("/", response_model=PlaybookResponse, status_code=status.HTTP_201_CREATED)
async def create_playbook(
    playbook: PlaybookCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create new playbook"""
    db_playbook = Playbook(
        user_id=current_user.id,
        name=playbook.name,
        description=playbook.description,
        trigger_condition=playbook.trigger_condition,
        is_active=playbook.is_active,
        steps=[step.dict() for step in playbook.steps]
    )

    db.add(db_playbook)
    db.commit()
    db.refresh(db_playbook)

    return db_playbook


@router.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(
    playbook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get playbook details"""
    playbook = db.query(Playbook).filter(
        Playbook.id == playbook_id,
        Playbook.user_id == current_user.id
    ).first()

    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    return playbook


@router.put("/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook(
    playbook_id: int,
    playbook_update: PlaybookUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update playbook"""
    playbook = db.query(Playbook).filter(
        Playbook.id == playbook_id,
        Playbook.user_id == current_user.id
    ).first()

    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    update_data = playbook_update.dict(exclude_unset=True)

    if "steps" in update_data:
        update_data["steps"] = [step.dict() for step in playbook_update.steps]

    for field, value in update_data.items():
        setattr(playbook, field, value)

    db.commit()
    db.refresh(playbook)

    return playbook


@router.delete("/{playbook_id}")
async def delete_playbook(
    playbook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete playbook"""
    playbook = db.query(Playbook).filter(
        Playbook.id == playbook_id,
        Playbook.user_id == current_user.id
    ).first()

    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    db.delete(playbook)
    db.commit()

    return {"message": "Playbook deleted successfully"}


@router.post("/{playbook_id}/preview")
async def preview_playbook(
    playbook_id: int,
    lead_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Preview playbook messages for a specific lead"""
    playbook = db.query(Playbook).filter(
        Playbook.id == playbook_id,
        Playbook.user_id == current_user.id
    ).first()

    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Generate preview messages for each step
    previews = []
    for step in playbook.steps:
        message = await ai_engine.generate_follow_up_message(
            lead_info={
                "name": lead.name,
                "company": lead.company,
                "title": lead.title
            },
            conversation_history=[],
            playbook_step={
                "objective": step["objective"],
                "tone": step["tone"]
            }
        )

        previews.append({
            "step_order": step["order"],
            "delay_days": step["delay_days"],
            "channel": step["channel"],
            "tone": step["tone"],
            "objective": step["objective"],
            "generated_message": message
        })

    return {
        "playbook_id": playbook_id,
        "playbook_name": playbook.name,
        "lead_name": lead.name,
        "previews": previews
    }


@router.get("/{playbook_id}/stats")
async def get_playbook_stats(
    playbook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get playbook execution statistics"""
    playbook = db.query(Playbook).filter(
        Playbook.id == playbook_id,
        Playbook.user_id == current_user.id
    ).first()

    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    # TODO: Implement actual statistics calculation
    # This is placeholder data
    return {
        "playbook_id": playbook_id,
        "total_executions": 156,
        "active_leads": 23,
        "completed_leads": 89,
        "converted_leads": 12,
        "conversion_rate": 13.5,
        "average_response_time": "2.3 days",
        "step_completion_rates": {
            "step_1": 100,
            "step_2": 67,
            "step_3": 34
        }
    }
