from pydantic import BaseModel, Field


class InvoiceItem(BaseModel):
    """Single invoice item."""

    name: str = Field(..., min_length=1)
    quantity: int = Field(default=1, ge=1)
    price: float = Field(..., gt=0)


class InvoiceTaskInput(BaseModel):
    """Input for invoice generation."""

    client_name: str = Field(..., min_length=2)
    client_address: str = Field(..., min_length=5)
    items: list[InvoiceItem] = Field(..., min_length=1)
    notes: str = Field(default="")


class CashflowItem(BaseModel):
    """Single cashflow item."""

    description: str
    amount: float
    date: str = ""
    category: str = ""


class CashflowTaskInput(BaseModel):
    """Input for cashflow analysis."""

    income: list[CashflowItem] = Field(default_factory=list)
    expenses: list[CashflowItem] = Field(default_factory=list)
    period: str = Field(default="miesiac")
