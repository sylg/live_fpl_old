import pusher
import redis
from bs4 import BeautifulSoup
import urllib2
from push import *

def get_fixture_ids():
	url = 'http://fantasy.premierleague.com/fixtures/5/'
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
		else:
			r.lpush('fixture_ids', fixture_id)


def create_scrapper():
	for ids in r.lrange('fixture_ids',0, -1):
		scrapper.delay(ids)


def dict_diff(dict_a, dict_b):
    return dict([
        (key, dict_b.get(key, dict_a.get(key)))
        for key in set(dict_a.keys()+dict_b.keys())
        if (
            (key in dict_a and (not key in dict_b or dict_a[key] != dict_b[key])) or
            (key in dict_b and (not key in dict_a or dict_a[key] != dict_b[key]))
        )
    ])


def scrapper(fixture_id):
	url = 'http://fantasy.premierleague.com/fixture/%s/' %fixture_id
	response = urllib2.urlopen(url)
	html = response.read()
	soup = BeautifulSoup(html)
	for teams in soup.find_all('table'):
		teamname = str(teams.find('caption').string)

		for players in teams.find('tbody').find_all('tr'):
			playername = str(players.td.string.strip())
			if r.lrem('lineups:%s' %fixture_id, 0, playername) == 0:
				r.rpush('lineups:%s' %fixture_id, playername)
			else:
				r.rpush('lineups:%s' %fixture_id, playername)

			
			r.hset(playername+':fresh:'+str(fixture_id),'TEAMNAME',str(teamname))
			keys = ['MP', 'GS', 'A', 'CS', 'GC', 'OG', 'PS', 'PM', 'YC', 'RC','S', 'B', 'ESP', 'TP']
			i = 1
			for key in keys:
				r.hset(playername+':fresh:'+str(fixture_id), key, int(players.find_all('td')[i].string.strip()))
				i += 1

	#Begin Differential between Scrap & push
	for players in r.lrange('lineups:%s' %fixture_id, 0, -1):
		old = r.hgetall(players+':old:%s' %fixture_id)
		fresh = r.hgetall(players+':fresh:%s' %fixture_id)
		if dict_diff(old,fresh):
			push_data(players,dict_diff(old,fresh))

	#Rename fresh data as old for next scrap
		# r.rename(players+':fresh:%s' %fixture_id, players+':fresh:%s' %fixture_id)




scrapper(51)
