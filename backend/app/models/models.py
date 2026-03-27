from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class LeadSource(str, enum.Enum):
    MANUAL = "manual"
    IMPORT = "import"
    API = "api"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Contact Info
    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(50))
    company = Column(String(255))
    title = Column(String(255))

    # Status & Source
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    source = Column(Enum(LeadSource), default=LeadSource.MANUAL)

    # AI Fields
    ai_score = Column(Integer, default=0)  # 0-100 lead quality score
    last_ai_contact = Column(DateTime(timezone=True))
    ai_notes = Column(Text)

    # Metadata
    tags = Column(String(500))  # comma-separated tags
    custom_fields = Column(Text)  # JSON string

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="leads")
    conversations = relationship("Conversation", back_populates="lead", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255))
    company = Column(String(255))
    avatar = Column(String(500))

    # Subscription
    plan = Column(String(50), default="free")  # free, pro, team
    leads_quota = Column(Integer, default=50)
    leads_used = Column(Integer, default=0)

    # Settings
    timezone = Column(String(50), default="Asia/Shanghai")
    email_signature = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    leads = relationship("Lead", back_populates="user")
    playbooks = relationship("Playbook", back_populates="user")
    webhooks = relationship("Webhook", back_populates="user")


class Playbook(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)

    # Message
    direction = Column(String(20))  # inbound, outbound
    channel = Column(String(50))  # email, wechat, sms
    content = Column(Text, nullable=False)
    ai_generated = Column(Boolean, default=False)

    # AI Analysis
    sentiment = Column(String(20))  # positive, neutral, negative
    intent = Column(String(50))  # question, interested, not_interested, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    lead = relationship("Lead", back_populates="conversations")


class Playbook(Base):
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Config
    name = Column(String(255), nullable=False)
    description = Column(Text)
    trigger_condition = Column(String(50))  # new_lead, no_response_3days, etc.
    is_active = Column(Boolean, default=True)

    # Steps (JSON)
    steps = Column(Text)  # JSON array of steps

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="playbooks")


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    events = Column(Text)  # JSON array of event names
    secret = Column(String(255))  # For HMAC signature
    is_active = Column(Boolean, default=True)

    last_triggered = Column(DateTime(timezone=True))
    delivery_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), nullable=False)

    event = Column(String(100), nullable=False)
    payload = Column(Text)  # JSON payload
    status = Column(String(20))  # pending, success, failed
    http_status = Column(Integer)
    response_body = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    webhook = relationship("Webhook", back_populates="deliveries")
