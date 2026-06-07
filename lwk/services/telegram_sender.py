from urllib.parse import quote

import requests


class TelegramSender:

    def __init__(
        self,
        bot_token: str,
    ) -> None:

        self.bot_token = bot_token

    def send(
        self,
        chat_id: int,
        text: str,
    ) -> None:

        url = (
            f"https://api.telegram.org"
            f"/bot{self.bot_token}"
            f"/sendMessage"
        )

        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
            },
            timeout=20,
        )

        response.raise_for_status()