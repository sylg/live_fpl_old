from celery import Celery
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



@periodic_task(run_every=crontab(minute='0',hour='11',day_of_week='sat'),ignore_result=True)
def cleandb():
	r.flushdb()
	rp.flushdb()
	print "Done Flushing the db. for new GW"

@periodic_task(run_every=crontab(minute='0', hour='0', day_of_week='sat'),ignore_result=True)
def fill_playerdb():
	i = 0
	no_more = 0
	while i <= 622 and no_more <= 5:
		url = "http://fantasy.premierleague.com/web/api/elements/%s/" %i
		response = requests.get(url, headers=headers)
		if response.status_code == 200:
			json = response.json
			web_name = json['web_name']
			position = json['type_name']
			teamname = json['team_name']
	 		rdb.hmset(i,{'web_name':web_name, 'position':position,'teamname':teamname})
	 		rdb.rpush('player_ids', i)
	 	elif response.status_code == 500:
	 		no_more +=1
		i += 1
	print "Done updating Player Database"



@periodic_task(run_every=timer,ignore_result=True)
def fplupdating():
	url = 'http://fantasy.premierleague.com/fixtures/'
	response = requests.get(url, headers=headers)
	if len(response.history) != 0:
		print "livefpl website is updating do nothing"
		r.set('scrapmode', 'OFF')
	else:
		print "livefpl website is live, go scrap"
		r.set('scrapmode', 'ON')

		url = "http://fantasy.premierleague.com/"
		br = mechanize.Browser()
		br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
		br.open(url)
		br.select_form(nr=0)
		br.form['email'] = "baboo2@yopmail.com"
		br.form['password'] = "bibi2000"
		br.submit()
		html = br.back().read()
		html2 = html

		start = html.find('<table class="ismTable ismEventStatus ismHomeMarginTop">')
		stop =  html.find('<div class="ismHomeMarginTop">')
		html = html[start:stop]
		soup = BeautifulSoup(html)
		if "Live" in [str(td.string) for td in soup.find_all('td', {'class':'ismInProgress'})]:
			r.set('livefpl_status','Live')
		else:
			r.set('livefpl_status','Offline')

		start2 = html2.find('ismMegaLarge')
		html2 = html2[start2+14:start2+25]
		currentgw = re.findall(r"\d{1,2}", html2)[0]
		r.set('currentgw',currentgw)

		url = "http://fantasy.premierleague.com/fixtures/"
		response = requests.get(url,headers=headers)
		html = response.text
		tablestart = html.find('<div id="ism" class="ism">')
		tableend = html.find('<aside class="ismAside">')
		html = html[tablestart:tableend]
		soup = BeautifulSoup(html)
		newgw = re.findall(r"\d{1,2}",str(soup.find('caption','ismStrongCaption').string))[0]
		r.set('newgw',newgw)



# @celery.task(ignore_result=True)
# def getgw():
# 	url = "http://fantasy.premierleague.com/"
# 	br = mechanize.Browser()
# 	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
# 	br.open(url)
# 	br.select_form(nr=0)
# 	br.form['email'] = "baboo2@yopmail.com"
# 	br.form['password'] = "bibi2000"
# 	br.submit()
# 	html = br.back().read()
# 	start = html.find('ismMegaLarge')
# 	html = html[start+14:start+25]
# 	currentgw = re.findall(r"\d{1,2}", html)[0]
# 	r.set('currentgw',currentgw)

# @celery.task(ignore_result=True)
# def livefpl_status():
# 	url = "http://fantasy.premierleague.com/"
# 	br = mechanize.Browser()
# 	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
# 	br.open(url)
# 	br.select_form(nr=0)
# 	br.form['email'] = "baboo2@yopmail.com"
# 	br.form['password'] = "bibi2000"
# 	br.submit()
# 	html = br.back().read()
	
# 	start = html.find('<table class="ismTable ismEventStatus ismHomeMarginTop">')
# 	stop =  html.find('<div class="ismHomeMarginTop">')
# 	html = html[start:stop]
# 	soup = BeautifulSoup(html)
# 	if "Live" in [str(td.string) for td in soup.find_all('td', {'class':'ismInProgress'})]:
# 		r.set('livefpl_status','Live')
# 	else:
# 		r.set('livefpl_status','Offline')

@periodic_task(run_every=timer, ignore_result=True)
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


@periodic_task(run_every=timerslow, ignore_result=True)
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
			pid = 0
			playername = str(players.td.string.strip())
			for ids in rdb.lrange('player_ids',0,-1):
				if playername == rdb.hget(ids, 'web_name') and teamname == rdb.hget(ids, 'teamname'):
					pid = ids
			if pid not in r.lrange('lineups:%s' %fixture_id, 0, -1):
				r.rpush('lineups:%s' %fixture_id, pid)



			
			rp.hset('%s:fresh'%pid,'TEAMNAME',str(teamname))
			keys = ['MP', 'GS', 'A', 'CS', 'GC', 'OG', 'PS', 'PM', 'YC', 'RC','S', 'B', 'ESP', 'TP']
			i = 1
			for key in keys:
				rp.hset('%s:fresh'%pid, key, int(players.find_all('td')[i].string.strip()))
				i += 1

	#Begin Differential between Scrap & push
	diff_update = {}
	scrapped_data = {}
	for pid in r.lrange('lineups:%s' %fixture_id, 0, -1):
		if rp.hexists('%s:old'%pid, 'MP'):
			old = rp.hgetall('%s:old'%pid)
			fresh = rp.hgetall('%s:fresh'%pid)
			dictdiff = dict_diff(old,fresh)
			if dictdiff:
				diff_update[pid] = dictdiff
				dictdiff['playername'] =rdb.hget(pid,'web_name')
				push_data(pid,dictdiff)
		else:
			scrapped_data[pid] = rp.hgetall('%s:fresh'%pid)



	if diff_update:
		update_lineup_pts.delay(diff_update, "diff_update")
	if scrapped_data:
		update_lineup_pts.delay(scrapped_data, "1st scrap")

@celery.task(ignore_result=True)
def add_data_db(team_id):
	add_data(team_id,r.get('currentgw'))
	push_league(team_id)


@celery.task(ignore_result=True)
def update_lineup_pts(dict_update, who):
	print "This is the dict from %s"%who
	print dict_update
	for pid in dict_update:
		if 'TP' in dict_update[pid]:
			for team_id in r.smembers('allteams'):
				old_gwpts = int(r.hget('team:%s'%team_id, 'gwpts'))
				old_cappts = int(r.hget('team:%s'%team_id, 'cappts'))

				if r.exists('%s:old'%pid):
					old_tp = int(rp.hget('%s:old'%pid, 'TP'))
				else:
					old_tp = 0

				if pid in r.lrange('team:%s:lineup'%team_id, 0, -5) and pid != r.hget('team:%s'%team_id,'captain'):
					print "%s is a player of team %s increasing by"%(pid, team_id)
					print int(dict_update[pid]['TP']) - old_tp
					r.hincrby('team:%s'%team_id, 'gwpts', int(dict_update[pid]['TP']) - old_tp ) 
				elif pid in r.lrange('team:%s:lineup'%team_id, 0, -5) and pid == r.hget('team:%s'%team_id,'captain'):
					r.hset('team:%s'%team_id, 'cappts', 0)
					print "%s is the captaion increasing cappts by:"%pid
					print int(dict_update[pid]['TP'])*2
					r.hincrby('team:%s'%team_id, 'cappts', int(dict_update[pid]['TP'])*2)
					
				if old_cappts != int(r.hget('team:%s'%team_id, 'cappts')):
					incr = int(r.hget('team:%s'%team_id, 'cappts')) - old_cappts
					r.hincrby('team:%s'%team_id,'gwpts', incr)

				if old_gwpts != int(r.hget('team:%s'%team_id, 'gwpts')):
					incr = int(r.hget('team:%s'%team_id, 'gwpts')) - old_gwpts 
					r.hincrby('team:%s'%team_id,'totalpts', incr)
					for league in r.hgetall('team:%s:leagues'%team_id):
						r.hincrby('team:%s:leagues'%team_id, league, incr)

		print "renaming %s fresh > old"%pid
		rp.rename('%s:fresh'%pid,'%s:old'%pid)
	print "done Updating the %s teams in DB."%len(r.smembers('allteams'))
