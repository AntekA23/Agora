"""PDF Generator tool for creating professional documents."""

import base64
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, BaseLoader

from app.core.config import settings

# Lazy import for WeasyPrint - only load when actually generating PDFs
# This allows the app to start even if WeasyPrint system dependencies are missing
_weasyprint_html = None


def _get_weasyprint_html():
    """Lazy load WeasyPrint HTML class."""
    global _weasyprint_html
    if _weasyprint_html is None:
        from weasyprint import HTML
        _weasyprint_html = HTML
    return _weasyprint_html


# Invoice HTML Template
INVOICE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 12px;
            line-height: 1.5;
            color: #333;
        }
        .header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #3b82f6;
        }
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #3b82f6;
        }
        .invoice-title {
            font-size: 28px;
            color: #1f2937;
            text-align: right;
        }
        .invoice-number {
            font-size: 14px;
            color: #6b7280;
            text-align: right;
        }
        .parties {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }
        .party {
            width: 45%;
        }
        .party-label {
            font-size: 10px;
            color: #6b7280;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .party-name {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .party-details {
            color: #4b5563;
        }
        .dates {
            display: flex;
            gap: 40px;
            margin-bottom: 30px;
            padding: 15px;
            background: #f9fafb;
            border-radius: 8px;
        }
        .date-item {
            text-align: center;
        }
        .date-label {
            font-size: 10px;
            color: #6b7280;
            text-transform: uppercase;
        }
        .date-value {
            font-size: 14px;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }
        th {
            background: #3b82f6;
            color: white;
            padding: 12px;
            text-align: left;
            font-size: 11px;
            text-transform: uppercase;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }
        tr:nth-child(even) {
            background: #f9fafb;
        }
        .text-right {
            text-align: right;
        }
        .totals {
            width: 300px;
            margin-left: auto;
        }
        .totals-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e5e7eb;
        }
        .totals-row.total {
            font-size: 18px;
            font-weight: bold;
            color: #3b82f6;
            border-bottom: none;
            border-top: 2px solid #3b82f6;
            padding-top: 15px;
        }
        .payment-info {
            margin-top: 30px;
            padding: 20px;
            background: #f0f9ff;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }
        .payment-title {
            font-weight: bold;
            margin-bottom: 10px;
        }
        .notes {
            margin-top: 30px;
            padding: 15px;
            background: #fefce8;
            border-radius: 8px;
            font-size: 11px;
            color: #854d0e;
        }
        .footer {
            margin-top: 50px;
            text-align: center;
            font-size: 10px;
            color: #9ca3af;
        }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="logo">{{ seller_name }}</div>
            <div class="party-details">{{ seller_address }}</div>
            {% if seller_nip %}<div class="party-details">NIP: {{ seller_nip }}</div>{% endif %}
        </div>
        <div>
            <div class="invoice-title">FAKTURA VAT</div>
            <div class="invoice-number">{{ invoice_number }}</div>
        </div>
    </div>

    <div class="parties">
        <div class="party">
            <div class="party-label">Sprzedawca</div>
            <div class="party-name">{{ seller_name }}</div>
            <div class="party-details">{{ seller_address }}</div>
            {% if seller_nip %}<div class="party-details">NIP: {{ seller_nip }}</div>{% endif %}
            {% if seller_email %}<div class="party-details">{{ seller_email }}</div>{% endif %}
        </div>
        <div class="party">
            <div class="party-label">Nabywca</div>
            <div class="party-name">{{ client_name }}</div>
            <div class="party-details">{{ client_address }}</div>
            {% if client_nip %}<div class="party-details">NIP: {{ client_nip }}</div>{% endif %}
        </div>
    </div>

    <div class="dates">
        <div class="date-item">
            <div class="date-label">Data wystawienia</div>
            <div class="date-value">{{ issue_date }}</div>
        </div>
        <div class="date-item">
            <div class="date-label">Data sprzedaży</div>
            <div class="date-value">{{ sale_date }}</div>
        </div>
        <div class="date-item">
            <div class="date-label">Termin płatności</div>
            <div class="date-value">{{ due_date }}</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Lp.</th>
                <th>Nazwa</th>
                <th class="text-right">Ilość</th>
                <th class="text-right">Cena netto</th>
                <th class="text-right">VAT</th>
                <th class="text-right">Wartość brutto</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ item.name }}</td>
                <td class="text-right">{{ item.quantity }}</td>
                <td class="text-right">{{ "%.2f"|format(item.price) }} PLN</td>
                <td class="text-right">{{ item.vat_rate }}%</td>
                <td class="text-right">{{ "%.2f"|format(item.gross) }} PLN</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="totals">
        <div class="totals-row">
            <span>Suma netto:</span>
            <span>{{ "%.2f"|format(total_net) }} PLN</span>
        </div>
        <div class="totals-row">
            <span>VAT ({{ vat_rate }}%):</span>
            <span>{{ "%.2f"|format(total_vat) }} PLN</span>
        </div>
        <div class="totals-row total">
            <span>Do zapłaty:</span>
            <span>{{ "%.2f"|format(total_gross) }} PLN</span>
        </div>
    </div>

    {% if bank_account %}
    <div class="payment-info">
        <div class="payment-title">Dane do przelewu</div>
        <div>Numer konta: {{ bank_account }}</div>
        <div>Tytuł przelewu: {{ invoice_number }}</div>
    </div>
    {% endif %}

    {% if notes %}
    <div class="notes">
        <strong>Uwagi:</strong> {{ notes }}
    </div>
    {% endif %}

    <div class="footer">
        Dokument wygenerowany automatycznie przez system Agora
    </div>
</body>
</html>
"""


# Report HTML Template
REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 12px;
            line-height: 1.6;
            color: #333;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #3b82f6;
        }
        .title {
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
        }
        .subtitle {
            font-size: 14px;
            color: #6b7280;
            margin-top: 5px;
        }
        .section {
            margin-bottom: 25px;
        }
        .section-title {
            font-size: 16px;
            font-weight: bold;
            color: #3b82f6;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid #e5e7eb;
        }
        .summary-box {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-item {
            flex: 1;
            padding: 20px;
            background: #f9fafb;
            border-radius: 8px;
            text-align: center;
        }
        .summary-value {
            font-size: 24px;
            font-weight: bold;
            color: #3b82f6;
        }
        .summary-value.positive { color: #10b981; }
        .summary-value.negative { color: #ef4444; }
        .summary-label {
            font-size: 11px;
            color: #6b7280;
            text-transform: uppercase;
        }
        .content {
            white-space: pre-wrap;
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
        }
        .footer {
            margin-top: 50px;
            text-align: center;
            font-size: 10px;
            color: #9ca3af;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">{{ title }}</div>
        <div class="subtitle">{{ subtitle }}</div>
    </div>

    {% if show_summary %}
    <div class="summary-box">
        <div class="summary-item">
            <div class="summary-value positive">{{ "%.2f"|format(total_income) }} PLN</div>
            <div class="summary-label">Przychody</div>
        </div>
        <div class="summary-item">
            <div class="summary-value negative">{{ "%.2f"|format(total_expenses) }} PLN</div>
            <div class="summary-label">Wydatki</div>
        </div>
        <div class="summary-item">
            <div class="summary-value {% if balance >= 0 %}positive{% else %}negative{% endif %}">
                {{ "%.2f"|format(balance) }} PLN
            </div>
            <div class="summary-label">Bilans</div>
        </div>
    </div>
    {% endif %}

    <div class="section">
        <div class="content">{{ content }}</div>
    </div>

    <div class="footer">
        Raport wygenerowany {{ generated_at }} przez system Agora
    </div>
</body>
</html>
"""


class PDFGenerator:
    """Service for generating PDF documents."""

    def __init__(self):
        self.env = Environment(loader=BaseLoader())

    def generate_invoice_pdf(
        self,
        invoice_number: str,
        seller_name: str,
        seller_address: str,
        seller_nip: str = "",
        seller_email: str = "",
        client_name: str = "",
        client_address: str = "",
        client_nip: str = "",
        items: list[dict] = None,
        notes: str = "",
        bank_account: str = "",
        vat_rate: int = 23,
        issue_date: str = None,
        sale_date: str = None,
        due_days: int = 14,
    ) -> bytes:
        """Generate professional invoice PDF."""
        items = items or []
        today = datetime.now()

        # Calculate totals
        total_net = 0
        for item in items:
            item_net = item.get("quantity", 1) * item.get("price", 0)
            item_vat = item_net * (item.get("vat_rate", vat_rate) / 100)
            item["gross"] = item_net + item_vat
            item["vat_rate"] = item.get("vat_rate", vat_rate)
            total_net += item_net

        total_vat = total_net * (vat_rate / 100)
        total_gross = total_net + total_vat

        # Render template
        template = self.env.from_string(INVOICE_TEMPLATE)
        html_content = template.render(
            invoice_number=invoice_number,
            seller_name=seller_name,
            seller_address=seller_address,
            seller_nip=seller_nip,
            seller_email=seller_email,
            client_name=client_name,
            client_address=client_address,
            client_nip=client_nip,
            items=items,
            total_net=total_net,
            total_vat=total_vat,
            total_gross=total_gross,
            vat_rate=vat_rate,
            notes=notes,
            bank_account=bank_account,
            issue_date=issue_date or today.strftime("%d.%m.%Y"),
            sale_date=sale_date or today.strftime("%d.%m.%Y"),
            due_date=(today + timedelta(days=due_days)).strftime("%d.%m.%Y"),
        )

        # Generate PDF (lazy load WeasyPrint)
        HTML = _get_weasyprint_html()
        html = HTML(string=html_content)
        return html.write_pdf()

    def generate_report_pdf(
        self,
        title: str,
        content: str,
        subtitle: str = "",
        total_income: float = 0,
        total_expenses: float = 0,
        balance: float = 0,
        show_summary: bool = True,
    ) -> bytes:
        """Generate report PDF (e.g., cashflow analysis)."""
        template = self.env.from_string(REPORT_TEMPLATE)
        html_content = template.render(
            title=title,
            subtitle=subtitle,
            content=content,
            total_income=total_income,
            total_expenses=total_expenses,
            balance=balance,
            show_summary=show_summary,
            generated_at=datetime.now().strftime("%d.%m.%Y %H:%M"),
        )

        # Generate PDF (lazy load WeasyPrint)
        HTML = _get_weasyprint_html()
        html = HTML(string=html_content)
        return html.write_pdf()

    def pdf_to_base64(self, pdf_bytes: bytes) -> str:
        """Convert PDF bytes to base64 string for API response."""
        return base64.b64encode(pdf_bytes).decode("utf-8")


# Singleton instance
pdf_generator = PDFGenerator()
