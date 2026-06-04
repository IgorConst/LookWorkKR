from pathlib import Path
import json


class SeenJobsStore:
    """
    Хранилище уже обработанных вакансий.

    MVP version:
        JSON file.
    """

    def __init__(
        self,
        file_path: str = "data/seen_jobs.json",
    ) -> None:

        self.file_path = Path(file_path)

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.file_path.exists():
            self._save(set())

    def load(self) -> set[str]:
        try:
            with open(
                self.file_path,
                "r",
                encoding="utf-8",
            ) as f:

                data = json.load(f)

            return set(data)

        except Exception:
            return set()

    def save(self, ids: set[str]) -> None:
        self._save(ids)

    def add(self, job_id: str) -> None:
        ids = self.load()

        ids.add(job_id)

        self._save(ids)

    def contains(self, job_id: str) -> bool:
        ids = self.load()

        return job_id in ids

    def get_new_ids(
        self,
        ids: list[str],
    ) -> list[str]:

        seen = self.load()

        return [
            job_id
            for job_id in ids
            if job_id not in seen
        ]

    def mark_seen(
        self,
        ids: list[str],
    ) -> None:

        seen = self.load()

        seen.update(ids)

        self._save(seen)

    def _save(self, ids: set[str]) -> None:

        with open(
            self.file_path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                sorted(ids),
                f,
                ensure_ascii=False,
                indent=2,
            )