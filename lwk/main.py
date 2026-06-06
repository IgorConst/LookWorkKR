from lwk.scrapers.korect_collector import KorectCollector
from lwk.scrapers.korect_seen_jobs import SeenJobsStore
from lwk.services.job_matcher import JobMatcher
from lwk.services.profile_loader import load_profiles

def main():

    print()
    print("LWK started")
    print()
    
    collector = KorectCollector()

    jobs = collector.get_latest_jobs()

    store = SeenJobsStore()

    matcher = JobMatcher()

    profiles = load_profiles()

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

    print()
    print("Done")