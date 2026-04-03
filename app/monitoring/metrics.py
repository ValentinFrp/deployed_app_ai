from prometheus_client import Counter, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 120],
)

AGENT_RUNS_TOTAL = Counter(
    "agent_runs_total",
    "Total agent runs",
    ["status"],
)

AGENT_TOKENS_TOTAL = Counter(
    "agent_tokens_total",
    "Total tokens used",
    ["type"],
)

AGENT_COST_USD_TOTAL = Counter(
    "agent_cost_usd_total",
    "Total estimated cost in USD",
)
