"""Invoice Agent - Complete invoice generation with PDF, persistence and numbering.

This module provides:
- Automatic invoice numbering (yearly/monthly)
- VAT calculations using calculator tools
- PDF generation using WeasyPrint
- Persistence to MongoDB
- AI-powered validation and review
"""

from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.models.invoice import Invoice, InvoiceItemModel, InvoiceParty, InvoiceStatus
from app.schemas.finance import (
    InvoiceItem,
    InvoiceItemResult,
    InvoiceResult,
    InvoiceTaskInput,
)
from app.services.agents.tools.pdf_generator import pdf_generator
from app.services.agents.tools.calculator import VATCalculatorTool


class InvoiceService:
    """Service for generating, storing and managing invoices."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize with database connection."""
        self.db = db
        self.vat_calculator = VATCalculatorTool()

    async def get_company(self, company_id: str) -> dict | None:
        """Get company data from database."""
        company = await self.db.companies.find_one({"_id": company_id})
        return company

    async def get_next_invoice_number(self, company_id: str) -> tuple[str, int]:
        """Generate next invoice number for company.

        Returns:
            Tuple of (full_invoice_number, sequence_number)
        """
        company = await self.get_company(company_id)
        if not company:
            raise ValueError(f"Firma o ID {company_id} nie istnieje")

        inv_settings = company.get("invoice_settings", {})
        prefix = inv_settings.get("invoice_prefix", "FV")
        numbering = inv_settings.get("invoice_numbering", "yearly")

        now = datetime.utcnow()
        current_year = now.year
        current_month = now.month

        last_number = inv_settings.get("last_invoice_number", 0)
        last_year = inv_settings.get("last_invoice_year", 0)
        last_month = inv_settings.get("last_invoice_month", 0)

        # Reset counter if new period
        if numbering == "yearly":
            if last_year != current_year:
                next_number = 1
            else:
                next_number = last_number + 1
            invoice_number = f"{prefix}/{next_number}/{current_year}"
        else:  # monthly
            if last_year != current_year or last_month != current_month:
                next_number = 1
            else:
                next_number = last_number + 1
            invoice_number = f"{prefix}/{next_number}/{current_month:02d}/{current_year}"

        # Update company settings
        await self.db.companies.update_one(
            {"_id": company_id},
            {
                "$set": {
                    "invoice_settings.last_invoice_number": next_number,
                    "invoice_settings.last_invoice_year": current_year,
                    "invoice_settings.last_invoice_month": current_month,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        return invoice_number, next_number

    def calculate_item(self, item: InvoiceItem) -> InvoiceItemResult:
        """Calculate VAT values for single item."""
        quantity = Decimal(str(item.quantity))
        unit_price = Decimal(str(item.price))
        vat_rate = Decimal(str(item.vat_rate))

        net_value = (quantity * unit_price).quantize(Decimal("0.01"), ROUND_HALF_UP)
        vat_value = (net_value * vat_rate / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
        gross_value = net_value + vat_value

        return InvoiceItemResult(
            name=item.name,
            description=item.description,
            quantity=float(quantity),
            unit=item.unit,
            unit_price_net=float(unit_price),
            vat_rate=item.vat_rate,
            net_value=float(net_value),
            vat_value=float(vat_value),
            gross_value=float(gross_value),
        )

    def calculate_totals(
        self, items: list[InvoiceItemResult]
    ) -> tuple[float, float, float, dict[str, dict[str, float]]]:
        """Calculate totals and VAT summary.

        Returns:
            Tuple of (total_net, total_vat, total_gross, vat_summary)
        """
        total_net = Decimal("0")
        total_vat = Decimal("0")
        total_gross = Decimal("0")
        vat_summary: dict[str, dict[str, float]] = {}

        for item in items:
            net = Decimal(str(item.net_value))
            vat = Decimal(str(item.vat_value))
            gross = Decimal(str(item.gross_value))

            total_net += net
            total_vat += vat
            total_gross += gross

            # VAT breakdown by rate
            rate_key = str(item.vat_rate)
            if rate_key not in vat_summary:
                vat_summary[rate_key] = {"net": 0.0, "vat": 0.0, "gross": 0.0}
            vat_summary[rate_key]["net"] += float(net)
            vat_summary[rate_key]["vat"] += float(vat)
            vat_summary[rate_key]["gross"] += float(gross)

        return (
            float(total_net.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            float(total_vat.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            float(total_gross.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            vat_summary,
        )

    async def generate_invoice(
        self,
        company_id: str,
        input_data: InvoiceTaskInput,
    ) -> InvoiceResult:
        """Generate complete invoice with calculations, PDF and persistence.

        Args:
            company_id: Company ID that issues the invoice
            input_data: Invoice input data

        Returns:
            InvoiceResult with all data and optional PDF
        """
        result = InvoiceResult()

        try:
            # 1. Get company data
            company = await self.get_company(company_id)
            if not company:
                result.success = False
                result.error = f"Firma o ID {company_id} nie istnieje"
                return result

            inv_settings = company.get("invoice_settings", {})

            # Check if invoice settings are configured
            seller_name = inv_settings.get("seller_name") or company.get("name", "")
            seller_nip = inv_settings.get("seller_nip", "")

            if not seller_name:
                result.success = False
                result.error = "Brak nazwy firmy. Uzupelnij dane w ustawieniach faktur."
                return result

            # 2. Generate invoice number
            invoice_number, seq_number = await self.get_next_invoice_number(company_id)

            # 3. Calculate items
            calculated_items = [self.calculate_item(item) for item in input_data.items]
            total_net, total_vat, total_gross, vat_summary = self.calculate_totals(
                calculated_items
            )

            # 4. Prepare dates
            now = datetime.utcnow()
            if input_data.issue_date:
                try:
                    issue_date = datetime.strptime(input_data.issue_date, "%Y-%m-%d")
                except ValueError:
                    issue_date = now
            else:
                issue_date = now

            if input_data.sale_date:
                try:
                    sale_date = datetime.strptime(input_data.sale_date, "%Y-%m-%d")
                except ValueError:
                    sale_date = now
            else:
                sale_date = now

            payment_days = input_data.payment_days or inv_settings.get(
                "default_payment_days", 14
            )
            due_date = issue_date + timedelta(days=payment_days)

            # 5. Prepare seller data
            seller = InvoiceParty(
                name=seller_name,
                address=inv_settings.get("seller_address", ""),
                nip=seller_nip,
                email=inv_settings.get("seller_email", ""),
                phone=inv_settings.get("seller_phone", ""),
            )

            # 6. Prepare buyer data
            buyer = InvoiceParty(
                name=input_data.client_name,
                address=input_data.client_address,
                nip=input_data.client_nip,
                email=input_data.client_email,
            )

            # 7. Build result
            result.invoice_number = invoice_number
            result.seller_name = seller.name
            result.seller_address = seller.address
            result.seller_nip = seller.nip
            result.client_name = buyer.name
            result.client_address = buyer.address
            result.client_nip = buyer.nip
            result.issue_date = issue_date.strftime("%d.%m.%Y")
            result.sale_date = sale_date.strftime("%d.%m.%Y")
            result.due_date = due_date.strftime("%d.%m.%Y")
            result.items = calculated_items
            result.total_net = total_net
            result.total_vat = total_vat
            result.total_gross = total_gross
            result.vat_summary = vat_summary
            result.bank_account = inv_settings.get("bank_account", "")
            result.notes = input_data.notes or inv_settings.get("invoice_notes", "")

            # 8. Generate PDF if requested
            if input_data.generate_pdf:
                try:
                    pdf_items = [
                        {
                            "name": item.name,
                            "quantity": item.quantity,
                            "price": item.unit_price_net,
                            "vat_rate": item.vat_rate,
                            "gross": item.gross_value,
                        }
                        for item in calculated_items
                    ]

                    pdf_bytes = pdf_generator.generate_invoice_pdf(
                        invoice_number=invoice_number,
                        seller_name=seller.name,
                        seller_address=seller.address,
                        seller_nip=seller.nip,
                        seller_email=seller.email,
                        client_name=buyer.name,
                        client_address=buyer.address,
                        client_nip=buyer.nip,
                        items=pdf_items,
                        notes=result.notes,
                        bank_account=result.bank_account,
                        vat_rate=inv_settings.get("default_vat_rate", 23),
                        issue_date=result.issue_date,
                        sale_date=result.sale_date,
                        due_days=payment_days,
                    )
                    result.pdf_base64 = pdf_generator.pdf_to_base64(pdf_bytes)
                    result.pdf_generated = True
                except Exception as e:
                    # PDF generation failed but continue - not critical
                    result.pdf_generated = False

            # 9. Save to database if requested
            if input_data.save_to_db:
                invoice_model = Invoice(
                    company_id=company_id,
                    invoice_number=invoice_number,
                    sequence_number=seq_number,
                    status=InvoiceStatus.ISSUED,
                    seller=seller,
                    buyer=buyer,
                    issue_date=issue_date,
                    sale_date=sale_date,
                    due_date=due_date,
                    items=[
                        InvoiceItemModel(
                            name=item.name,
                            description=item.description,
                            quantity=item.quantity,
                            unit=item.unit,
                            unit_price_net=item.unit_price_net,
                            vat_rate=item.vat_rate,
                            net_value=item.net_value,
                            vat_value=item.vat_value,
                            gross_value=item.gross_value,
                        )
                        for item in calculated_items
                    ],
                    total_net=total_net,
                    total_vat=total_vat,
                    total_gross=total_gross,
                    vat_summary=vat_summary,
                    bank_account=result.bank_account,
                    payment_days=payment_days,
                    notes=result.notes,
                    pdf_generated=result.pdf_generated,
                    pdf_base64=result.pdf_base64 if result.pdf_generated else "",
                )

                invoice_dict = invoice_model.model_dump(by_alias=True, exclude={"id"})
                insert_result = await self.db.invoices.insert_one(invoice_dict)
                result.invoice_id = str(insert_result.inserted_id)

            result.success = True
            return result

        except Exception as e:
            result.success = False
            result.error = f"Blad generowania faktury: {e!s}"
            return result

    async def get_invoice(self, invoice_id: str) -> Invoice | None:
        """Get invoice by ID."""
        doc = await self.db.invoices.find_one({"_id": invoice_id})
        if doc:
            return Invoice(**doc)
        return None

    async def list_invoices(
        self,
        company_id: str,
        status: InvoiceStatus | None = None,
        limit: int = 50,
        skip: int = 0,
    ) -> list[Invoice]:
        """List invoices for company."""
        query: dict[str, Any] = {"company_id": company_id}
        if status:
            query["status"] = status.value

        cursor = (
            self.db.invoices.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        invoices = []
        async for doc in cursor:
            invoices.append(Invoice(**doc))
        return invoices

    async def update_invoice_status(
        self, invoice_id: str, status: InvoiceStatus
    ) -> bool:
        """Update invoice status."""
        update_data: dict[str, Any] = {
            "status": status.value,
            "updated_at": datetime.utcnow(),
        }

        if status == InvoiceStatus.PAID:
            update_data["payment_date"] = datetime.utcnow()
        elif status == InvoiceStatus.SENT:
            update_data["sent_at"] = datetime.utcnow()

        result = await self.db.invoices.update_one(
            {"_id": invoice_id}, {"$set": update_data}
        )
        return result.modified_count > 0

    async def mark_overdue_invoices(self, company_id: str) -> int:
        """Mark overdue invoices for company. Returns count of updated invoices."""
        now = datetime.utcnow()
        result = await self.db.invoices.update_many(
            {
                "company_id": company_id,
                "status": {"$in": [InvoiceStatus.ISSUED.value, InvoiceStatus.SENT.value]},
                "due_date": {"$lt": now},
            },
            {
                "$set": {
                    "status": InvoiceStatus.OVERDUE.value,
                    "updated_at": now,
                }
            },
        )
        return result.modified_count


async def validate_invoice_with_ai(
    invoice_result: InvoiceResult,
) -> dict[str, Any]:
    """Use AI to validate and review generated invoice.

    This is optional - called after invoice generation for quality check.
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.2,
    )

    validator = Agent(
        role="Invoice Validator",
        goal="Sprawdz poprawnosc faktury VAT",
        backstory="""Jestes doswiadczonym ksiegowym specjalizujacym sie w polskich fakturach VAT.
        Sprawdzasz faktury pod katem:
        - Poprawnosci obliczen (netto, VAT, brutto)
        - Kompletnosci wymaganych danych
        - Zgodnosci z polskimi przepisami""",
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=f"""Sprawdz fakture:

NUMER: {invoice_result.invoice_number}
SPRZEDAWCA: {invoice_result.seller_name}, NIP: {invoice_result.seller_nip}
NABYWCA: {invoice_result.client_name}, NIP: {invoice_result.client_nip}

POZYCJE:
{chr(10).join([f"- {item.name}: {item.quantity} x {item.unit_price_net} PLN = {item.net_value} netto + {item.vat_value} VAT = {item.gross_value} brutto" for item in invoice_result.items])}

SUMY:
- Netto: {invoice_result.total_net} PLN
- VAT: {invoice_result.total_vat} PLN
- Brutto: {invoice_result.total_gross} PLN

Odpowiedz w formacie JSON:
{{
    "is_valid": true/false,
    "calculation_correct": true/false,
    "issues": ["lista problemow jesli sa"],
    "suggestions": ["lista sugestii jesli sa"]
}}""",
        expected_output="JSON z wynikami walidacji",
        agent=validator,
    )

    crew = Crew(
        agents=[validator],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    import json
    import re

    result_text = str(result)
    json_match = re.search(r"\{[\s\S]*\}", result_text)

    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return {"is_valid": True, "raw_response": result_text}


# =============================================================================
# LEGACY FUNCTION (for backward compatibility)
# =============================================================================


async def generate_invoice_draft(
    client_name: str,
    client_address: str,
    items: list[dict],
    notes: str = "",
    language: str = "pl",
) -> dict:
    """Legacy function - generates invoice draft without persistence.

    DEPRECATED: Use InvoiceService.generate_invoice() instead for full functionality.
    """
    # Calculate totals
    total = sum(item.get("quantity", 1) * item.get("price", 0) for item in items)
    vat = round(total * 0.23, 2)
    gross = round(total + vat, 2)

    calculated_items = []
    for item in items:
        qty = item.get("quantity", 1)
        price = item.get("price", 0)
        net = round(qty * price, 2)
        item_vat = round(net * 0.23, 2)
        calculated_items.append(
            {
                "name": item.get("name", "Usluga"),
                "quantity": qty,
                "unit_price_net": price,
                "vat_rate": 23,
                "net_value": net,
                "vat_value": item_vat,
                "gross_value": round(net + item_vat, 2),
            }
        )

    return {
        "client_name": client_name,
        "client_address": client_address,
        "items": calculated_items,
        "total_net": total,
        "vat": vat,
        "total_gross": gross,
        "notes": notes,
        "invoice_number": "[DO UZUPELNIENIA]",
        "issue_date": datetime.utcnow().strftime("%d.%m.%Y"),
        "message": "UWAGA: To jest draft. Uzyj InvoiceService dla pelnej funkcjonalnosci.",
    }
