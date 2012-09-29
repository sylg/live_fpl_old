from celery import Celery
from datetime import timedelta
from celery.schedules import crontab
from celery.decorators import periodic_task
import redis
import pusher
from bs4 import BeautifulSoup
import urllib2
import pickle
import os

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost')
r = redis.from_url(redis_url)
celery = Celery('tasks', backend=redis_url, broker=redis_url)

pusher.app_id = "28247"
pusher.key = "b2c9525770d59267a6a2"
pusher.secret = "12d6efe3c861e6ce372a"
p = pusher.Pusher()

# r = redis.StrictRedis(host='localhost', port=6379, db=0)


class DictDiffer(object):
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        return self.set_current - self.intersect 
    def removed(self):
        return self.set_past - self.intersect 
    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])




@periodic_task(run_every=crontab(minute='*/5',hour='8-21',day_of_week='saturday,sunday,monday,tuesday'))
def get_fixture_ids():
	url = 'http://fantasy.premierleague.com/fixtures/'
	response = urllib2.urlopen(url)
	html = response.read()
	tablestart = html.find('<div id="ism" class="ism">')
	tableend = html.find('<aside class="ismAside">')
	html = html[tablestart:tableend]
	soup = BeautifulSoup(html)
	for row in soup.find_all('tr', 'ismFixtureSummary'):
		fixture_id = str(row.find('a', text="Detailed stats")['data-id'])
		if r.lrem('fixture_ids', 0, fixture_id) == 0:
			r.lpush('fixture_ids', fixture_id)
			r.expire('fixture_ids', 39600)
			id_updated_msg = 'just add fixture %s' % fixture_id'
			p['test_channel'].trigger('chatmessage', {'message': id_updated_msg })
		else:
			r.lpush('fixture_ids', fixture_id)
			id_updated_msg = 'just add fixture %s' % fixture_id'
			p['test_channel'].trigger('chatmessage', {'message': id_updated_msg })


@periodic_task(run_every=crontab(minute='*', hour='8-22',day_of_week='saturday,sunday,monday,tuesday'))
def create_scrapper():
	if r.llen('fixture_ids') != 0:
		for ids in r.lrange('fixture_ids',0, -1):
			scrapper.delay(ids)

@celery.task
def scrapper(fixture_id):
	url = 'http://fantasy.premierleague.com/fixture/%s/' %fixture_id
	response = urllib2.urlopen(url)
	html = response.read()
	soup = BeautifulSoup(html)
	datas = []
	datas_push = []
	for teams in soup.find_all('table'):
		teamname = teams.find('caption').string
		for players in teams.find('tbody').find_all('tr'):
			playername = str(players.td.string.strip())
			data = {}
			data['TEAMNAME'] = str(teamname)
			keys = ['MP', 'GS', 'A', 'CS', 'GC', 'OG', 'PS', 'PM', 'YC', 'RC','S', 'B', 'ESP', 'TP']
			i = 1
			for key in keys:
				data[key] = str(players.find_all('td')[i].string.strip())
				if data[key] == '0':
					del data[key]
				i += 1
			datas.append([playername, data])

	#check if 1st scrap do nothing, else do a diff.
	if r.exists('data_old:%s' %fixture_id):
		datas_old = pickle.loads(r.get('data_old:%s' % fixture_id))
		i = 0
		#start Differential
		for players in datas:
			#new stats
			new_stats = DictDiffer(players[1], datas_old[i][1])
			added = {}
			updated = {}
			for keys in new_stats.added():
				added[str(keys)] = players[1][keys]
				added['TEAMNAME'] = players[1]['TEAMNAME'] 
			#updated stats
			for keys in new_stats.changed():
				added[str(keys)] = players[1][keys]
			if added:
				datas_push.append([players[0],added])
			i += 1
	else:
		r.set('data_old:%s' % fixture_id,pickle.dumps(datas))
		r.expire('data_old:%s' % fixture_id, 432000)
	#save fresh data as old for next scrapping diff
	r.set('data_old:%s' % fixture_id,pickle.dumps(datas))

	msg_test = 'I just scrapped this url:%s' %url
	p['test_channel'].trigger('chatmessage', {'message': msg_test})