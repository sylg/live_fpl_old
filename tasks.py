from celery import Celery
from datetime import timedelta
from celery.schedules import crontab
from celery.decorators import periodic_task
import redis
from bs4 import BeautifulSoup
import requests
from push import *
from classictable import *


celery = Celery('tasks', broker='redis://localhost:6379/0', backend='redis')
#celery = Celery('tasks', broker=redis_url, backend=redis_url)

def dict_diff(dict_a, dict_b):
    return dict([
        (key, dict_b.get(key, dict_a.get(key)))
        for key in set(dict_a.keys()+dict_b.keys())
        if (
            (key in dict_a and (not key in dict_b or dict_a[key] != dict_b[key])) or
            (key in dict_b and (not key in dict_a or dict_a[key] != dict_b[key]))
        )
    ])

@periodic_task(run_every=crontab(minute='*/1',hour='10-21',day_of_week='saturday,sunday,monday,tuesday'), ignore_result=True)
def get_fixture_ids():
	url = 'http://fantasy.premierleague.com/fixtures/'
	response = requests.get(url, headers=headers)
	html = response.text
	tablestart = html.find('<div id="ism" class="ism">')
	tableend = html.find('<aside class="ismAside">')
	html = html[tablestart:tableend]
	soup = BeautifulSoup(html)
	for row in soup.find_all('tr', 'ismFixtureSummary'):
		fixture_id = row.find('a', text="Detailed stats")['data-id']
		if fixture_id not in r.lrange('fixture_ids',0,-1):
			r.lpush('fixture_ids', fixture_id)


@periodic_task(run_every=crontab(minute='*', hour='10-22',day_of_week='saturday,sunday,monday,tuesday,wednesday'), ignore_result=True)
def create_scrapper():
	if r.llen('fixture_ids') != 0:
		for ids in r.lrange('fixture_ids',0, -1):
			scrapper.delay(ids)

@celery.task(ignore_result=True)
def scrapper(fixture_id):
	url = 'http://0.0.0.0:5001/fixture/%s/' %fixture_id
	response = requests.get(url, headers=headers)
	html = response.text
	soup = BeautifulSoup(html)
	for teams in soup.find_all('table'):
		teamname = str(teams.find('caption').string)

		for players in teams.find('tbody').find_all('tr'):
			playername = str(players.td.string.strip())
			if playername not in r.lrange('lineups:%s' %fixture_id, 0, -1):
				r.rpush('lineups:%s' %fixture_id, playername)


			
			r.hset(playername+':fresh','TEAMNAME',str(teamname))
			keys = ['MP', 'GS', 'A', 'CS', 'GC', 'OG', 'PS', 'PM', 'YC', 'RC','S', 'B', 'ESP', 'TP']
			i = 1
			for key in keys:
				r.hset(playername+':fresh', key, int(players.find_all('td')[i].string.strip()))
				i += 1

	#Begin Differential between Scrap & push
	diff_update = {}
	for players in r.lrange('lineups:%s' %fixture_id, 0, -1):
		if r.hexists(players+':old', 'MP'):
			old = r.hgetall(players+':old')
			fresh = r.hgetall(players+':fresh')
			if dict_diff(old,fresh):
				diff_update[players] = dict_diff(old,fresh)
				r.set('livefpl_status','live')
				push_data(players,dict_diff(old,fresh),fixture_id)
		else:
			r.rename(players+':fresh', players+':old')

	if diff_update:
		update_lineup_pts.delay(diff_update,fixture_id)
	
	if r.hexists(players+':fresh', 'MP'):
		for players in r.lrange('lineups:%s' %fixture_id, 0, -1):
			r.rename(players+':fresh', players+':old')


@celery.task(ignore_result=True)
def add_data_db(team_id):
	add_data(team_id,r.get('currentgw'))
	push_league(team_id)


@celery.task(ignore_result=True)
def update_lineup_pts(dict_update,fixture_id):
	print "This is the dict"
	print dict_update
	for player_update in dict_update:
		if 'TP' in dict_update[player_update] and player_update:
			for team_id in r.smembers('allteams'):
				old_gwpts = int(r.hget('team:%s'%team_id, 'gwpts'))
				old_tp = int(r.hget(player_update+':old', 'TP'))
				old_cappts = int(r.hget('team:%s'%team_id, 'cappts'))
				if player_update in r.lrange('team:%s:lineup'%team_id, 0, -5) and player_update != r.hget('team:%s'%team_id,'captain'):
					print "updating TP of %s in team %s by %s pts ( %s - %s )" % (player_update, team_id, int(dict_update[player_update]['TP']) - old_tp,int(dict_update[player_update]['TP']), old_tp )
					r.hincrby('team:%s'%team_id, 'gwpts', int(dict_update[player_update]['TP']) - old_tp) 
				elif player_update in r.lrange('team:%s:lineup'%team_id, 0, -5) and player_update == r.hget('team:%s'%team_id,'captain'):
					print "%s is Captain of %s" % (player_update, team_id)
					r.hset('team:%s'%team_id, 'cappts', 0)
					r.hincrby('team:%s'%team_id, 'cappts', (int(dict_update[player_update]['TP']))*2)
					

				if old_cappts != int(r.hget('team:%s'%team_id, 'cappts')):
					r.hincrby('team:%s'%team_id,'gwpts', -old_cappts)
					incr = int(r.hget('team:%s'%team_id, 'cappts'))
					print "capppts are diff %s & %s. Updating gwpts by %s"% (old_cappts, r.hget('team:%s'%team_id, 'cappts'), str(incr))
					r.hincrby('team:%s'%team_id,'gwpts', incr)


				if old_gwpts != int(r.hget('team:%s'%team_id, 'gwpts')):
					incr = int(r.hget('team:%s'%team_id, 'gwpts')) - old_gwpts 
					print "gwpts are different %s & %s. Updating totalpts by %s" %( old_gwpts , r.hget('team:%s'%team_id, 'gwpts'), str(incr))
					r.hincrby('team:%s'%team_id,'totalpts', incr)
