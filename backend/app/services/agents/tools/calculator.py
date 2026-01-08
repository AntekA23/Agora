"""Financial calculator tool for AI agents.

Provides calculation capabilities for:
- VAT calculations (Polish rates: 23%, 8%, 5%, 0%)
- Gross/net price conversions
- Margin and markup calculations
- Cashflow projections
- Percentage calculations
"""

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from crewai.tools import BaseTool
from pydantic import Field


# Polish VAT rates
VAT_RATES = {
    "standard": Decimal("0.23"),  # 23% - most goods/services
    "reduced": Decimal("0.08"),   # 8% - food, some services
    "super_reduced": Decimal("0.05"),  # 5% - basic food, books
    "zero": Decimal("0.00"),      # 0% - exports, some medical
}


class VATCalculatorTool(BaseTool):
    """Tool for VAT calculations with Polish tax rates."""

    name: str = "vat_calculator"
    description: str = """Kalkulator VAT dla polskich stawek podatkowych.
    Uzyj tego narzedzia do:
    - Obliczenia kwoty brutto z netto (dodanie VAT)
    - Obliczenia kwoty netto z brutto (odliczenie VAT)
    - Obliczenia samej kwoty VAT

    Dostepne stawki VAT: 23% (standard), 8% (reduced), 5% (super_reduced), 0% (zero)

    Input format: 'operacja kwota stawka'
    Przyklady:
    - 'netto_to_brutto 1000 23' -> oblicza brutto z 1000 netto przy 23% VAT
    - 'brutto_to_netto 1230 23' -> oblicza netto z 1230 brutto przy 23% VAT
    - 'vat_amount 1000 23' -> oblicza kwote VAT od 1000 netto przy 23%"""

    def _run(self, input_str: str) -> str:
        """Execute VAT calculation."""
        try:
            parts = input_str.strip().split()
            if len(parts) < 3:
                return "Blad: Podaj operacje, kwote i stawke VAT (np. 'netto_to_brutto 1000 23')"

            operation = parts[0].lower()
            amount = Decimal(parts[1].replace(",", "."))
            rate_str = parts[2].replace("%", "")

            # Determine VAT rate
            rate_decimal = Decimal(rate_str) / 100

            if operation in ["netto_to_brutto", "net_to_gross", "do_brutto"]:
                vat_amount = (amount * rate_decimal).quantize(Decimal("0.01"), ROUND_HALF_UP)
                gross = amount + vat_amount
                return (
                    f"OBLICZENIE VAT (netto -> brutto):\n"
                    f"Kwota netto: {amount:.2f} PLN\n"
                    f"Stawka VAT: {rate_str}%\n"
                    f"Kwota VAT: {vat_amount:.2f} PLN\n"
                    f"Kwota brutto: {gross:.2f} PLN"
                )

            elif operation in ["brutto_to_netto", "gross_to_net", "do_netto"]:
                net = (amount / (1 + rate_decimal)).quantize(Decimal("0.01"), ROUND_HALF_UP)
                vat_amount = amount - net
                return (
                    f"OBLICZENIE VAT (brutto -> netto):\n"
                    f"Kwota brutto: {amount:.2f} PLN\n"
                    f"Stawka VAT: {rate_str}%\n"
                    f"Kwota netto: {net:.2f} PLN\n"
                    f"Kwota VAT: {vat_amount:.2f} PLN"
                )

            elif operation in ["vat_amount", "kwota_vat", "vat"]:
                vat_amount = (amount * rate_decimal).quantize(Decimal("0.01"), ROUND_HALF_UP)
                return (
                    f"KWOTA VAT:\n"
                    f"Podstawa (netto): {amount:.2f} PLN\n"
                    f"Stawka VAT: {rate_str}%\n"
                    f"Kwota VAT: {vat_amount:.2f} PLN"
                )

            else:
                return (
                    f"Nieznana operacja: {operation}\n"
                    f"Dostepne: netto_to_brutto, brutto_to_netto, vat_amount"
                )

        except Exception as e:
            return f"Blad obliczenia: {e!s}"


class MarginCalculatorTool(BaseTool):
    """Tool for margin and markup calculations."""

    name: str = "margin_calculator"
    description: str = """Kalkulator marzy i narzutu.
    Uzyj tego narzedzia do:
    - Obliczenia marzy procentowej (margin)
    - Obliczenia narzutu procentowego (markup)
    - Obliczenia ceny sprzedazy z kosztu i marzy
    - Obliczenia zysku

    Input format: 'operacja wartosc1 wartosc2'
    Przyklady:
    - 'margin 80 100' -> oblicza marze (koszt 80, cena 100) = 20%
    - 'markup 80 100' -> oblicza narzut (koszt 80, cena 100) = 25%
    - 'price_from_margin 80 20' -> cena przy koszcie 80 i marzy 20%
    - 'price_from_markup 80 25' -> cena przy koszcie 80 i narzucie 25%
    - 'profit 80 100' -> zysk (koszt 80, cena 100)"""

    def _run(self, input_str: str) -> str:
        """Execute margin/markup calculation."""
        try:
            parts = input_str.strip().split()
            if len(parts) < 3:
                return "Blad: Podaj operacje i wartosci (np. 'margin 80 100')"

            operation = parts[0].lower()
            val1 = Decimal(parts[1].replace(",", "."))
            val2 = Decimal(parts[2].replace(",", ".").replace("%", ""))

            if operation == "margin":
                # Margin = (Price - Cost) / Price * 100
                cost, price = val1, val2
                if price == 0:
                    return "Blad: Cena nie moze byc zero"
                margin = ((price - cost) / price * 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
                profit = price - cost
                return (
                    f"MARZA:\n"
                    f"Koszt: {cost:.2f} PLN\n"
                    f"Cena sprzedazy: {price:.2f} PLN\n"
                    f"Zysk: {profit:.2f} PLN\n"
                    f"Marza: {margin:.2f}%"
                )

            elif operation == "markup":
                # Markup = (Price - Cost) / Cost * 100
                cost, price = val1, val2
                if cost == 0:
                    return "Blad: Koszt nie moze byc zero"
                markup = ((price - cost) / cost * 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
                profit = price - cost
                return (
                    f"NARZUT:\n"
                    f"Koszt: {cost:.2f} PLN\n"
                    f"Cena sprzedazy: {price:.2f} PLN\n"
                    f"Zysk: {profit:.2f} PLN\n"
                    f"Narzut: {markup:.2f}%"
                )

            elif operation in ["price_from_margin", "cena_z_marzy"]:
                # Price = Cost / (1 - Margin)
                cost = val1
                margin_pct = val2 / 100
                if margin_pct >= 1:
                    return "Blad: Marza nie moze byc >= 100%"
                price = (cost / (1 - margin_pct)).quantize(Decimal("0.01"), ROUND_HALF_UP)
                profit = price - cost
                return (
                    f"CENA Z MARZY:\n"
                    f"Koszt: {cost:.2f} PLN\n"
                    f"Docelowa marza: {val2:.2f}%\n"
                    f"Cena sprzedazy: {price:.2f} PLN\n"
                    f"Zysk: {profit:.2f} PLN"
                )

            elif operation in ["price_from_markup", "cena_z_narzutu"]:
                # Price = Cost * (1 + Markup)
                cost = val1
                markup_pct = val2 / 100
                price = (cost * (1 + markup_pct)).quantize(Decimal("0.01"), ROUND_HALF_UP)
                profit = price - cost
                return (
                    f"CENA Z NARZUTU:\n"
                    f"Koszt: {cost:.2f} PLN\n"
                    f"Narzut: {val2:.2f}%\n"
                    f"Cena sprzedazy: {price:.2f} PLN\n"
                    f"Zysk: {profit:.2f} PLN"
                )

            elif operation in ["profit", "zysk"]:
                cost, price = val1, val2
                profit = price - cost
                margin = ((profit / price) * 100).quantize(Decimal("0.01"), ROUND_HALF_UP) if price else Decimal(0)
                return (
                    f"ZYSK:\n"
                    f"Koszt: {cost:.2f} PLN\n"
                    f"Cena sprzedazy: {price:.2f} PLN\n"
                    f"Zysk: {profit:.2f} PLN\n"
                    f"Marza: {margin:.2f}%"
                )

            else:
                return (
                    f"Nieznana operacja: {operation}\n"
                    f"Dostepne: margin, markup, price_from_margin, price_from_markup, profit"
                )

        except Exception as e:
            return f"Blad obliczenia: {e!s}"


class PercentageCalculatorTool(BaseTool):
    """Tool for percentage calculations."""

    name: str = "percentage_calculator"
    description: str = """Kalkulator procentow.
    Uzyj tego narzedzia do:
    - Obliczenia procentu z liczby
    - Obliczenia jaki procent stanowi jedna liczba wzgledem drugiej
    - Obliczenia zmiany procentowej
    - Dodania/odjecia procentu

    Input format: 'operacja wartosc1 wartosc2'
    Przyklady:
    - 'percent_of 20 500' -> 20% z 500 = 100
    - 'what_percent 100 500' -> jaki procent 100 stanowi z 500 = 20%
    - 'change 500 600' -> zmiana procentowa z 500 na 600 = +20%
    - 'add_percent 500 20' -> 500 + 20% = 600
    - 'subtract_percent 600 20' -> 600 - 20% = 480"""

    def _run(self, input_str: str) -> str:
        """Execute percentage calculation."""
        try:
            parts = input_str.strip().split()
            if len(parts) < 3:
                return "Blad: Podaj operacje i wartosci (np. 'percent_of 20 500')"

            operation = parts[0].lower()
            val1 = Decimal(parts[1].replace(",", ".").replace("%", ""))
            val2 = Decimal(parts[2].replace(",", ".").replace("%", ""))

            if operation in ["percent_of", "procent_z"]:
                # X% of Y
                result = (val1 / 100 * val2).quantize(Decimal("0.01"), ROUND_HALF_UP)
                return f"{val1}% z {val2} = {result}"

            elif operation in ["what_percent", "jaki_procent"]:
                # X is what percent of Y
                if val2 == 0:
                    return "Blad: Nie mozna dzielic przez zero"
                result = (val1 / val2 * 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
                return f"{val1} stanowi {result}% z {val2}"

            elif operation in ["change", "zmiana"]:
                # Percentage change from X to Y
                if val1 == 0:
                    return "Blad: Wartosc poczatkowa nie moze byc zero"
                change = ((val2 - val1) / val1 * 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
                sign = "+" if change > 0 else ""
                return (
                    f"ZMIANA PROCENTOWA:\n"
                    f"Z: {val1}\n"
                    f"Na: {val2}\n"
                    f"Zmiana: {sign}{change}%"
                )

            elif operation in ["add_percent", "dodaj_procent"]:
                # X + Y%
                addition = (val1 * val2 / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
                result = val1 + addition
                return f"{val1} + {val2}% = {result} (dodano: {addition})"

            elif operation in ["subtract_percent", "odejmij_procent"]:
                # X - Y%
                subtraction = (val1 * val2 / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
                result = val1 - subtraction
                return f"{val1} - {val2}% = {result} (odjeto: {subtraction})"

            else:
                return (
                    f"Nieznana operacja: {operation}\n"
                    f"Dostepne: percent_of, what_percent, change, add_percent, subtract_percent"
                )

        except Exception as e:
            return f"Blad obliczenia: {e!s}"


class CashflowCalculatorTool(BaseTool):
    """Tool for cashflow and financial projections."""

    name: str = "cashflow_calculator"
    description: str = """Kalkulator cashflow i projekcji finansowych.
    Uzyj tego narzedzia do:
    - Obliczenia salda cashflow
    - Projekcji przychodow/wydatkow
    - Obliczenia break-even

    Input format: 'operacja parametry...'
    Przyklady:
    - 'balance 10000 8000' -> saldo (przychody 10000, wydatki 8000)
    - 'projection 5000 10' -> 5000/msc przez 10 miesiecy
    - 'break_even 10000 500' -> break-even (koszty stale 10000, zysk/szt 500)
    - 'runway 50000 8000' -> ile miesiecy przy 50000 kapitalu i 8000 wydatkow/msc"""

    def _run(self, input_str: str) -> str:
        """Execute cashflow calculation."""
        try:
            parts = input_str.strip().split()
            if len(parts) < 3:
                return "Blad: Podaj operacje i parametry"

            operation = parts[0].lower()
            val1 = Decimal(parts[1].replace(",", "."))
            val2 = Decimal(parts[2].replace(",", "."))

            if operation in ["balance", "saldo"]:
                income, expenses = val1, val2
                balance = income - expenses
                sign = "+" if balance >= 0 else ""
                status = "DODATNIE" if balance >= 0 else "UJEMNE"
                return (
                    f"SALDO CASHFLOW:\n"
                    f"Przychody: {income:.2f} PLN\n"
                    f"Wydatki: {expenses:.2f} PLN\n"
                    f"Saldo: {sign}{balance:.2f} PLN ({status})"
                )

            elif operation in ["projection", "projekcja"]:
                monthly = val1
                months = int(val2)
                total = monthly * months
                return (
                    f"PROJEKCJA:\n"
                    f"Kwota miesieczna: {monthly:.2f} PLN\n"
                    f"Liczba miesiecy: {months}\n"
                    f"Suma: {total:.2f} PLN"
                )

            elif operation in ["break_even", "prog_rentownosci"]:
                fixed_costs = val1
                profit_per_unit = val2
                if profit_per_unit <= 0:
                    return "Blad: Zysk na jednostce musi byc dodatni"
                units = (fixed_costs / profit_per_unit).quantize(Decimal("1"), ROUND_HALF_UP)
                return (
                    f"PROG RENTOWNOSCI (Break-Even):\n"
                    f"Koszty stale: {fixed_costs:.2f} PLN\n"
                    f"Zysk na jednostce: {profit_per_unit:.2f} PLN\n"
                    f"Wymagana sprzedaz: {units} jednostek"
                )

            elif operation in ["runway", "przezywalnosc"]:
                capital = val1
                monthly_burn = val2
                if monthly_burn <= 0:
                    return "Blad: Miesie czne wydatki musza byc dodatnie"
                months = int(capital / monthly_burn)
                remaining = capital - (months * monthly_burn)
                return (
                    f"RUNWAY (Przezywalnosc):\n"
                    f"Kapital: {capital:.2f} PLN\n"
                    f"Miesieczne wydatki: {monthly_burn:.2f} PLN\n"
                    f"Wystarczy na: {months} miesiecy\n"
                    f"Pozostanie: {remaining:.2f} PLN"
                )

            else:
                return (
                    f"Nieznana operacja: {operation}\n"
                    f"Dostepne: balance, projection, break_even, runway"
                )

        except Exception as e:
            return f"Blad obliczenia: {e!s}"


class GeneralCalculatorTool(BaseTool):
    """General-purpose calculator for simple math expressions."""

    name: str = "calculator"
    description: str = """Prosty kalkulator do podstawowych obliczen matematycznych.
    Uzyj tego narzedzia do:
    - Dodawania, odejmowania, mnozenia, dzielenia
    - Podstawowych wyrazen matematycznych

    Input: wyrazenie matematyczne
    Przyklady:
    - '1000 + 500'
    - '2500 * 1.23'
    - '(1000 + 500) * 0.23'
    - '10000 / 12'"""

    # Allowed characters in expressions for safety
    ALLOWED_PATTERN = re.compile(r'^[\d\s\+\-\*\/\.\,\(\)]+$')

    def _run(self, expression: str) -> str:
        """Execute safe mathematical calculation."""
        try:
            # Normalize input
            expr = expression.replace(",", ".").strip()

            # Security check - only allow numbers and basic operators
            if not self.ALLOWED_PATTERN.match(expr):
                return "Blad: Niedozwolone znaki w wyrazeniu. Uzywaj tylko liczb i operatorow +, -, *, /, (, )"

            # Evaluate the expression safely
            result = eval(expr, {"__builtins__": {}}, {})

            # Format result
            if isinstance(result, float):
                result = Decimal(str(result)).quantize(Decimal("0.01"), ROUND_HALF_UP)

            return f"Wynik: {expression} = {result}"

        except ZeroDivisionError:
            return "Blad: Dzielenie przez zero"
        except Exception as e:
            return f"Blad obliczenia: {e!s}"


# Factory functions
def get_calculator_tools() -> list[BaseTool]:
    """Get all calculator tools for agents."""
    return [
        VATCalculatorTool(),
        MarginCalculatorTool(),
        PercentageCalculatorTool(),
        CashflowCalculatorTool(),
        GeneralCalculatorTool(),
    ]


def get_vat_calculator() -> BaseTool:
    """Get VAT calculator tool."""
    return VATCalculatorTool()


def get_finance_calculator_tools() -> list[BaseTool]:
    """Get calculator tools specifically for finance agents."""
    return [
        VATCalculatorTool(),
        MarginCalculatorTool(),
        CashflowCalculatorTool(),
        GeneralCalculatorTool(),
    ]


# Convenience instances
vat_calculator = VATCalculatorTool()
margin_calculator = MarginCalculatorTool()
percentage_calculator = PercentageCalculatorTool()
cashflow_calculator = CashflowCalculatorTool()
general_calculator = GeneralCalculatorTool()
