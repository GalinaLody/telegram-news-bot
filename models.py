"""Модели данных, которыми обмениваются шаги цепочки дайджеста."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class News:
    """Одна новость, собранная из источника.

    Attributes:
        title: Заголовок новости.
        url: Нормализованная ссылка на оригинал; служит ключом дедупликации.
        source: Название источника.
        published_at: Время публикации (с часовым поясом).
        summary_raw: Сырой текст новости, возможно с HTML.
        topic: Тема, под которой новость попадёт в дайджест.
    """

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
