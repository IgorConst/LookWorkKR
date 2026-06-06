import json
from pathlib import Path

from lwk.models.user_profile import UserProfile

CONFIG_FILE = (
    Path(__file__).parent.parent
    / "config"
    / "users.json"
)

def load_profiles() -> list[UserProfile]:

    with open(CONFIG_FILE, encoding="utf-8") as f:
        data = json.load(f)

    path = Path(CONFIG_FILE)

    with open(
        path,
        encoding="utf-8",
    ) as f:

        data = json.load(f)

    profiles = []

    for user in data["users"]:

        profiles.append(
            UserProfile(
                name=user["name"],
                telegram_id=user["telegram_id"],
                cities=user.get("cities", []),
                min_salary=user.get("min_salary"),
                required_visas=user.get(
                    "required_visas",
                    [],
                ),
                keywords=user.get(
                    "keywords",
                    [],
                ),
            )
        )

    return profiles