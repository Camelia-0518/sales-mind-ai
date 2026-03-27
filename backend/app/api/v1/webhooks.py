from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime
import hashlib
import hmac

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import Webhook, WebhookDelivery, User, Lead
from app.services.email_service import email_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Schemas
class WebhookCreate(BaseModel):
    name: str
    url: HttpUrl
    events: List[str]
    secret: Optional[str] = None
    is_active: bool = True


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    secret: Optional[str] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: int
    name: str
    url: str
    events: List[str]
    is_active: bool
    created_at: str
    last_triggered: Optional[str]
    delivery_count: int
    success_rate: float

    class Config:
        from_attributes = True


# Supported webhook events
WEBHOOK_EVENTS = {
    "lead.created": "New lead created",
    "lead.updated": "Lead information updated",
    "lead.deleted": "Lead deleted",
    "lead.status_changed": "Lead status changed",
    "lead.imported": "Leads imported in batch",
    "conversation.created": "New conversation/message",
    "playbook.triggered": "Playbook executed",
    "proposal.generated": "Proposal generated",
    "user.updated": "User profile updated",
}


def generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC signature for webhook payload"""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


async def trigger_webhooks(
    event: str,
    payload: Dict[str, Any],
    user_id: int,
    db: Session
):
    """Trigger all webhooks subscribed to an event"""
    webhooks = db.query(Webhook).filter(
        Webhook.user_id == user_id,
        Webhook.is_active == True,
        Webhook.events.contains([event])
    ).all()

    import httpx
    import json

    for webhook in webhooks:
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event=event,
            payload=payload,
            status="pending"
        )
        db.add(delivery)
        db.commit()

        try:
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Event": event,
                "X-Webhook-ID": str(webhook.id),
                "X-Delivery-ID": str(delivery.id),
            }

            # Add signature if secret exists
            if webhook.secret:
                payload_str = json.dumps(payload, sort_keys=True)
                signature = generate_signature(payload_str, webhook.secret)
                headers["X-Webhook-Signature"] = f"sha256={signature}"

            # Send webhook
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    str(webhook.url),
                    json=payload,
                    headers=headers
                )

            # Update delivery status
            delivery.status = "success" if response.status_code < 400 else "failed"
            delivery.http_status = response.status_code
            delivery.response_body = response.text[:1000]  # Limit response size
            webhook.last_triggered = datetime.utcnow()
            webhook.delivery_count += 1

        except Exception as e:
            delivery.status = "failed"
            delivery.response_body = str(e)[:1000]

        finally:
            db.commit()


@router.get("/events")
async def get_available_events(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available webhook events"""
    return {
        "events": [
            {"name": key, "description": value}
            for key, value in WEBHOOK_EVENTS.items()
        ]
    }


@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all webhooks for current user"""
    webhooks = db.query(Webhook).filter(
        Webhook.user_id == current_user.id
    ).order_by(Webhook.created_at.desc()).all()

    # Calculate success rate for each webhook
    result = []
    for webhook in webhooks:
        total_deliveries = db.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook.id
        ).count()

        successful_deliveries = db.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook.id,
            WebhookDelivery.status == "success"
        ).count()

        success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 100

        result.append({
            **webhook.__dict__,
            "delivery_count": total_deliveries,
            "success_rate": round(success_rate, 2)
        })

    return result


@router.post("/", response_model=WebhookResponse)
async def create_webhook(
    webhook: WebhookCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create new webhook"""
    # Validate events
    invalid_events = [e for e in webhook.events if e not in WEBHOOK_EVENTS]
    if invalid_events:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid events: {', '.join(invalid_events)}"
        )

    db_webhook = Webhook(
        user_id=current_user.id,
        name=webhook.name,
        url=str(webhook.url),
        events=webhook.events,
        secret=webhook.secret,
        is_active=webhook.is_active
    )

    db.add(db_webhook)
    db.commit()
    db.refresh(db_webhook)

    return {
        **db_webhook.__dict__,
        "delivery_count": 0,
        "success_rate": 100.0
    }


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get webhook details"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.user_id == current_user.id
    ).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    total_deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook.id
    ).count()

    successful_deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook.id,
        WebhookDelivery.status == "success"
    ).count()

    success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 100

    return {
        **webhook.__dict__,
        "delivery_count": total_deliveries,
        "success_rate": round(success_rate, 2)
    }


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook_update: WebhookUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update webhook"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.user_id == current_user.id
    ).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Validate events if provided
    if webhook_update.events:
        invalid_events = [e for e in webhook_update.events if e not in WEBHOOK_EVENTS]
        if invalid_events:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid events: {', '.join(invalid_events)}"
            )

    update_data = webhook_update.dict(exclude_unset=True)
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])

    for field, value in update_data.items():
        setattr(webhook, field, value)

    db.commit()
    db.refresh(webhook)

    total_deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook.id
    ).count()

    successful_deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook.id,
        WebhookDelivery.status == "success"
    ).count()

    success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 100

    return {
        **webhook.__dict__,
        "delivery_count": total_deliveries,
        "success_rate": round(success_rate, 2)
    }


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete webhook"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.user_id == current_user.id
    ).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    db.delete(webhook)
    db.commit()

    return {"message": "Webhook deleted successfully"}


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send test payload to webhook"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.user_id == current_user.id
    ).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    test_payload = {
        "event": "test",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "message": "This is a test webhook payload",
            "lead_id": 123,
            "lead_name": "Test Lead"
        }
    }

    await trigger_webhooks("test", test_payload, current_user.id, db)

    return {"message": "Test webhook sent", "webhook_id": webhook_id}


@router.get("/{webhook_id}/deliveries")
async def get_webhook_deliveries(
    webhook_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get webhook delivery history"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.user_id == current_user.id
    ).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook_id
    ).order_by(WebhookDelivery.created_at.desc()).limit(limit).all()

    return {
        "webhook_id": webhook_id,
        "deliveries": [
            {
                "id": d.id,
                "event": d.event,
                "status": d.status,
                "http_status": d.http_status,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "response_preview": d.response_body[:200] if d.response_body else None
            }
            for d in deliveries
        ]
    }
