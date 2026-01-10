from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# =============================================================================
# INVOICE SCHEMAS
# =============================================================================


class InvoiceItem(BaseModel):
    """Single invoice item input."""

    name: str = Field(..., min_length=1)
    description: str = Field(default="")
    quantity: float = Field(default=1, gt=0)
    unit: str = Field(default="szt.")
    price: float = Field(..., gt=0)  # Unit price net
    vat_rate: int = Field(default=23, ge=0, le=100)


class InvoiceClientInput(BaseModel):
    """Client (buyer) information for invoice."""

    name: str = Field(..., min_length=2)
    address: str = Field(..., min_length=5)
    nip: str = Field(default="")
    email: str = Field(default="")


class InvoiceTaskInput(BaseModel):
    """Input for invoice generation task."""

    client_name: str = Field(..., min_length=2)
    client_address: str = Field(..., min_length=5)
    client_nip: str = Field(default="")
    client_email: str = Field(default="")
    items: list[InvoiceItem] = Field(..., min_length=1)
    notes: str = Field(default="")
    payment_days: int = Field(default=14, ge=0, le=365)
    issue_date: str = Field(default="")  # YYYY-MM-DD, empty = today
    sale_date: str = Field(default="")  # YYYY-MM-DD, empty = today
    generate_pdf: bool = Field(default=True)
    save_to_db: bool = Field(default=True)


class InvoiceItemResult(BaseModel):
    """Calculated invoice item in result."""

    name: str
    description: str = ""
    quantity: float
    unit: str
    unit_price_net: float
    vat_rate: int
    net_value: float
    vat_value: float
    gross_value: float


class InvoiceResult(BaseModel):
    """Complete invoice generation result."""

    success: bool = True
    invoice_id: str | None = None  # MongoDB ID if saved
    invoice_number: str = ""

    # Parties
    seller_name: str = ""
    seller_address: str = ""
    seller_nip: str = ""
    client_name: str = ""
    client_address: str = ""
    client_nip: str = ""

    # Dates
    issue_date: str = ""
    sale_date: str = ""
    due_date: str = ""

    # Items with calculations
    items: list[InvoiceItemResult] = Field(default_factory=list)

    # Totals
    total_net: float = 0.0
    total_vat: float = 0.0
    total_gross: float = 0.0
    vat_summary: dict[str, dict[str, float]] = Field(default_factory=dict)

    # Payment
    bank_account: str = ""
    payment_method: str = "przelew"

    # Additional
    notes: str = ""
    currency: str = "PLN"

    # PDF
    pdf_generated: bool = False
    pdf_base64: str = ""  # Base64 encoded PDF

    # Errors
    error: str = ""


# =============================================================================
# CASHFLOW SCHEMAS
# =============================================================================


class CashflowItem(BaseModel):
    """Single cashflow item."""

    description: str
    amount: float = Field(..., gt=0)
    date: str = ""  # YYYY-MM-DD
    category: str = ""
    tags: list[str] = Field(default_factory=list)


class CashflowTaskInput(BaseModel):
    """Input for cashflow analysis."""

    income: list[CashflowItem] = Field(default_factory=list)
    expenses: list[CashflowItem] = Field(default_factory=list)
    period: str = Field(default="miesiac")  # miesiac, kwartal, rok
    include_analysis: bool = Field(default=True)
    include_recommendations: bool = Field(default=True)
    generate_pdf: bool = Field(default=False)
    save_to_db: bool = Field(default=False)


class CategoryBreakdown(BaseModel):
    """Category breakdown in cashflow."""

    category: str
    amount: float
    percentage: float
    count: int = 1


class CashflowMetrics(BaseModel):
    """Calculated cashflow metrics."""

    # Basic
    total_income: float = 0.0
    total_expenses: float = 0.0
    balance: float = 0.0

    # Ratios
    expense_to_income_ratio: float = 0.0  # wydatki / przychody
    savings_rate: float = 0.0  # (przychody - wydatki) / przychody * 100

    # Averages (if multiple periods)
    avg_income: float = 0.0
    avg_expenses: float = 0.0

    # Runway
    months_runway: float = 0.0  # Na ile miesiecy starczy przy obecnych wydatkach

    # Health score 0-100
    health_score: int = 0
    health_status: str = ""  # "healthy", "warning", "critical"


class CashflowRecommendation(BaseModel):
    """Single cashflow recommendation."""

    action: str
    priority: str = "medium"  # high, medium, low
    expected_impact: str = ""
    category: str = ""  # cost_reduction, income_increase, risk_mitigation


class CashflowResult(BaseModel):
    """Complete cashflow analysis result."""

    success: bool = True
    report_id: str | None = None  # MongoDB ID if saved

    # Period
    period: str = ""
    period_start: str = ""
    period_end: str = ""

    # Metrics
    metrics: CashflowMetrics = Field(default_factory=CashflowMetrics)

    # Breakdowns
    income_by_category: list[CategoryBreakdown] = Field(default_factory=list)
    expenses_by_category: list[CategoryBreakdown] = Field(default_factory=list)

    # AI Analysis
    summary: str = ""
    analysis: str = ""
    recommendations: list[CashflowRecommendation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)

    # Comparison with benchmarks (if available)
    benchmark_comparison: str = ""

    # PDF
    pdf_generated: bool = False
    pdf_base64: str = ""

    # Errors
    error: str = ""


# =============================================================================
# INVOICE SETTINGS SCHEMAS (for API)
# =============================================================================


class InvoiceSettingsUpdate(BaseModel):
    """Schema for updating company invoice settings."""

    seller_name: str | None = None
    seller_address: str | None = None
    seller_nip: str | None = None
    seller_email: str | None = None
    seller_phone: str | None = None
    bank_name: str | None = None
    bank_account: str | None = None
    invoice_prefix: str | None = None
    invoice_numbering: str | None = None  # "yearly" or "monthly"
    default_vat_rate: int | None = None
    default_payment_days: int | None = None
    invoice_notes: str | None = None
    invoice_footer: str | None = None


class InvoiceSettingsResponse(BaseModel):
    """Response with company invoice settings."""

    seller_name: str = ""
    seller_address: str = ""
    seller_nip: str = ""
    seller_email: str = ""
    seller_phone: str = ""
    bank_name: str = ""
    bank_account: str = ""
    invoice_prefix: str = "FV"
    invoice_numbering: str = "yearly"
    default_vat_rate: int = 23
    default_payment_days: int = 14
    invoice_notes: str = ""
    invoice_footer: str = ""
    is_configured: bool = False  # True if seller_name and seller_nip are set
