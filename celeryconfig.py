from datetime import timedelta
from celery.schedules import crontab

CELERY_TIMEZONE = 'Europe/London'


BROKER_URL = 'redis://'

# List of modules to import when celery starts.
CELERY_IMPORTS = ("tasks", )

## Using the database to store task state and results.
CELERY_RESULT_BACKEND = "redis://"



