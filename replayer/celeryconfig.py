from datetime import timedelta
from celery.schedules import crontab

CELERY_TIMEZONE = 'Europe/London'

redis_url = 'redis://localhost:6379/3'
BROKER_URL = redis_url

# List of modules to import when celery starts.
CELERY_IMPORTS = ("tasks" )

# Using the database to store task state and results.
CELERY_RESULT_BACKEND = redis_url