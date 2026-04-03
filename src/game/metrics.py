from prometheus_client import Counter, Histogram

# HTTP metrics
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path", "status_code", "client_type"]
)

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code", "client_type"]
)

# Game-specific metrics
game_errors_total = Counter(
    "game_errors_total",
    "Total game errors",
    ["error_type", "client_type"]
)

game_words_submitted_total = Counter(
    "game_words_submitted_total",
    "Total words submitted by users",
    ["client_type"]
)
