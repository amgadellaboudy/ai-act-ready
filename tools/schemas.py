from pydantic import BaseModel, Field
from enum import Enum


class RiskTier(str, Enum):
    minimal = "minimal"
    limited = "limited"
    high = "high"
    unacceptable = "unacceptable"


class AuditResult(BaseModel):
    tier: RiskTier = Field(..., description="Risk tier per EU AI Act")
    actions: list[str] = Field(..., max_items=10, description="List of remediation actions")
    model_card_md: str = Field(..., description="Markdown model card")
