from dataclasses import dataclass
import re


VISA_RE = re.compile(r"F\d+", re.IGNORECASE)


@dataclass(slots=True)
class MatchResult:
    score: int
    city_match: bool
    salary_match: bool
    visa_match: bool
    keyword_match: bool


class JobMatcher:

    CITY_SCORE = 50
    SALARY_SCORE = 30
    VISA_SCORE = 10
    KEYWORD_SCORE = 10

    def score(self, job, profile) -> MatchResult:

        score = 0

        city_match = self._city_match(job, profile)
        salary_match = self._salary_match(job, profile)
        visa_match = self._visa_match(job, profile)
        keyword_match = self._keyword_match(job, profile)

        if city_match:
            score += self.CITY_SCORE

        if salary_match:
            score += self.SALARY_SCORE

        if visa_match:
            score += self.VISA_SCORE

        if keyword_match:
            score += self.KEYWORD_SCORE

        print("DEBUG/ Match score:", score)

        return MatchResult(
            score=score,
            city_match=city_match,
            salary_match=salary_match,
            visa_match=visa_match,
            keyword_match=keyword_match,
        )

    def _city_match(self, job, profile) -> bool:

        if not profile.cities:
            return True

        if not job.city_ru:
            return False

        return job.city_ru in profile.cities

    def _salary_match(self, job, profile) -> bool:

        if profile.min_salary is None:
            return True

        if job.salary_min is None:
            return False

        return job.salary_min >= profile.min_salary

    def _visa_match(self, job, profile) -> bool:

        if not profile.required_visas:
            return True

        visas_found = {
            visa.upper()
            for visa in VISA_RE.findall(
                job.description.upper()
            )
        }

        required_visas = {
            visa.upper()
            for visa in profile.required_visas
        }

        return bool(
            visas_found.intersection(
                required_visas
            )
        )

    def _keyword_match(self, job, profile) -> bool:

        if not profile.keywords:
            return True

        text = (
            f"{job.title}\n{job.description}"
        ).lower()

        for keyword in profile.keywords:

            if keyword.lower() in text:
                return True

        return False