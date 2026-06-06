from lwk.scrapers.korect_collector import KorectCollector
from lwk.scrapers.korect_seen_jobs import SeenJobsStore

from lwk.services.profile_loader import load_profiles
from lwk.services.job_matcher import JobMatcher


MIN_MATCH_SCORE = 50


def main() -> None:

    print()
    print("=== LWK START ===")
    print()

    collector = KorectCollector()
    seen_store = SeenJobsStore()

    jobs = collector.get_latest_jobs()

    print(f"Jobs loaded: {len(jobs)}")

    new_jobs = [
        job
        for job in jobs
        if not seen_store.contains(job.external_id)
    ]

    print(f"New jobs found: {len(new_jobs)}")

    if not new_jobs:

        print()
        print("No new jobs.")
        print()
        print("=== LWK FINISH ===")

        return

    profiles = load_profiles()

    print(f"Profiles loaded: {len(profiles)}")

    matcher = JobMatcher()

    matches_found = 0

    for job in new_jobs:

        print()
        print("=" * 80)
        print(f"JOB: {job.title}")

        if job.city_ru:
            print(f"City: {job.city_ru}")

        if job.salary_max:
            print(f"Salary: {job.salary_max:,}")

        print("-" * 80)

        for profile in profiles:

            result = matcher.score(job, profile)

            if result.score < MIN_MATCH_SCORE:
                continue

            matches_found += 1

            print(
                f"[MATCH] {profile.name} "
                f"(score={result.score})"
            )

            print(
                f"city={result.city_match} "
                f" salary={result.salary_match}"
                f" visa={result.visa_match}"
                f" keyword={result.keyword_match}"
            )

    seen_store.mark_seen(
        [job.external_id for job in new_jobs]
    )

    print()
    print(f"Matches found: {matches_found}")
    print()
    print("=== LWK FINISH ===")