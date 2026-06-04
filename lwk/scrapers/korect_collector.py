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
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
# from pathlib import Path
from korect_seen_jobs import SeenJobsStore

import requests
# import json

API_URL = "https://korect.kr/api/v1/jobs"


@dataclass(slots=True)
class JobDto:
    external_id: str

    title: str
    description: str

    city: Optional[str]
    location: Optional[str]

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

            jobs.append(
                JobDto(
                    external_id=item.get("id"),

                    title=item.get("title", "").strip(),

                    description=item.get("description", "").strip(),

                    city=item.get("city"),

                    location=item.get("location"),

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

        print(f"City:      {job.city}")
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


def main() -> None:
    collector = KorectCollector()

    jobs = collector.get_latest_jobs()

    store = SeenJobsStore()

    new_jobs = []

    for job in jobs:

        if store.contains(job.external_id):
            continue

        new_jobs.append(job)

    print()
    print(f"NEW JOBS FOUND: {len(new_jobs)}")

    print()

    for job in new_jobs:

        print(job.title)

    store.mark_seen(
        [job.external_id for job in new_jobs]
    )

    #collector = KorectCollector()

    #jobs = collector.get_latest_jobs()

    #   print_jobs(jobs)


if __name__ == "__main__":
    main()