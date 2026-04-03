import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv('WORKERS', '2'))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = int(os.getenv('WORKER_TIMEOUT', '120'))
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = os.getenv('LOG_LEVEL', 'info')
