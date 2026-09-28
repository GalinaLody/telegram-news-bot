import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

import storage
from bot import bot, send_message
from collectors.rss_collector import fetch_rss
from collectors.telegram_collector import fetch_telegram_channel
from digest import build_digest, dedupe, filter_recent, rank, split_for_telegram
from models import News

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)

load_dotenv()

SOURCES_PATH = Path(__file__).resolve().parent / "sources.yaml"
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")


async def collect_all() -> tuple[list[News], list[tuple[str, str]]]:
    with open(SOURCES_PATH, encoding="utf-8") as f:
        sources = yaml.safe_load(f)

    enabled_sources = [s for s in sources if s.get("enabled")]
    logger.info(f"Источников для сбора: {len(enabled_sources)}")

    all_news: list[News] = []
    failed_sources: list[tuple[str, str]] = []

    for source in enabled_sources:
        topics = source.get("topics", [])
        source_type = source.get("type")

        try:
            if source_type == "rss":
                news_items = fetch_rss(
                    url=source["url"],
                    source_name=source["name"],
                    topic=topics[0],
                    keywords=source.get("keywords"),
                )
            elif source_type == "telegram":
                channel = source["url"].rstrip("/").split("/")[-1]
                news_items = await fetch_telegram_channel(
                    channel_username=channel,
                    topic=topics[0],
                )
            else:
                continue
        except Exception as exc:
            logger.warning(f"Источник '{source['name']}' упал: {exc}")
            failed_sources.append((source["name"], str(exc)))
            continue

        if len(topics) > 1:
            for i, news in enumerate(news_items):
                news.topic = topics[i % len(topics)]

        logger.info(f"{source['name']}: получено {len(news_items)} новостей")
        all_news.extend(news_items)

    return all_news, failed_sources


async def run_weekly_digest(dry_run: bool = True) -> None:
    try:
        news_items, failed_sources = await collect_all()
        logger.info(f"Всего собрано новостей: {len(news_items)}")

        seen_urls: set[str] = set()
        unique_news: list[News] = []
        for news in news_items:
            if news.url not in seen_urls:
                seen_urls.add(news.url)
                unique_news.append(news)
        logger.info(f"После удаления повторов внутри сбора: {len(unique_news)}")

        recent_news = filter_recent(unique_news)
        logger.info(f"После filter_recent: {len(recent_news)}")

        deduped_news = dedupe(recent_news)
        logger.info(f"После dedupe: {len(deduped_news)}")

        ranked_news = rank(deduped_news)
        logger.info(f"После rank: {len(ranked_news)}")

        if ranked_news:
            digest_text = build_digest(ranked_news)
        else:
            logger.info("Нет новых новостей")
            digest_text = "На этой неделе новых новостей не нашлось."

        if failed_sources:
            failed_names = ", ".join(name for name, _ in failed_sources)
            digest_text = f"⚠️ Без новостей (ошибка сбора): {failed_names}\n\n{digest_text}"

        parts = split_for_telegram(digest_text)

        if dry_run:
            for i, part in enumerate(parts, start=1):
                print(f"--- Часть {i}/{len(parts)} ---")
                print(part)
        else:
            for part in parts:
                await send_message(OWNER_CHAT_ID, part)

            for news in ranked_news:
                storage.mark_sent(news.url)

            logger.info(
                f"Дайджест успешно отправлен: {len(parts)} частей, "
                f"{len(ranked_news)} новостей помечено как отправленные"
            )

            # Сбой очистки не должен выглядеть как сбой уже доставленного дайджеста.
            try:
                removed = storage.cleanup_old()
                logger.info(f"cleanup_old: удалено старых записей: {removed}")
            except Exception:
                logger.exception("Не удалось очистить старые записи sent_news")
    except Exception as exc:
        logger.exception("Ошибка при формировании/отправке дайджеста")

        if not dry_run:
            try:
                await send_message(
                    OWNER_CHAT_ID,
                    f"Не удалось сформировать/отправить дайджест. Ошибка: "
                    f"{type(exc).__name__}: {exc}. Подробности — в логах GitHub Actions.",
                )
            except Exception:
                logger.exception("Не удалось отправить уведомление об ошибке")

        raise
    finally:
        if not dry_run:
            await bot.session.close()
