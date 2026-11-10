"""Нормализация ссылок, чтобы одна статья не выглядела как несколько разных URL."""

from urllib.parse import urlsplit, urlunsplit

TRACKING_PARAMS = {"fbclid", "gclid"}


def normalize_url(url: str) -> str:
    """Привести ссылку к единому виду для сравнения и хранения.

    Схема и домен переводятся в нижний регистр, удаляются параметры `utm_*`,
    `fbclid`, `gclid`, фрагмент (`#...`) и завершающий `/` в пути (кроме
    корня). Остальные параметры сохраняются в исходном порядке и виде.

    Args:
        url: Исходная ссылка.

    Returns:
        Нормализованная ссылка.
    """
    parts = urlsplit(url)

    query_items = [
        item
        for item in parts.query.split("&")
        if item
        and not item.split("=", 1)[0].lower().startswith("utm_")
        and item.split("=", 1)[0].lower() not in TRACKING_PARAMS
    ]

    path = parts.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/") or "/"

    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "&".join(query_items), ""))
