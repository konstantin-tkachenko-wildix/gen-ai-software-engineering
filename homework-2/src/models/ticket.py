"""Pydantic models for the support ticket domain."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, ConfigDict


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TicketCategory(str, Enum):
    ACCOUNT_ACCESS = "account_access"
    TECHNICAL_ISSUE = "technical_issue"
    BILLING_QUESTION = "billing_question"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    OTHER = "other"


class TicketPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TicketStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketSource(str, Enum):
    WEB_FORM = "web_form"
    EMAIL = "email"
    API = "api"
    CHAT = "chat"
    PHONE = "phone"


class DeviceType(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"


class TicketMetadata(BaseModel):
    """Free-form context about where/how the ticket was submitted."""

    model_config = ConfigDict(extra="ignore")

    source: TicketSource = TicketSource.API
    browser: Optional[str] = None
    device_type: Optional[DeviceType] = None


class ClassificationResult(BaseModel):
    """Result of an auto-classification run, stored on the ticket for auditing."""

    category: TicketCategory
    priority: TicketPriority
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    keywords_found: List[str] = Field(default_factory=list)
    classified_at: datetime = Field(default_factory=utcnow)
    manually_overridden: bool = False


class TicketBase(BaseModel):
    """Fields shared between create and stored ticket representations."""

    customer_id: str = Field(min_length=1, max_length=100)
    customer_email: EmailStr
    customer_name: str = Field(min_length=1, max_length=200)
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    tags: List[str] = Field(default_factory=list)
    assigned_to: Optional[str] = None
    metadata: TicketMetadata = Field(default_factory=TicketMetadata)


class TicketCreate(TicketBase):
    """Payload accepted by POST /tickets and the bulk import parsers."""

    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    status: TicketStatus = TicketStatus.NEW


class TicketUpdate(BaseModel):
    """Payload accepted by PUT /tickets/{id}. All fields optional (partial update)."""

    customer_id: Optional[str] = Field(default=None, min_length=1, max_length=100)
    customer_email: Optional[EmailStr] = None
    customer_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    subject: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=10, max_length=2000)
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[TicketMetadata] = None
    resolved_at: Optional[datetime] = None


class Ticket(TicketBase):
    """Full ticket representation as stored and returned by the API."""

    id: UUID = Field(default_factory=uuid4)
    category: TicketCategory = TicketCategory.OTHER
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.NEW
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    resolved_at: Optional[datetime] = None
    classification: Optional[ClassificationResult] = None
