from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str
    category: str

class CampaignInput(BaseModel):
    segment_name: str
    campaign_type: str
    products: List[Product]
    num_variants: int

class SubjectLine(BaseModel):
    subject: str = Field(..., max_length=50)

class Preheader(BaseModel):
    preheader: str = Field(..., min_length=50, max_length=100)

class EmailModule(BaseModel):
    title: str
    content: str
    cta_text: Optional[str]
    cta_link: Optional[str]

class EmailBody(BaseModel):
    product_modules : List[EmailModule]
    main_cta: str
    main_cta_link: str

class EmailVariant(BaseModel):
    subject_line: str
    pre_header: str
    body: str
    html_email: Optional[str] = None

class ProductResearch(BaseModel):
    product_name: str
    research_summary: str
    offer_summary: str

class EmailCampaignState(TypedDict):
    products: List[Product]
    campaignInfo: CampaignInput
    campaign_plan: Optional[str]
    research_findings: Optional[List[ProductResearch]]
    current_subject_line: Optional[str]
    current_preheader: Optional[str]
    current_body: Optional[str]
    current_variant: Optional[EmailVariant]
    html_email: Optional[str]
    variants: Optional[List[dict]]
    qa_feedback: Optional[str]
    current_tone: Optional[str]

class QAFeedback(BaseModel):
    overall_rating: int
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    needs_revision: bool
    revision_count: int = 0