#!/usr/bin/env bash
# Run service and kept celery in the same shot
celery -A url_shortener worker --loglevel=info --pool=solo &

python -m gunicorn url_shortener.asgi:application -k uvicorn.workers.UvicornWorker