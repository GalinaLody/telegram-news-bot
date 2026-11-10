# main.py
MAIN_MISSING_ENV_EXIT_CODE = 1

# digest.py
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
COLLECTORS_RSS_COLLECTOR_SOCKET_TIMEOUT_SECONDS = 30

# collectors/telegram_collector.py
COLLECTORS_TELEGRAM_COLLECTOR_TITLE_MAX_CHARS = 80
COLLECTORS_TELEGRAM_COLLECTOR_VIBECODING_PREVIEW_COUNT = 5
COLLECTORS_TELEGRAM_COLLECTOR_VERYVIBECODING_PREVIEW_COUNT = 3
