from dataclasses import dataclass

@dataclass(slots=True)
class UserProfile:

    name: str

    telegram_id: int

    cities: list[str]

    min_salary: int | None

    required_visas: list[str]

    keywords: list[str]
