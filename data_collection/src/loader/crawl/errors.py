class CrawlError(Exception):
    """Base class for crawl-specific failures."""


class BlockedRequestError(CrawlError):
    """Raised when the request looks blocked or connection state is unstable."""


class SlowResponseError(CrawlError):
    """Raised when the server is too slow and should be retried later."""


class StaleListingError(CrawlError):
    """Raised when the listing appears gone or permanently unavailable."""


class MissingPerformanceRecordError(CrawlError):
    """Raised when the detail page exists but has no performance record iframe."""
