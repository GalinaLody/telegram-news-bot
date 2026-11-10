from datetime import timedelta, timezone

# main.py
MAIN_MISSING_ENV_EXIT_CODE = 1

# filtering.py, summarizer.py, builder.py
# Часовой пояс дайджеста: в Турции с 2016 года круглый год UTC+3 без перехода на летнее время.
# ZoneInfo не используем: на Windows для неё нужен отдельный пакет tzdata.
DIGEST_TIMEZONE = timezone(timedelta(hours=3), "Europe/Istanbul")
# Окно дайджеста в днях: по нему фильтруются новости и ограничивается выгрузка из Telegram.
DIGEST_FILTER_RECENT_DAYS = 7
DIGEST_RANK_TARGET_COUNT = 25
DIGEST_SUMMARY_MAX_CHARS = 280
# Лимит Telegram Bot API на длину одного сообщения.
DIGEST_TELEGRAM_MESSAGE_MAX_LEN = 4096
# Длина разделителя "\n\n" между блоками дайджеста.
DIGEST_BLOCK_SEPARATOR_LEN = 2

# sender.py
SENDER_TIMEOUT_SECONDS = 30

# storage.py
STORAGE_CLEANUP_OLD_DAYS = 30

# collectors/rss_collector.py
COLLECTORS_RSS_TIMEOUT_SECONDS = 30

# collectors/telegram_collector.py
COLLECTORS_TELEGRAM_COLLECTOR_TITLE_MAX_CHARS = 80
