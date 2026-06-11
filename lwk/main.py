import os
import time
from pathlib import Path
from dotenv import load_dotenv

from lwk.logger import logger
from lwk.scrapers.korect_collector import KorectCollector
from lwk.scrapers.korect_seen_jobs import SeenJobsStore
from lwk.services.telegram_sender import TelegramSender
from lwk.services.profile_loader import load_profiles
from lwk.services.job_matcher import JobMatcher

MIN_MATCH_SCORE = 50
CHECK_INTERVAL = 300  # 5 минут

# Путь к файлу-флагу (в корне проекта LookWorkKR)
STOP_FLAG_PATH = Path(__file__).parent.parent / "stop.flag"
#      Когда нужно остановить скрипт, ты заходишь на сервер через обычный SSH-терминал и пишешь:
#   cd ~/LookWorkKR
#   touch stop.flag

def main():
    logger.info("Starting LWK main loop...")
    while True:
        if STOP_FLAG_PATH.exists():
            logger.warning("Stop flag detected! Shutting down gracefully...")
            STOP_FLAG_PATH.unlink()  # Удаляем флаг, чтобы следующий запуск прошел нормально
            break

        try:
            run_once()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        time.sleep(CHECK_INTERVAL)

def run_once():
    load_dotenv()
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not telegram_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing in .env")

    sender = TelegramSender(bot_token=telegram_token)

    logger.info("=== LWK START ===")

    collector = KorectCollector()
    seen_store = SeenJobsStore()

    jobs = collector.get_latest_jobs()
    logger.info(f"Jobs loaded: {len(jobs)}")

    new_jobs = [job for job in jobs if not seen_store.contains(job.external_id)]
    logger.info(f"New jobs found: {len(new_jobs)}")

    if not new_jobs:
        logger.info("No new jobs.")
        logger.info("=== LWK FINISH ===")
        return

    profiles = load_profiles()
    logger.info(f"Profiles loaded: {len(profiles)}")

    matcher = JobMatcher()
    matches_found = 0

    for job in new_jobs:
        logger.info("=" * 80)
        logger.info(f"JOB: {job.title}")
        
        if job.city_ru:
            logger.info(f"City: {job.city_ru}")
        if job.salary_max:
            logger.info(f"Salary: {job.salary_max:,}")

        logger.info("-" * 80)

        for profile in profiles:
            result = matcher.score(job, profile)

            if result.score < MIN_MATCH_SCORE:
                continue

            matches_found += 1
            logger.info(f"[MATCH] {profile.name} (score={result.score})")
            logger.info(f"city={result.city_match} salary={result.salary_match} visa={result.visa_match} keyword={result.keyword_match}")

            message = build_message(job, result)

            try:
                sender.send(profile.telegram_id, message)
                logger.info(f"Telegram sent to {profile.name}")
            except Exception as ex:
                logger.error(f"Telegram failed for {profile.name}: {ex}")

    seen_store.mark_seen([job.external_id for job in new_jobs])

    logger.info(f"Matches found: {matches_found}")
    logger.info("=== LWK FINISH ===")

def build_message(job, result) -> str:
    # ... (оставляем без изменений)
    reasons = []
    if result.city_match:
        reasons.append("город")
    if result.salary_match:
        reasons.append("зп")
    if result.visa_match:
        reasons.append("visa")
    if result.keyword_match:
        reasons.append("keywords")

    salary = "не указана"
    if job.salary_text:
        salary = job.salary_text
    if job.salary_min and job.salary_max:
        salary = f"{job.salary_min:,} - {job.salary_max:,} KRW"
    elif job.salary_max:
        salary = f"до {job.salary_max:,} KRW"
    elif job.salary_min:
        salary = f"от {job.salary_min:,} KRW"

    lines = [job.title, ""]
    if job.city_ru:
        lines.append(f"📍 {job.city_ru}")
    lines.append(f"Зарплата: {salary}")
    if job.phone:
        lines.append(f"☎ {job.phone}")
    lines.append("")

    if job.description:
        preview = job.description[:300].replace("\n\n", "\n").strip()
        lines.append(preview)
        lines.append("")

    lines.append(f"Совпадение: {result.score} ({', '.join(reasons)})")
    return "\n".join(lines)