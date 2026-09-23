import sys
from pathlib import Path

import httpx
import yaml

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SOURCES_PATH = Path(__file__).resolve().parent / "sources.yaml"
CHECK_NAMES = {"VC.ru — раздел AI", "Cursor — Changelog/Blog", "TechCrunch — AI"}

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


def check_url(url: str, headers: dict) -> None:
    try:
        response = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
        content_type = response.headers.get("content-type", "—")
        preview = response.text[:300]
        print(f"URL: {url}")
        print(f"Статус: {response.status_code}")
        print(f"Content-Type: {content_type}")
        print(f"Первые 300 символов ответа:\n{preview}")
    except Exception as exc:
        print(f"URL: {url}")
        print(f"Ошибка запроса: {exc}")


if __name__ == "__main__":
    with open(SOURCES_PATH, encoding="utf-8") as f:
        sources = yaml.safe_load(f)

    targets = [s for s in sources if s["name"] in CHECK_NAMES]

    for source in targets:
        print("=" * 80)
        print(f"Источник: {source['name']}")

        print("-" * 40)
        print("С заголовками по умолчанию:")
        check_url(source["url"], headers={})

        print("-" * 40)
        print("С браузерным User-Agent:")
        check_url(source["url"], headers={"User-Agent": BROWSER_USER_AGENT})

        print()
