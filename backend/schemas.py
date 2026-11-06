from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class InvestigationSummary(BaseModel):
    """Header of the RCA form. All fields optional: unknown => null."""
    deviation_id: Optional[str] = Field(None, description="Linked deviation/incident reference, if stated")
    title: Optional[str] = None
    product_name: Optional[str] = None
    batch_number: Optional[str] = None
    process_step: Optional[str] = Field(None, description="e.g. drying, crystallization, milling")
    equipment_id: Optional[str] = None
    date_detected: Optional[str] = None
    reported_by: Optional[str] = None
    problem_statement: Optional[str] = Field(None, description="What happened, factual, no speculation")
    affected_quantity: Optional[str] = None
    immediate_containment: Optional[str] = Field(None, description="Actions already taken, e.g. batch quarantined")


class RiskAssessment(BaseModel):
    severity: Optional[Literal["Critical", "Major", "Minor"]] = None
    batch_impact: Optional[str] = None
    recommended_next_action: Optional[str] = None
    regulatory_reportability: Optional[str] = Field(None, description="Possible regulatory impact; say 'to be assessed by QA' if unsure")
    rationale: Optional[str] = None


class Why(BaseModel):
    level: int
    question: str
    answer: str
    evidence_needed: Optional[str] = None


class Cause(BaseModel):
    id: str
    text: str
    category: Literal["Man", "Machine", "Method", "Material", "Measurement", "Environment"]
    is_probable_root: bool = False
    confidence: Literal["low", "medium", "high"] = "low"
    source_quote: Optional[str] = Field(None, description="Sentence from the input that supports this cause; null if none")
    status: Literal["suggested", "confirmed", "rejected"] = "suggested"  # changed by humans only


class EvidenceItem(BaseModel):
    item: str
    status: Literal["available", "missing"]
    why_needed: Optional[str] = None
    related_cause_id: Optional[str] = None


class Capa(BaseModel):
    id: str
    type: Literal["Corrective", "Preventive"]
    action: str
    rationale: str
    effectiveness_check: str
    linked_cause_id: Optional[str] = None


class Analysis(BaseModel):
    whys: List[Why] = []
    causes: List[Cause] = []
    evidence: List[EvidenceItem] = []
    capas: List[Capa] = []


class FormState(BaseModel):
    summary: InvestigationSummary = InvestigationSummary()
    risk: RiskAssessment = RiskAssessment()
    analysis: Analysis = Analysis()