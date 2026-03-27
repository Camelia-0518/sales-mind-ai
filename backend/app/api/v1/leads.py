import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from io import BytesIO

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import Lead, LeadStatus, LeadSource, User
from app.services.ai_engine import ai_engine

router = APIRouter(prefix="/leads", tags=["leads"])


# Schemas
class LeadCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    tags: Optional[str] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    status: Optional[LeadStatus] = None
    tags: Optional[str] = None


class LeadResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    title: Optional[str]
    status: LeadStatus
    ai_score: int
    source: LeadSource
    tags: Optional[str]
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class ImportResponse(BaseModel):
    success: int
    failed: int
    errors: List[str]


# Routes
@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[LeadStatus] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取线索列表"""
    query = db.query(Lead).filter(Lead.user_id == current_user.id)

    if status:
        query = query.filter(Lead.status == status)

    if search:
        query = query.filter(
            (Lead.name.ilike(f"%{search}%")) |
            (Lead.email.ilike(f"%{search}%")) |
            (Lead.company.ilike(f"%{search}%"))
        )

    leads = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()
    return leads


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead: LeadCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新线索"""
    # Check quota
    if current_user.leads_used >= current_user.leads_quota:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lead quota exceeded. Please upgrade your plan."
        )

    db_lead = Lead(
        user_id=current_user.id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        company=lead.company,
        title=lead.title,
        tags=lead.tags,
        source=LeadSource.MANUAL
    )

    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)

    # Update quota
    current_user.leads_used += 1
    db.commit()

    # AI评分异步进行
    try:
        score = await ai_engine.score_lead({
            "name": lead.name,
            "company": lead.company,
            "title": lead.title,
            "source": "manual"
        })
        db_lead.ai_score = score
        db.commit()
    except Exception as e:
        print(f"AI scoring failed: {e}")

    return db_lead


@router.post("/import", response_model=ImportResponse)
async def import_leads(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """批量导入线索 (Excel/CSV)"""
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel (.xlsx, .xls) and CSV files are supported"
        )

    try:
        contents = await file.read()

        if file.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(contents))
        else:
            df = pd.read_excel(BytesIO(contents))

        # Validate required columns
        if 'name' not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must contain 'name' column"
            )

        success = 0
        failed = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                if current_user.leads_used >= current_user.leads_quota:
                    errors.append(f"Row {idx + 2}: Quota exceeded")
                    failed += 1
                    continue

                db_lead = Lead(
                    user_id=current_user.id,
                    name=str(row.get('name', '')),
                    email=str(row.get('email', '')) if pd.notna(row.get('email')) else None,
                    phone=str(row.get('phone', '')) if pd.notna(row.get('phone')) else None,
                    company=str(row.get('company', '')) if pd.notna(row.get('company')) else None,
                    title=str(row.get('title', '')) if pd.notna(row.get('title')) else None,
                    source=LeadSource.IMPORT
                )

                db.add(db_lead)
                current_user.leads_used += 1
                success += 1

            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
                failed += 1

        db.commit()

        return ImportResponse(success=success, failed=failed, errors=errors)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取单个线索详情"""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_update: LeadUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新线索"""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    for field, value in lead_update.dict(exclude_unset=True).items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除线索"""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    db.delete(lead)
    current_user.leads_used = max(0, current_user.leads_used - 1)
    db.commit()

    return {"message": "Lead deleted successfully"}


@router.post("/{lead_id}/ai-follow-up")
async def ai_follow_up(
    lead_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """触发AI跟进"""
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Get conversation history
    conversations = lead.conversations[-5:] if lead.conversations else []
    history = [{"content": c.content, "ai_generated": c.ai_generated} for c in conversations]

    # Generate follow-up message
    message = await ai_engine.generate_follow_up_message(
        lead_info={
            "name": lead.name,
            "company": lead.company,
            "title": lead.title
        },
        conversation_history=history,
        playbook_step={"objective": "重新激活沉默客户"}
    )

    return {
        "lead_id": lead_id,
        "generated_message": message,
        "channel": "email"
    }


@router.get("/stats/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取仪表盘统计数据"""
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # Total leads
    total_leads = db.query(Lead).filter(Lead.user_id == current_user.id).count()

    # Status distribution
    status_counts = db.query(
        Lead.status,
        func.count(Lead.id)
    ).filter(Lead.user_id == current_user.id).group_by(Lead.status).all()

    status_dict = {status.value: count for status, count in status_counts}

    # Recent leads (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_leads = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.created_at >= week_ago
    ).order_by(Lead.created_at.desc()).limit(5).all()

    # Average AI score
    avg_score = db.query(func.avg(Lead.ai_score)).filter(
        Lead.user_id == current_user.id
    ).scalar() or 0

    return {
        "total_leads": total_leads,
        "quota": {
            "used": current_user.leads_used,
            "total": current_user.leads_quota
        },
        "status_distribution": status_dict,
        "average_ai_score": round(float(avg_score), 1),
        "recent_leads": recent_leads,
        "plan": current_user.plan
    }
