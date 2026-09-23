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
