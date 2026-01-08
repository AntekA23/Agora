"""Validators tool for AI agents.

Provides validation capabilities for Polish business identifiers:
- NIP (Numer Identyfikacji Podatkowej) - Tax ID
- REGON (Rejestr Gospodarki Narodowej) - Business Registry Number
- IBAN - International Bank Account Number (Polish format)
- PESEL - Personal ID number
- Email validation
- Phone number validation (Polish format)
"""

import re
from typing import ClassVar, Literal, Pattern

from crewai.tools import BaseTool
from pydantic import Field


class NIPValidatorTool(BaseTool):
    """Tool for validating Polish NIP (Tax Identification Number)."""

    name: str = "nip_validator"
    description: str = """Waliduje polski numer NIP (Numer Identyfikacji Podatkowej).
    NIP sklada sie z 10 cyfr z suma kontrolna.

    Input: numer NIP (moze zawierac myslniki, spacje)
    Przyklady poprawnych formatow:
    - '1234567890'
    - '123-456-78-90'
    - '123 456 78 90'

    Zwraca informacje czy NIP jest poprawny oraz sformatowany numer."""

    # NIP weights for checksum
    NIP_WEIGHTS: ClassVar[list[int]] = [6, 5, 7, 2, 3, 4, 5, 6, 7]

    def _run(self, nip: str) -> str:
        """Validate NIP number."""
        # Remove non-digits
        clean_nip = re.sub(r'\D', '', nip.strip())

        # Check length
        if len(clean_nip) != 10:
            return (
                f"NIEPOPRAWNY NIP: '{nip}'\n"
                f"Powod: NIP musi miec 10 cyfr (podano {len(clean_nip)} cyfr)"
            )

        # Calculate checksum
        try:
            digits = [int(d) for d in clean_nip]
            checksum = sum(w * d for w, d in zip(self.NIP_WEIGHTS, digits[:9])) % 11

            if checksum != digits[9]:
                return (
                    f"NIEPOPRAWNY NIP: '{nip}'\n"
                    f"Powod: Niepoprawna suma kontrolna"
                )

            # Format nicely
            formatted = f"{clean_nip[:3]}-{clean_nip[3:6]}-{clean_nip[6:8]}-{clean_nip[8:]}"

            return (
                f"POPRAWNY NIP: {formatted}\n"
                f"Numer: {clean_nip}\n"
                f"Status: Prawidlowy format i suma kontrolna"
            )

        except Exception as e:
            return f"Blad walidacji NIP: {e!s}"


class REGONValidatorTool(BaseTool):
    """Tool for validating Polish REGON (Business Registry Number)."""

    name: str = "regon_validator"
    description: str = """Waliduje polski numer REGON (numer rejestru gospodarki narodowej).
    REGON moze miec 9 cyfr (podstawowy) lub 14 cyfr (rozszerzony).

    Input: numer REGON
    Przyklady:
    - '123456789' (9-cyfrowy)
    - '12345678912345' (14-cyfrowy)

    Zwraca informacje czy REGON jest poprawny."""

    # REGON weights
    REGON9_WEIGHTS: ClassVar[list[int]] = [8, 9, 2, 3, 4, 5, 6, 7]
    REGON14_WEIGHTS: ClassVar[list[int]] = [2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8]

    def _run(self, regon: str) -> str:
        """Validate REGON number."""
        # Remove non-digits
        clean_regon = re.sub(r'\D', '', regon.strip())

        # Check length (9 or 14)
        if len(clean_regon) not in [9, 14]:
            return (
                f"NIEPOPRAWNY REGON: '{regon}'\n"
                f"Powod: REGON musi miec 9 lub 14 cyfr (podano {len(clean_regon)} cyfr)"
            )

        try:
            digits = [int(d) for d in clean_regon]

            if len(clean_regon) == 9:
                # Validate 9-digit REGON
                checksum = sum(w * d for w, d in zip(self.REGON9_WEIGHTS, digits[:8])) % 11
                checksum = 0 if checksum == 10 else checksum

                if checksum != digits[8]:
                    return (
                        f"NIEPOPRAWNY REGON: '{regon}'\n"
                        f"Powod: Niepoprawna suma kontrolna"
                    )

                return (
                    f"POPRAWNY REGON (9-cyfrowy): {clean_regon}\n"
                    f"Typ: Podstawowy numer REGON\n"
                    f"Status: Prawidlowy format i suma kontrolna"
                )

            else:
                # Validate 14-digit REGON (first validate 9-digit part)
                checksum9 = sum(w * d for w, d in zip(self.REGON9_WEIGHTS, digits[:8])) % 11
                checksum9 = 0 if checksum9 == 10 else checksum9

                if checksum9 != digits[8]:
                    return (
                        f"NIEPOPRAWNY REGON: '{regon}'\n"
                        f"Powod: Niepoprawna suma kontrolna czesci podstawowej"
                    )

                # Validate full 14-digit
                checksum14 = sum(w * d for w, d in zip(self.REGON14_WEIGHTS, digits[:13])) % 11
                checksum14 = 0 if checksum14 == 10 else checksum14

                if checksum14 != digits[13]:
                    return (
                        f"NIEPOPRAWNY REGON: '{regon}'\n"
                        f"Powod: Niepoprawna suma kontrolna czesci rozszerzonej"
                    )

                return (
                    f"POPRAWNY REGON (14-cyfrowy): {clean_regon}\n"
                    f"REGON podstawowy: {clean_regon[:9]}\n"
                    f"Numer jednostki lokalnej: {clean_regon[9:]}\n"
                    f"Status: Prawidlowy format i suma kontrolna"
                )

        except Exception as e:
            return f"Blad walidacji REGON: {e!s}"


class IBANValidatorTool(BaseTool):
    """Tool for validating IBAN (especially Polish bank accounts)."""

    name: str = "iban_validator"
    description: str = """Waliduje numer IBAN (miedzynarodowy numer konta bankowego).
    Polski IBAN ma format: PL + 26 cyfr (lub 26 cyfr bez PL).

    Input: numer IBAN
    Przyklady:
    - 'PL61109010140000071219812874'
    - '61 1090 1014 0000 0712 1981 2874'
    - '61109010140000071219812874'

    Zwraca informacje czy IBAN jest poprawny oraz kod banku."""

    # Polish bank codes (first 3 digits after country code)
    POLISH_BANKS: ClassVar[dict[str, str]] = {
        "102": "PKO BP",
        "103": "Bank Handlowy (Citi)",
        "105": "ING Bank Slaski",
        "109": "Santander Bank Polska",
        "113": "BNP Paribas",
        "114": "mBank",
        "116": "Bank Millennium",
        "124": "Pekao SA",
        "132": "Bank Pocztowy",
        "147": "Credit Agricole",
        "154": "BOŚ Bank",
        "158": "Mercedes-Benz Bank",
        "161": "SGB-Bank",
        "175": "Raiffeisen Bank",
        "193": "Bank Polskiej Spółdzielczości",
        "194": "Krakowski Bank Spółdzielczy",
        "212": "Nest Bank",
        "247": "VeloBank (dawniej Getin)",
        "249": "Alior Bank",
    }

    def _run(self, iban: str) -> str:
        """Validate IBAN number."""
        # Normalize: remove spaces, dashes, convert to uppercase
        clean_iban = re.sub(r'[\s\-]', '', iban.strip().upper())

        # Add PL prefix if not present and looks like Polish account
        if len(clean_iban) == 26 and clean_iban.isdigit():
            clean_iban = "PL" + clean_iban

        # Check country code for Polish IBAN
        country_code = clean_iban[:2]
        is_polish = country_code == "PL"

        # Check length (Polish IBAN = 28 chars total)
        expected_length = 28 if is_polish else None
        if is_polish and len(clean_iban) != 28:
            return (
                f"NIEPOPRAWNY IBAN: '{iban}'\n"
                f"Powod: Polski IBAN musi miec 28 znakow (PL + 26 cyfr)\n"
                f"Podano: {len(clean_iban)} znakow"
            )

        # Check format (country code + digits)
        if not re.match(r'^[A-Z]{2}[0-9]+$', clean_iban):
            return (
                f"NIEPOPRAWNY IBAN: '{iban}'\n"
                f"Powod: IBAN musi zaczynac sie od 2 liter kodu kraju, po ktorych nastepuja cyfry"
            )

        # Validate checksum using mod-97 algorithm
        try:
            # Move first 4 chars to end
            rearranged = clean_iban[4:] + clean_iban[:4]

            # Convert letters to numbers (A=10, B=11, ... Z=35)
            numeric = ""
            for char in rearranged:
                if char.isdigit():
                    numeric += char
                else:
                    numeric += str(ord(char) - ord('A') + 10)

            # Check mod 97
            if int(numeric) % 97 != 1:
                return (
                    f"NIEPOPRAWNY IBAN: '{iban}'\n"
                    f"Powod: Niepoprawna suma kontrolna (mod-97)"
                )

            # Format output
            formatted = ' '.join([clean_iban[i:i+4] for i in range(0, len(clean_iban), 4)])

            result = f"POPRAWNY IBAN: {formatted}\n"
            result += f"Kod kraju: {country_code}\n"

            # Add bank info for Polish accounts
            if is_polish:
                bank_code = clean_iban[4:7]
                bank_name = self.POLISH_BANKS.get(bank_code, "Nieznany bank")
                result += f"Kod banku: {bank_code} ({bank_name})\n"
                result += f"Numer rozliczeniowy: {clean_iban[4:12]}\n"
                result += f"Numer konta: {clean_iban[12:]}\n"

            result += "Status: Prawidlowy format i suma kontrolna"
            return result

        except Exception as e:
            return f"Blad walidacji IBAN: {e!s}"


class PESELValidatorTool(BaseTool):
    """Tool for validating Polish PESEL (Personal ID Number)."""

    name: str = "pesel_validator"
    description: str = """Waliduje polski numer PESEL (Powszechny Elektroniczny System Ewidencji Ludnosci).
    PESEL sklada sie z 11 cyfr i zawiera date urodzenia oraz plec.

    Input: numer PESEL (11 cyfr)

    Zwraca informacje czy PESEL jest poprawny, date urodzenia i plec."""

    PESEL_WEIGHTS: ClassVar[list[int]] = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]

    def _run(self, pesel: str) -> str:
        """Validate PESEL number."""
        # Remove non-digits
        clean_pesel = re.sub(r'\D', '', pesel.strip())

        # Check length
        if len(clean_pesel) != 11:
            return (
                f"NIEPOPRAWNY PESEL: '{pesel}'\n"
                f"Powod: PESEL musi miec 11 cyfr (podano {len(clean_pesel)} cyfr)"
            )

        try:
            digits = [int(d) for d in clean_pesel]

            # Calculate checksum
            checksum = sum(w * d for w, d in zip(self.PESEL_WEIGHTS, digits[:10])) % 10
            control = (10 - checksum) % 10

            if control != digits[10]:
                return (
                    f"NIEPOPRAWNY PESEL: '{pesel}'\n"
                    f"Powod: Niepoprawna suma kontrolna"
                )

            # Extract birth date
            year = int(clean_pesel[0:2])
            month = int(clean_pesel[2:4])
            day = int(clean_pesel[4:6])

            # Determine century from month encoding
            if month > 80:
                year += 1800
                month -= 80
            elif month > 60:
                year += 2200
                month -= 60
            elif month > 40:
                year += 2100
                month -= 40
            elif month > 20:
                year += 2000
                month -= 20
            else:
                year += 1900

            birth_date = f"{day:02d}.{month:02d}.{year}"

            # Determine gender (10th digit: even = female, odd = male)
            gender = "Mezczyzna" if digits[9] % 2 == 1 else "Kobieta"

            return (
                f"POPRAWNY PESEL: {clean_pesel}\n"
                f"Data urodzenia: {birth_date}\n"
                f"Plec: {gender}\n"
                f"Status: Prawidlowy format i suma kontrolna"
            )

        except Exception as e:
            return f"Blad walidacji PESEL: {e!s}"


class EmailValidatorTool(BaseTool):
    """Tool for validating email addresses."""

    name: str = "email_validator"
    description: str = """Waliduje adres email.

    Input: adres email

    Sprawdza poprawnosc formatu adresu email."""

    # Email regex pattern (simplified but effective)
    EMAIL_PATTERN: ClassVar[Pattern[str]] = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    def _run(self, email: str) -> str:
        """Validate email address."""
        clean_email = email.strip().lower()

        if not clean_email:
            return "NIEPOPRAWNY EMAIL: Pusty adres"

        if not self.EMAIL_PATTERN.match(clean_email):
            # Provide specific feedback
            if '@' not in clean_email:
                reason = "Brak znaku @"
            elif clean_email.count('@') > 1:
                reason = "Za duzo znakow @"
            elif '.' not in clean_email.split('@')[1]:
                reason = "Brak domeny (np. .pl, .com)"
            else:
                reason = "Niepoprawny format"

            return f"NIEPOPRAWNY EMAIL: '{email}'\nPowod: {reason}"

        # Extract parts
        local_part, domain = clean_email.split('@')

        return (
            f"POPRAWNY EMAIL: {clean_email}\n"
            f"Czesc lokalna: {local_part}\n"
            f"Domena: {domain}\n"
            f"Status: Prawidlowy format"
        )


class PhoneValidatorTool(BaseTool):
    """Tool for validating Polish phone numbers."""

    name: str = "phone_validator"
    description: str = """Waliduje polski numer telefonu.

    Akceptowane formaty:
    - +48 123 456 789
    - 48 123456789
    - 123 456 789
    - 123456789

    Zwraca sformatowany numer telefonu."""

    def _run(self, phone: str) -> str:
        """Validate Polish phone number."""
        # Remove all non-digits except leading +
        clean = phone.strip()
        has_plus = clean.startswith('+')
        digits = re.sub(r'\D', '', clean)

        # Remove country code if present
        if digits.startswith('48') and len(digits) == 11:
            digits = digits[2:]
        elif digits.startswith('0048') and len(digits) == 13:
            digits = digits[4:]

        # Check length (Polish mobile/landline = 9 digits)
        if len(digits) != 9:
            return (
                f"NIEPOPRAWNY NUMER: '{phone}'\n"
                f"Powod: Polski numer telefonu musi miec 9 cyfr (podano {len(digits)} cyfr)"
            )

        # Determine type based on first digit
        first_digit = digits[0]
        if first_digit in ['4', '5', '6', '7', '8']:
            phone_type = "Komorkowy"
        elif first_digit in ['1', '2', '3']:
            phone_type = "Stacjonarny"
        else:
            phone_type = "Nieznany typ"

        # Format nicely
        formatted = f"+48 {digits[:3]} {digits[3:6]} {digits[6:]}"
        formatted_compact = f"+48{digits}"

        return (
            f"POPRAWNY NUMER: {formatted}\n"
            f"Format kompaktowy: {formatted_compact}\n"
            f"Typ: {phone_type}\n"
            f"Status: Prawidlowy format"
        )


class UniversalValidatorTool(BaseTool):
    """Universal validator that auto-detects the type of identifier."""

    name: str = "validator"
    description: str = """Uniwersalny walidator - automatycznie wykrywa typ identyfikatora.
    Obsluguje: NIP, REGON, IBAN, PESEL, email, telefon.

    Input: dowolny identyfikator do walidacji
    Przyklady:
    - '1234567890' -> wykryje NIP
    - 'PL61109010140000071219812874' -> wykryje IBAN
    - 'jan.kowalski@firma.pl' -> wykryje email
    - '+48 123 456 789' -> wykryje telefon"""

    def _run(self, value: str) -> str:
        """Auto-detect and validate identifier."""
        clean = value.strip()
        digits_only = re.sub(r'\D', '', clean)

        # Try to detect type
        if '@' in clean:
            return EmailValidatorTool()._run(clean)

        if clean.upper().startswith('PL') or (len(digits_only) == 26):
            return IBANValidatorTool()._run(clean)

        if clean.startswith('+') or (len(digits_only) == 9 and digits_only[0] in '456789'):
            return PhoneValidatorTool()._run(clean)

        if len(digits_only) == 10:
            return NIPValidatorTool()._run(clean)

        if len(digits_only) == 11:
            return PESELValidatorTool()._run(clean)

        if len(digits_only) in [9, 14]:
            return REGONValidatorTool()._run(clean)

        return (
            f"NIE ROZPOZNANO TYPU: '{value}'\n"
            f"Podpowiedz: Uzywaj konkretnych walidatorow:\n"
            f"- nip_validator dla NIP\n"
            f"- regon_validator dla REGON\n"
            f"- iban_validator dla IBAN\n"
            f"- pesel_validator dla PESEL\n"
            f"- email_validator dla email\n"
            f"- phone_validator dla telefonu"
        )


# Factory functions
def get_validator_tools() -> list[BaseTool]:
    """Get all validator tools for agents."""
    return [
        UniversalValidatorTool(),
        NIPValidatorTool(),
        REGONValidatorTool(),
        IBANValidatorTool(),
        PESELValidatorTool(),
        EmailValidatorTool(),
        PhoneValidatorTool(),
    ]


def get_business_validators() -> list[BaseTool]:
    """Get validators for business identifiers."""
    return [
        NIPValidatorTool(),
        REGONValidatorTool(),
        IBANValidatorTool(),
    ]


def get_contact_validators() -> list[BaseTool]:
    """Get validators for contact information."""
    return [
        EmailValidatorTool(),
        PhoneValidatorTool(),
    ]


# Convenience instances
universal_validator = UniversalValidatorTool()
nip_validator = NIPValidatorTool()
regon_validator = REGONValidatorTool()
iban_validator = IBANValidatorTool()
pesel_validator = PESELValidatorTool()
email_validator = EmailValidatorTool()
phone_validator = PhoneValidatorTool()
