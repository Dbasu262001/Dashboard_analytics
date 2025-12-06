#!/bin/bash
exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 10 --worker-class uvicorn.workers.UvicornWorker analytics_dashboard.app:app
