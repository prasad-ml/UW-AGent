"""
Data models for credit card application and underwriting decisions.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level classifications."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DecisionStatus(str, Enum):
    """Underwriting decision statuses."""
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    PENDING_REVIEW = "PENDING_REVIEW"


class FindingStatus(str, Enum):
    """Agent finding statuses."""
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"


class CreditApplication(BaseModel):
    """Credit card application model."""
    
    application_id: str = Field(..., description="Unique application identifier")
    customer_name: str = Field(..., description="Customer full name")
    ssn: str = Field(..., description="Social Security Number")
    annual_income: float = Field(..., description="Annual income in USD", gt=0)
    credit_score: int = Field(..., description="Credit score", ge=300, le=850)
    dti_ratio: Optional[float] = Field(None, description="Debt-to-Income ratio", ge=0, le=1)
    review_rules: List[str] = Field(..., description="List of review rules to apply")
    
    # Additional optional fields
    address: Optional[str] = Field(None, description="Customer address")
    employment_status: Optional[str] = Field(None, description="Employment status")
    requested_credit_limit: Optional[float] = Field(None, description="Requested credit limit")
    existing_debt: Optional[float] = Field(None, description="Existing debt amount")
    
    # Metadata
    submitted_at: datetime = Field(default_factory=datetime.now, description="Application submission timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "application_id": "APP-12345",
                "customer_name": "John Doe",
                "ssn": "123-45-6789",
                "annual_income": 75000.0,
                "credit_score": 720,
                "dti_ratio": 0.35,
                "review_rules": ["INCOME_VALIDATION", "FRAUD_CHECK"],
                "address": "123 Main St, New York, NY 10001",
                "employment_status": "EMPLOYED",
                "requested_credit_limit": 10000.0,
                "existing_debt": 15000.0
            }
        }


class AgentFinding(BaseModel):
    """Findings from an individual agent."""
    
    agent_name: str = Field(..., description="Name of the agent that produced this finding")
    check_type: str = Field(..., description="Type of check performed")
    status: FindingStatus = Field(..., description="Status of the finding")
    details: Dict = Field(default_factory=dict, description="Detailed findings")
    risk_level: RiskLevel = Field(..., description="Risk level assessment")
    confidence: float = Field(..., description="Confidence score", ge=0, le=1)
    reasoning: str = Field(..., description="Explanation for the finding")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the finding was created")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "IdentityAgent",
                "check_type": "IDENTITY_VERIFICATION",
                "status": "PASS",
                "details": {
                    "ssn_valid": True,
                    "identity_theft_flags": 0,
                    "address_verified": True
                },
                "risk_level": "LOW",
                "confidence": 0.92,
                "reasoning": "All identity checks passed with high confidence",
                "timestamp": "2026-01-28T10:30:00"
            }
        }


class UnderwritingDecision(BaseModel):
    """Final underwriting decision for an application."""
    
    application_id: str = Field(..., description="Application identifier")
    decision: DecisionStatus = Field(..., description="Final decision")
    confidence_score: float = Field(..., description="Confidence in the decision", ge=0, le=1)
    findings: List[AgentFinding] = Field(default_factory=list, description="All agent findings")
    reasoning: str = Field(..., description="Explanation for the decision")
    timestamp: datetime = Field(default_factory=datetime.now, description="Decision timestamp")
    
    # Additional metadata
    processing_time_seconds: Optional[float] = Field(None, description="Time taken to process")
    rules_applied: List[str] = Field(default_factory=list, description="Review rules that were applied")
    requires_manual_review: bool = Field(False, description="Whether manual review is needed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "application_id": "APP-12345",
                "decision": "APPROVED",
                "confidence_score": 0.92,
                "findings": [],
                "reasoning": "All required checks passed with high confidence. Income verified, DTI within acceptable limits, and no fraud indicators detected.",
                "timestamp": "2026-01-28T10:35:00",
                "processing_time_seconds": 2.5,
                "rules_applied": ["INCOME_VALIDATION", "FRAUD_CHECK"],
                "requires_manual_review": False
            }
        }
    
    def add_finding(self, finding: AgentFinding) -> None:
        """Add an agent finding to the decision."""
        self.findings.append(finding)
    
    def get_findings_by_status(self, status: FindingStatus) -> List[AgentFinding]:
        """Get all findings with a specific status."""
        return [f for f in self.findings if f.status == status]
    
    def has_critical_failures(self) -> bool:
        """Check if there are any critical failures."""
        return any(
            f.status == FindingStatus.FAIL and f.risk_level == RiskLevel.CRITICAL
            for f in self.findings
        )
    
    def all_checks_passed(self) -> bool:
        """Check if all findings passed."""
        return all(f.status == FindingStatus.PASS for f in self.findings)
