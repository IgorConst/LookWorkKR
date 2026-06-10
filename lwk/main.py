import os
import time

from dotenv import load_dotenv
#from sqlalchemy import TIME

from lwk.scrapers.korect_collector import KorectCollector
from lwk.scrapers.korect_seen_jobs import SeenJobsStore
from lwk.services.telegram_sender import TelegramSender

from lwk.services.profile_loader import load_profiles
from lwk.services.job_matcher import JobMatcher

MIN_MATCH_SCORE = 50

CHECK_INTERVAL = 300  # 5 минут=> 300 с

def main():
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(CHECK_INTERVAL)

def run_once():
    load_dotenv()  # loads .env into environment variables
    

    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not telegram_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing in .env")

    sender = TelegramSender(bot_token=telegram_token)

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

            #### Here you can add code to send notifications about the match, e.g. via Telegram
            message = build_message(
                job,
                result,
            )

            try:
                sender.send(
                    profile.telegram_id,
                    message,
                )

                print(
                    f"Telegram sent to {profile.name}"
                )

            except Exception as ex:

                print(
                    f"Telegram failed for "
                    f"{profile.name}: {ex}"
                )

    seen_store.mark_seen(
        [job.external_id for job in new_jobs]
    )

    print()
    print(f"Matches found: {matches_found}")
    print()
    print("=== LWK FINISH ===")


def build_message(job, result) -> str:

    reasons = []

    if result.city_match:
        reasons.append("город")

    if result.salary_match:
        reasons.append("зарплата")

    if result.visa_match:
        reasons.append("виза")

    if result.keyword_match:
        reasons.append("ключевые слова")

    salary = "не указана"

    if job.salary_min and job.salary_max:
        salary = (
            f"{job.salary_min:,} - "
            f"{job.salary_max:,} KRW"
        )

    elif job.salary_max:
        salary = (
            f"до {job.salary_max:,} KRW"
        )

    elif job.salary_min:
        salary = (
            f"от {job.salary_min:,} KRW"
        )

    lines = [
        job.title,
        "",
    ]

    if job.city_ru:
        lines.append(
            f"📍 {job.city_ru}"
        )

    lines.append(
        f"Зарплата: {salary}"
    )

    if job.phone:
        lines.append(
            f"☎ {job.phone}"
        )

    lines.append("")

    if job.description:

        preview = (
            job.description[:300]
            .replace("\n\n", "\n")
            .strip()
        )

        lines.append(preview)
        lines.append("")

    lines.append(
        f"Совпадение: {result.score} "
        f"({', '.join(reasons)})"
    )

    return "\n".join(lines)