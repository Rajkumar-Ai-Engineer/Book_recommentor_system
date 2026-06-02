
from .custom_logger import BookRecommendationLogger as _CustomLogger  # backward compat
try:
    from .custom_logger import BookRecommendationLogger
except Exception:
    BookRecommendationLogger = _CustomLogger

# Expose a global structlog-style logger used across the codebase
GLOBAL_LOGGER = BookRecommendationLogger().get_logger(__name__)
