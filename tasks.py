from celery import Celery
from datetime import timedelta
from celery.schedules import crontab
from celery.decorators import periodic_task
from bs4 import BeautifulSoup
import requests
from push import *
from classictable import *
from settings import *
import re
import mechanize

celery = Celery('tasks', broker=redis_url, backend=redis_url)

def dict_diff(dict_a, dict_b):
    return dict([
        (key, dict_b.get(key, dict_a.get(key)))
        for key in set(dict_a.keys()+dict_b.keys())
        if (
            (key in dict_a and (not key in dict_b or dict_a[key] != dict_b[key])) or
            (key in dict_b and (not key in dict_a or dict_a[key] != dict_b[key]))
        )
    ])


@periodic_task(run_every=crontab(minute='10'),ignore_result=True)
def fplupdating():
	url = 'http://fantasy.premierleague.com/fixtures/'
	response = requests.get(url, headers=headers)
	if len(response.history) != 0:
		print "livefpl website is updating do nothing"
		r.set('scrapmode', 'OFF')
	else:
		print "livefpl website is live, go scrap"
		r.set('scrapmode', 'ON')
		livefpl_status.delay()
		getgw.delay()

@celery.task(ignore_result=True)
def getgw():
	url = "http://fantasy.premierleague.com/"
	br = mechanize.Browser()
	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
	br.open(url)
	br.select_form(nr=0)
	br.form['email'] = "baboo2@yopmail.com"
	br.form['password'] = "bibi2000"
	br.submit()
	html = br.back().read()
	start = html.find('ismMegaLarge')
	html = html[start+14:start+25]
	currentgw = re.findall(r"\d{1,2}", html)[0]
	r.set('currentgw',currentgw)

@celery.task(ignore_result=True)
def livefpl_status():
	url = "http://fantasy.premierleague.com/"
	br = mechanize.Browser()
	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
	br.open(url)
	br.select_form(nr=0)
	br.form['email'] = "baboo2@yopmail.com"
	br.form['password'] = "bibi2000"
	br.submit()
	html = br.back().read()
	
	start = html.find('<table class="ismTable ismEventStatus ismHomeMarginTop">')
	stop =  html.find('<div class="ismHomeMarginTop">')
	html = html[start:stop]
	soup = BeautifulSoup(html)
	if "Live" in [str(td.string) for td in soup.find_all('td', {'class':'ismInProgress'})]:
		r.set('livefpl_status','Live')
	else:
		r.set('livefpl_status','Offline')

@periodic_task(run_every=crontab(minute='*',hour='10-21',day_of_week='saturday,sunday,monday,tuesday'), ignore_result=True)
def get_fixture_ids():
	if r.get('scrapmode') == 'ON' and r.get('livefpl_status') == 'Live':
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


@periodic_task(run_every=crontab(minute='*', hour='10-22',day_of_week='saturday,sunday,monday,tuesday,wednesday,thursday'), ignore_result=True)
def create_scrapper():
	if r.llen('fixture_ids') != 0 and r.get('livefpl_status') == 'Live':
		for ids in r.lrange('fixture_ids',0, -1):
			scrapper.delay(ids)

@celery.task(ignore_result=True)
def scrapper(fixture_id):
	#url = 'http://0.0.0.0:5001/fixture/%s/'%fixture_id
	url = 'http://fantasy.premierleague.com/fixture/%s/' %fixture_id
	response = requests.get(url, headers=headers)
	html = response.text
	soup = BeautifulSoup(html)
	for teams in soup.find_all('table'):
		teamname = str(teams.find('caption').string)

		for players in teams.find('tbody').find_all('tr'):
			playername = str(players.td.string.strip())
			if playername not in r.lrange('lineups:%s' %fixture_id, 0, -1):
				r.rpush('lineups:%s' %fixture_id, playername)


			
			rp.hset(playername+':fresh:%s'%fixture_id,'TEAMNAME',str(teamname))
			keys = ['MP', 'GS', 'A', 'CS', 'GC', 'OG', 'PS', 'PM', 'YC', 'RC','S', 'B', 'ESP', 'TP']
			i = 1
			for key in keys:
				rp.hset(playername+':fresh:%s'%fixture_id, key, int(players.find_all('td')[i].string.strip()))
				i += 1

	#Begin Differential between Scrap & push
	diff_update = {}
	scrapped_data = {}
	for players in r.lrange('lineups:%s' %fixture_id, 0, -1):
		if rp.hexists('%s:old:%s'%(players,fixture_id), 'MP'):
			print "old hash for %s exist checking if there's a dif."%players
			old = rp.hgetall(players+':old:%s'%fixture_id)
			fresh = rp.hgetall(players+':fresh:%s'%fixture_id)
			if dict_diff(old,fresh):
				print "there's a diff. Pushing."
				diff_update[players] = dict_diff(old,fresh)
				push_data(players,dict_diff(old,fresh),fixture_id)
			else:
				print "no diff. Not pushing"
		else:
			print "old hash for %s doesn't exist. Renaming."%players
			scrapped_data[players] = rp.hgetall(players+':fresh:%s'%fixture_id)
			print "adding 1st scrap data for %s to scrapped_data"%players


	if diff_update:
		update_lineup_pts.delay(diff_update,fixture_id, "diff_update")
	if scrapped_data:
		update_lineup_pts.delay(scrapped_data,fixture_id, "1st scrap")

@celery.task(ignore_result=True)
def add_data_db(team_id):
	add_data(team_id,r.get('currentgw'))
	push_league(team_id)


@celery.task(ignore_result=True)
def update_lineup_pts(dict_update,fixture_id, who):
	print "This is the dict from %s"%who
	print dict_update
	for player_update in dict_update:
		if 'TP' in dict_update[player_update]:
			for team_id in r.smembers('allteams'):
				old_gwpts = int(r.hget('team:%s'%team_id, 'gwpts'))

				if rp.exists(player_update+':old:%s'%fixture_id):
					old_tp = int(rp.hget(player_update+':old:%s'%fixture_id, 'TP'))
				else:
					old_tp = 0

				old_cappts = int(r.hget('team:%s'%team_id, 'cappts'))
				if player_update in r.lrange('team:%s:lineup'%team_id, 0, -5) and player_update != r.hget('team:%s'%team_id,'captain'):
					print "increasing gwpts of team %s by %s pts"%(team_id, dict_update[player_update]['TP'])
					r.hincrby('team:%s'%team_id, 'gwpts', int(dict_update[player_update]['TP']) - old_tp ) 
				elif player_update in r.lrange('team:%s:lineup'%team_id, 0, -5) and player_update == r.hget('team:%s'%team_id,'captain'):
					r.hset('team:%s'%team_id, 'cappts', 0)
					r.hincrby('team:%s'%team_id, 'cappts', int(dict_update[player_update]['TP'])*2)
					

				if old_cappts != int(r.hget('team:%s'%team_id, 'cappts')):
					r.hincrby('team:%s'%team_id,'gwpts', -old_cappts)
					incr = int(r.hget('team:%s'%team_id, 'cappts'))
					r.hincrby('team:%s'%team_id,'gwpts', incr)


				if old_gwpts != int(r.hget('team:%s'%team_id, 'gwpts')):
					incr = int(r.hget('team:%s'%team_id, 'gwpts')) - old_gwpts 
					print "increasing team %s by %s"%(team_id, incr)
					r.hincrby('team:%s'%team_id,'totalpts', incr)
					for league in r.hgetall('team:%s:leagues'%team_id):
						r.hincrby('team:%s:leagues'%team_id, league, incr)
		rp.rename(player_update+':fresh:%s'%fixture_id, player_update+':old:%s'%fixture_id)

	print "done Updating the %s teams in DB."%len(r.smembers('allteams'))

