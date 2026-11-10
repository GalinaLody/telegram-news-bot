from dataclasses import dataclass
from datetime import datetime


@dataclass
class News:
    title: str
    url: str
    source: str
    published_at: datetime
    summary_raw: str
    topic: str


@dataclass
class DigestPart:
    """Одно сообщение дайджеста и новости, которые в нём лежат.

    Attributes:
        text: Готовый текст сообщения для отправки в Telegram.
        news: Новости этой части; после её доставки их можно помечать отправленными.
    """

    text: str
    news: list[News]
