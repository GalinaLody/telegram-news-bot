"""Цепочка недельного дайджеста: сбор, фильтры, сборка, отправка, запись в базу.

Вызывается из main.py; собирает вместе остальные модули проекта.
"""

import logging

import storage
from builder import build_intro, build_parts
from collectors.rss_collector import fetch_rss
from collectors.telegram_collector import fetch_telegram_channel
from config import OWNER_CHAT_ID, load_sources, load_topic_keywords
from filtering import assign_topic, dedupe, filter_recent, rank, remove_duplicates
from models import News
from sender import send_message
from urls import normalize_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)


async def collect_all() -> tuple[list[News], list[tuple[str, str]]]:
    """Собрать новости из всех включённых источников sources.yaml.

    У каждой новости URL нормализуется, а у источников с несколькими темами
    тема выбирается по ключевым словам. Сбой одного источника не прерывает сбор.

    Returns:
        Пара: все собранные новости и список упавших источников
        в виде (название, текст ошибки).
    """
    enabled_sources = [s for s in load_sources() if s.get("enabled")]
    topic_keywords = load_topic_keywords()
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

        for news in news_items:
            news.url = normalize_url(news.url)

        if len(topics) > 1:
            for news in news_items:
                news.topic = assign_topic(news, topics, topic_keywords)

        logger.info(f"{source['name']}: получено {len(news_items)} новостей")
        all_news.extend(news_items)

    return all_news, failed_sources


async def run_weekly_digest(dry_run: bool = True) -> None:
    """Собрать новости, сформировать дайджест и отправить его владельцу.

    Каждая часть дайджеста помечается отправленной сразу после доставки. При
    ошибке владельцу уходит уведомление, и исключение пробрасывается дальше.

    Args:
        dry_run: Если True, части только печатаются; ничего не отправляется,
            а файл digest.db не создаётся и не меняется (база только читается).
    """
    sent_parts = 0
    total_parts = 0
    try:
        if not dry_run:
            storage.init_db()

        news_items, failed_sources = await collect_all()
        logger.info(f"Всего собрано новостей: {len(news_items)}")

        unique_news = remove_duplicates(news_items)
        logger.info(f"После удаления повторов внутри сбора: {len(unique_news)}")

        recent_news = filter_recent(unique_news)
        logger.info(f"После filter_recent: {len(recent_news)}")

        deduped_news = dedupe(recent_news)
        logger.info(f"После dedupe: {len(deduped_news)}")

        ranked_news = rank(deduped_news)
        logger.info(f"После rank: {len(ranked_news)}")

        if not ranked_news:
            logger.info("Нет новых новостей")

        # Порядок в начале сообщения: вступление, затем предупреждение об упавших источниках.
        header_blocks = [build_intro(ranked_news)]
        if failed_sources:
            failed_names = ", ".join(name for name, _ in failed_sources)
            header_blocks.append(f"⚠️ Без новостей (ошибка сбора): {failed_names}")
        header = "\n\n".join(block for block in header_blocks if block)

        parts = build_parts(ranked_news, header=header)
        total_parts = len(parts)

        if dry_run:
            for i, part in enumerate(parts, start=1):
                print(f"--- Часть {i}/{total_parts} ---")
                print(part.text)
        else:
            # Новости помечаем сразу после доставки своей части: если упадёт
            # следующая часть, уже доставленное не придёт повторно.
            for part in parts:
                send_message(OWNER_CHAT_ID, part.text)
                for news in part.news:
                    storage.mark_sent(news.url)
                sent_parts += 1

            logger.info(
                f"Дайджест успешно отправлен: {total_parts} частей, "
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
            progress = f" Отправлено частей: {sent_parts} из {total_parts}." if total_parts else ""
            try:
                send_message(
                    OWNER_CHAT_ID,
                    f"Не удалось сформировать/отправить дайджест. Ошибка: "
                    f"{type(exc).__name__}: {exc}.{progress} "
                    f"Подробности — в логах GitHub Actions.",
                )
            except Exception:
                logger.exception("Не удалось отправить уведомление об ошибке")

        raise
