"""Seasonal context builder for AI agents.

Provides awareness of current date, season, upcoming holidays,
and seasonal suggestions for content creation.
"""

from datetime import datetime, timedelta
from typing import TypedDict


class SeasonalContext(TypedDict):
    """Seasonal context data structure."""
    current_date: str
    day_of_week: str
    season: str
    season_pl: str
    upcoming_holidays: list[dict[str, str]]
    seasonal_themes: list[str]
    weather_context: str


# Polish holidays and important dates
POLISH_HOLIDAYS = [
    # Stale swieta
    {"month": 1, "day": 1, "name": "Nowy Rok", "type": "holiday"},
    {"month": 1, "day": 6, "name": "Trzech Kroli", "type": "holiday"},
    {"month": 2, "day": 14, "name": "Walentynki", "type": "commercial"},
    {"month": 3, "day": 8, "name": "Dzien Kobiet", "type": "commercial"},
    {"month": 3, "day": 20, "name": "Pierwszy dzien wiosny", "type": "seasonal"},
    {"month": 5, "day": 1, "name": "Swieto Pracy", "type": "holiday"},
    {"month": 5, "day": 3, "name": "Swieto Konstytucji", "type": "holiday"},
    {"month": 5, "day": 26, "name": "Dzien Matki", "type": "commercial"},
    {"month": 6, "day": 1, "name": "Dzien Dziecka", "type": "commercial"},
    {"month": 6, "day": 21, "name": "Pierwszy dzien lata", "type": "seasonal"},
    {"month": 6, "day": 23, "name": "Dzien Ojca", "type": "commercial"},
    {"month": 8, "day": 15, "name": "Wniebowziecie NMP", "type": "holiday"},
    {"month": 9, "day": 1, "name": "Poczatek roku szkolnego", "type": "seasonal"},
    {"month": 9, "day": 23, "name": "Pierwszy dzien jesieni", "type": "seasonal"},
    {"month": 10, "day": 14, "name": "Dzien Nauczyciela", "type": "commercial"},
    {"month": 10, "day": 31, "name": "Halloween", "type": "commercial"},
    {"month": 11, "day": 1, "name": "Wszystkich Swietych", "type": "holiday"},
    {"month": 11, "day": 11, "name": "Swieto Niepodleglosci", "type": "holiday"},
    {"month": 11, "day": 29, "name": "Black Friday", "type": "commercial"},  # Approximate
    {"month": 12, "day": 6, "name": "Mikolajki", "type": "commercial"},
    {"month": 12, "day": 21, "name": "Pierwszy dzien zimy", "type": "seasonal"},
    {"month": 12, "day": 24, "name": "Wigilia", "type": "holiday"},
    {"month": 12, "day": 25, "name": "Boze Narodzenie", "type": "holiday"},
    {"month": 12, "day": 26, "name": "Drugi dzien swiat", "type": "holiday"},
    {"month": 12, "day": 31, "name": "Sylwester", "type": "holiday"},
]

# Seasonal themes and suggestions
SEASON_THEMES = {
    "winter": {
        "pl": "zima",
        "themes": [
            "cieplo i przytulnosc",
            "gorace napoje",
            "zimowe promocje",
            "swiateczny klimat",
            "noworoczne postanowienia",
            "ferie zimowe",
            "walentynki (luty)",
        ],
        "weather": "zimna pogoda, snieg, mrozy",
        "colors": "biel, srebro, granat, bordo",
        "mood": "przytulny, ciepły, swiateczny",
    },
    "spring": {
        "pl": "wiosna",
        "themes": [
            "nowy poczatek",
            "swiezosc i energia",
            "wiosenne porządki",
            "wielkanoc",
            "dzien kobiet",
            "dzien matki",
            "majowka",
            "koniec roku szkolnego",
        ],
        "weather": "ocieplenie, deszcze, kwitnienie",
        "colors": "pastelowe, zielen, zolty, rozowy",
        "mood": "optymistyczny, energiczny, swiezy",
    },
    "summer": {
        "pl": "lato",
        "themes": [
            "wakacje i odpoczynek",
            "letnie promocje",
            "oswiezenie",
            "podroze",
            "dzien dziecka",
            "dzien ojca",
            "festiwale i eventy",
            "sezon grillowy",
        ],
        "weather": "upaly, slonce, ciepłe wieczory",
        "colors": "zolty, pomaranczowy, turkus, biel",
        "mood": "radosny, beztroski, energiczny",
    },
    "autumn": {
        "pl": "jesien",
        "themes": [
            "powrot do szkoly",
            "jesienne nowosci",
            "halloween",
            "black friday",
            "przygotowania do swiat",
            "dzien nauczyciela",
            "comfort food",
            "dynie i jesienna estetyka",
        ],
        "weather": "chlodniej, deszcze, kolorowe liscie",
        "colors": "pomaranczowy, brazowy, bordowy, zloty",
        "mood": "nostalgiczny, przytulny, refleksyjny",
    },
}

DAYS_OF_WEEK_PL = {
    0: "poniedzialek",
    1: "wtorek",
    2: "sroda",
    3: "czwartek",
    4: "piatek",
    5: "sobota",
    6: "niedziela",
}

MONTHS_PL = {
    1: "styczen",
    2: "luty",
    3: "marzec",
    4: "kwiecien",
    5: "maj",
    6: "czerwiec",
    7: "lipiec",
    8: "sierpien",
    9: "wrzesien",
    10: "pazdziernik",
    11: "listopad",
    12: "grudzien",
}


def get_season(date: datetime) -> str:
    """Determine the season based on date."""
    month = date.month
    day = date.day

    # Astronomical seasons (approximate)
    if (month == 12 and day >= 21) or month in [1, 2] or (month == 3 and day < 20):
        return "winter"
    elif (month == 3 and day >= 20) or month in [4, 5] or (month == 6 and day < 21):
        return "spring"
    elif (month == 6 and day >= 21) or month in [7, 8] or (month == 9 and day < 23):
        return "summer"
    else:
        return "autumn"


def get_upcoming_holidays(date: datetime, days_ahead: int = 30) -> list[dict[str, str]]:
    """Get holidays coming up in the next N days."""
    upcoming = []
    current_year = date.year

    for holiday in POLISH_HOLIDAYS:
        # Check this year and next year (for year-end)
        for year in [current_year, current_year + 1]:
            try:
                holiday_date = datetime(year, holiday["month"], holiday["day"])
                days_until = (holiday_date - date).days

                if 0 <= days_until <= days_ahead:
                    upcoming.append({
                        "name": holiday["name"],
                        "date": holiday_date.strftime("%d.%m"),
                        "days_until": days_until,
                        "type": holiday["type"],
                    })
            except ValueError:
                # Invalid date (e.g., Feb 30)
                continue

    # Sort by days until
    upcoming.sort(key=lambda x: x["days_until"])
    return upcoming[:5]  # Max 5 upcoming holidays


def build_seasonal_context(date: datetime | None = None) -> str:
    """Build seasonal context string for AI agents.

    Args:
        date: Optional date to use. Defaults to current date.

    Returns:
        Formatted context string with seasonal information.
    """
    if date is None:
        date = datetime.now()

    season = get_season(date)
    season_data = SEASON_THEMES[season]
    upcoming = get_upcoming_holidays(date)

    day_name = DAYS_OF_WEEK_PL[date.weekday()]
    month_name = MONTHS_PL[date.month]

    lines = [
        "=== KONTEKST CZASOWY ===",
        f"Dzisiejsza data: {date.day} {month_name} {date.year} ({day_name})",
        f"Pora roku: {season_data['pl']}",
        f"Pogoda/klimat: {season_data['weather']}",
        f"Nastroj sezonu: {season_data['mood']}",
        f"Kolory sezonu: {season_data['colors']}",
    ]

    if upcoming:
        lines.append("")
        lines.append("Nadchodzace okazje:")
        for h in upcoming:
            days_text = "dzis" if h["days_until"] == 0 else f"za {h['days_until']} dni"
            lines.append(f"- {h['name']} ({h['date']}) - {days_text}")

    lines.append("")
    lines.append("Sezonowe tematy do wykorzystania:")
    for theme in season_data["themes"][:5]:
        lines.append(f"- {theme}")

    lines.append("")
    lines.append("WAZNE: Dostosuj tresc do aktualnej pory roku i nadchodzacych wydarzen!")

    return "\n".join(lines)


def get_seasonal_context_data(date: datetime | None = None) -> SeasonalContext:
    """Get seasonal context as structured data.

    Args:
        date: Optional date to use. Defaults to current date.

    Returns:
        SeasonalContext dictionary with all seasonal data.
    """
    if date is None:
        date = datetime.now()

    season = get_season(date)
    season_data = SEASON_THEMES[season]

    return SeasonalContext(
        current_date=date.strftime("%Y-%m-%d"),
        day_of_week=DAYS_OF_WEEK_PL[date.weekday()],
        season=season,
        season_pl=season_data["pl"],
        upcoming_holidays=get_upcoming_holidays(date),
        seasonal_themes=season_data["themes"],
        weather_context=season_data["weather"],
    )
