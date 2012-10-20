from datetime import timedelta
from celery.schedules import crontab
from push import *

CELERY_TIMEZONE = 'Europe/London'


BROKER_URL = 'redis://localhost:6379/0'
#BROKER_URL = redis_url

# List of modules to import when celery starts.
CELERY_IMPORTS = ("tasks" )

# Using the database to store task state and results.
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
#CELERY_RESULT_BACKEND = redis_url
