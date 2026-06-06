"""
LWK - Look Work in Korea

Korect/KoWork collector v0.1

Назначение:
    - получить последние вакансии из API
    - преобразовать их в объекты JobDto
    - вывести результат в консоль

Без БД.
Без Telegram.
Без OpenAI.
=====
TB moved to LWK/__main__.py
for Imports use syntax like -- from lwk.services.job_matcher import Foo
"""
from bs4 import BeautifulSoup

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# from pathlib import Path
#from lwk.scrapers.korect_seen_jobs import SeenJobsStore

import requests  # type: ignore
# import json
#from lwk.services.job_matcher import JobMatcher
#from lwk.models.user_profile import UserProfile

API_URL = "https://korect.kr/api/v1/jobs"


@dataclass(slots=True)
class JobDto:
    external_id: str

    title: str
    description: str

    #city: Optional[str]
    location: Optional[str]
    city_ru: Optional[str]
    city_ko: Optional[str]
    city_en: Optional[str]

    latitude: Optional[float]
    longitude: Optional[float]

    salary_min: Optional[int]
    salary_max: Optional[int]

    phone: Optional[str]

    category: Optional[str]

    published_at: Optional[datetime]


class KorectCollector:
    """Collector for korect.kr / kowork.kr jobs API."""

    def __init__(
        self,
        page_size: int = 20,
        timeout: int = 30,
    ) -> None:
        self.page_size = page_size
        self.timeout = timeout

    def get_latest_jobs(self) -> list[JobDto]:
        """
        Получить последнюю страницу вакансий.
        """

        params = {
            "sortBy": "publishedAt",
            "sortOrder": "desc",
            "isFeatured": "false",
            "hasActiveHotBoost": "false",
            "limit": self.page_size,
            "page": 1,
            "status": "ACTIVE",
        }

        response = requests.get(
            API_URL,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        payload = response.json()

        jobs: list[JobDto] = []

        for item in payload.get("data", []):

                    
            city_info = item.get("cityTranslation") or {}      

            jobs.append(
                JobDto(
                    external_id=item.get("id"),

                    title=item.get("title", "").strip(),

                    description=clean_html(item.get("description", "")).strip(),

                    #city=item.get("city"),

                    city_ru = city_info.get("nameRu"),
                    city_ko = city_info.get("nameKo"),
                    city_en = city_info.get("nameEn"),

                    location=item.get("location"),

                    latitude = city_info.get("latitude"),
                    longitude = city_info.get("longitude"),
                    
                    salary_min=item.get("salaryMin"),

                    salary_max=item.get("salaryMax"),

                    phone=item.get("hrPhone"),

                    category=(
                        item.get("category", {})
                        .get("nameRu")
                    ),

                    published_at=self._parse_datetime(
                        item.get("publishedAt")
                    ),
                )
            )

        return jobs

    @staticmethod
    def _parse_datetime(value: str | None) -> Optional[datetime]:
        if not value:
            return None

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError:
            return None
        
def print_jobs(jobs: list[JobDto]) -> None:
    print()
    print("=" * 80)
    print(f"Jobs received: {len(jobs)}")
    print("=" * 80)

    for index, job in enumerate(jobs, start=1):

        print()
        print(f"[{index}] {job.title}")

        print(f"City:      {job.city_ru}")
        print(f"Location:  {job.location}")

        print(
            f"Salary:    {job.salary_min:,}"
            if job.salary_min
            else "Salary:    n/a"
        )

        print(f"Category:  {job.category}")
        print(f"Phone:     {job.phone}")
        print(f"Published: {job.published_at}")

        print("-" * 80)

        description = (
            job.description[:300]
            .replace("\n", " ")
            .strip()
        )

        print(description)

        if len(job.description) > 300:
            print("...")

def clean_html(text: str) -> str:
    if not text:
        return ""

    return BeautifulSoup(
        text,
        "html.parser"
    ).get_text("\n")
