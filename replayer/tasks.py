from celery import Celery
from celery.schedules import crontab
from celery.decorators import periodic_task
import requests
import os
import redis

redis_url = 'redis://localhost:6379/3'
r = redis.StrictRedis(host='localhost', port=6379, db=0 )
rs = redis.StrictRedis(host='localhost', port=6379, db=3 )

celery = Celery('tasks', broker=redis_url, backend=redis_url)







@periodic_task(run_every=crontab(minute='*' ,hour='*'),ignore_result=True)
def unit_testing_scrap():
	if r.get('scrapmode') == 'ON' and r.exists('fixture_ids'):
		for fixture in r.lrange('fixture_ids', 0, -1):
			if not rs.exists('scrapcounter:%s'%fixture):
				rs.set('scrapcounter:%s'%fixture,0)
			if not os.path.exists(os.getcwd()+'/%s/'%fixture):
				os.makedirs(os.getcwd()+'/%s/'%fixture)
			i = rs.get('scrapcounter:%s'%fixture)
			if int(i) == 0:
				last_file = "no file"
			else:
				last_file = open(os.getcwd()+'/%s/update%s.html'%(fixture, int(i) - 1)).read()

			url = 'http://fantasy.premierleague.com/fixture/%s/' %fixture
			response = requests.get(url)
			html = response.text
			if html != last_file:
				f = open(os.getcwd()+'/%s/update%s.html'%(fixture,i), 'w')
				f.write(html)
				f.close()
				rs.incr('scrapcounter:%s'%fixture)
				print "created the file /%s/update%s.html"%(fixture,i)
			else:
				print "same data in %s | i = %s"%(fixture, str(i))
		