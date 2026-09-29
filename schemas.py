from typing import Any, Optional, Literal
from pydantic import BaseModel, Field

class TenderCreate(BaseModel):
    tender_number: str
    title: str
    description: Optional[str] = None
    requirements: dict[str, Any] = Field(default_factory=dict)
    status: str = "draft"
    created_by: Optional[str] = None

class BidCreate(BaseModel):
    bidder_id: str
    tender_id: Optional[str] = None
    tender_number: Optional[str] = None
    tender_title: Optional[str] = None
    status: str = "submitted"

class DecisionRequest(BaseModel):
    decision: Literal["QUALIFIED", "DISQUALIFIED", "SEEK_CLARIFICATION"]
    remarks: Optional[str] = None
    officer_id: Optional[str] = None

class ComplianceEvaluateRequest(BaseModel):
    bid_id: str
    rules: Optional[dict[str, Any]] = None

class ExtractRequest(BaseModel):
    document_id: Optional[str] = None
    document_type: Literal["PAN", "GST", "UDYAM"]
    ocr_text: str

class AuditCreate(BaseModel):
    bid_id: Optional[str] = None
    actor_id: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    details: dict[str, Any] = Field(default_factory=dict)
