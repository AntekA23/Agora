"""Invoice model for persistence in MongoDB."""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field

from app.models.base import MongoBaseModel


class InvoiceStatus(str, Enum):
    """Invoice status."""

    DRAFT = "draft"  # Szkic - jeszcze nie wyslana
    ISSUED = "issued"  # Wystawiona
    SENT = "sent"  # Wyslana do klienta
    PAID = "paid"  # Oplacona
    OVERDUE = "overdue"  # Po terminie
    CANCELLED = "cancelled"  # Anulowana


class InvoiceItemModel(BaseModel):
    """Single invoice item with VAT calculation."""

    name: str
    description: str = ""
    quantity: float = 1.0
    unit: str = "szt."  # szt., godz., usluga, etc.
    unit_price_net: float  # Cena jednostkowa netto
    vat_rate: int = 23  # Stawka VAT (23, 8, 5, 0)

    # Calculated fields
    net_value: float = 0.0  # quantity * unit_price_net
    vat_value: float = 0.0  # net_value * vat_rate / 100
    gross_value: float = 0.0  # net_value + vat_value

    def calculate(self) -> "InvoiceItemModel":
        """Calculate net, VAT and gross values."""
        self.net_value = round(self.quantity * self.unit_price_net, 2)
        self.vat_value = round(self.net_value * self.vat_rate / 100, 2)
        self.gross_value = round(self.net_value + self.vat_value, 2)
        return self


class InvoiceParty(BaseModel):
    """Invoice party (seller or buyer)."""

    name: str
    address: str = ""
    nip: str = ""  # Tax ID
    email: str = ""
    phone: str = ""


class Invoice(MongoBaseModel):
    """Invoice model for MongoDB persistence."""

    # Identifiers
    company_id: str  # Company that issued the invoice
    invoice_number: str  # Full invoice number (e.g., "FV/1/2024")
    sequence_number: int  # Sequential number in period

    # Status
    status: InvoiceStatus = InvoiceStatus.DRAFT

    # Parties
    seller: InvoiceParty
    buyer: InvoiceParty

    # Dates
    issue_date: datetime = Field(default_factory=datetime.utcnow)
    sale_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: datetime | None = None
    payment_date: datetime | None = None  # When actually paid

    # Items
    items: list[InvoiceItemModel] = Field(default_factory=list)

    # Totals (calculated from items)
    total_net: float = 0.0
    total_vat: float = 0.0
    total_gross: float = 0.0

    # VAT breakdown by rate
    vat_summary: dict[str, dict[str, float]] = Field(default_factory=dict)
    # e.g., {"23": {"net": 1000, "vat": 230, "gross": 1230}}

    # Payment
    payment_method: str = "przelew"  # przelew, gotowka, karta
    bank_account: str = ""
    payment_days: int = 14

    # Additional
    notes: str = ""
    internal_notes: str = ""  # Notes not shown on invoice
    currency: str = "PLN"

    # PDF storage
    pdf_generated: bool = False
    pdf_path: str = ""  # Path to stored PDF
    pdf_base64: str = ""  # Base64 encoded PDF (optional, for quick access)

    # Tracking
    sent_at: datetime | None = None
    viewed_at: datetime | None = None
    reminder_sent_at: datetime | None = None

    def calculate_totals(self) -> "Invoice":
        """Calculate all totals from items."""
        self.total_net = 0.0
        self.total_vat = 0.0
        self.total_gross = 0.0
        self.vat_summary = {}

        for item in self.items:
            item.calculate()
            self.total_net += item.net_value
            self.total_vat += item.vat_value
            self.total_gross += item.gross_value

            # VAT breakdown
            rate_key = str(item.vat_rate)
            if rate_key not in self.vat_summary:
                self.vat_summary[rate_key] = {"net": 0.0, "vat": 0.0, "gross": 0.0}
            self.vat_summary[rate_key]["net"] += item.net_value
            self.vat_summary[rate_key]["vat"] += item.vat_value
            self.vat_summary[rate_key]["gross"] += item.gross_value

        # Round totals
        self.total_net = round(self.total_net, 2)
        self.total_vat = round(self.total_vat, 2)
        self.total_gross = round(self.total_gross, 2)

        return self

    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if self.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
            return False
        if self.due_date and datetime.utcnow() > self.due_date:
            return True
        return False

    def days_until_due(self) -> int | None:
        """Get days until due date (negative if overdue)."""
        if not self.due_date:
            return None
        delta = self.due_date - datetime.utcnow()
        return delta.days


class CashflowRecord(MongoBaseModel):
    """Cashflow record for tracking income/expenses."""

    company_id: str
    record_type: str  # "income" or "expense"

    # Basic info
    description: str
    amount: float
    category: str = ""
    date: datetime = Field(default_factory=datetime.utcnow)

    # Optional linking
    invoice_id: str | None = None  # Linked invoice if applicable
    recurring: bool = False
    recurring_period: str = ""  # "monthly", "weekly", etc.

    # Tags for analysis
    tags: list[str] = Field(default_factory=list)


class CashflowReport(MongoBaseModel):
    """Generated cashflow analysis report."""

    company_id: str
    period: str  # "month", "quarter", "year"
    period_start: datetime
    period_end: datetime

    # Summary
    total_income: float = 0.0
    total_expenses: float = 0.0
    balance: float = 0.0

    # Breakdown by category
    income_by_category: dict[str, float] = Field(default_factory=dict)
    expenses_by_category: dict[str, float] = Field(default_factory=dict)

    # Analysis content (generated by AI)
    analysis_content: str = ""
    recommendations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    health_score: int = 0  # 0-100

    # PDF
    pdf_generated: bool = False
    pdf_path: str = ""
    pdf_base64: str = ""
