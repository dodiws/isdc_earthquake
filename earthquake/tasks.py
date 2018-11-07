
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from datetime import datetime
from .views import (
	getLatestEarthQuake,
	getLatestShakemap,
	)
from dashboard.views import classmarkerGet

logger = get_task_logger(__name__)

@periodic_task(run_every=(crontab(hour='*')))
def updateLatestEarthQuake():
	getLatestEarthQuake()

@periodic_task(run_every=(crontab(hour='*')))
def updateLatestShakemap():
	getLatestShakemap(True)