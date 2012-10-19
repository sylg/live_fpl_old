import pusher
import redis
from bs4 import BeautifulSoup
from push import *
import requests
from tasks import *
from classictable import *
from time import sleep

headers = {'User-agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}


def dict_diff(dict_a, dict_b):
    return dict([
        (key, dict_b.get(key, dict_a.get(key)))
        for key in set(dict_a.keys()+dict_b.keys())
        if (
            (key in dict_a and (not key in dict_b or dict_a[key] != dict_b[key])) or
            (key in dict_b and (not key in dict_a or dict_a[key] != dict_b[key]))
        )
    ])



def getteams(leagueid):
	url = 'http://fantasy.premierleague.com/my-leagues/%s/standings/' % leagueid
	response = urllib2.urlopen(url)
	html = response.read()
	tablestart = html.find('<!-- League tables -->')
	tableend = html.find('</section>')
	html = html[tablestart:tableend]
	soup = BeautifulSoup(html)
	if len(soup.find_all('tr')) <= 25:
		print "its good"
		for team in soup.find_all('tr'):

			if team.find('a') == None:
				continue
			teamname = str(team.find('a').string)
			team_id = int(team.a['href'].strip('/').split('/')[1])
			total_pts = int(team.td.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.string)
			gw_pts = int(team.td.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.string)
			r.sadd('league:%s'%leagueid, team_id)
			for team in r.smembers('league:%s'%leagueid):
				r.hmset('team:%s' %team_id,{'id':team_id, 'totalpts':total_pts, 'gwpts':gw_pts, 'teamname':teamname})
	else:
		print "not good"
		r.sadd('league:%s'%leagueid,"toobig")
		

def getlineup(teamid, gw):
	url = "http://fantasy.premierleague.com/entry/%s/event-history/%s/#ismDataView" % (teamid, gw)
	response = requests.get(url, headers=headers)
	html = response.text
	tablestart = html.find('<tbody id="ismDataElements">')
	tableend = html.find('<!-- sponsor -->')
	html = html[tablestart:tableend]
	soup = BeautifulSoup(html)
	for row in soup.find_all('tr'):
		r.hset('team:%s:lineup'%teamid,str(row.td.string), 0) 
	

def get_classic_leagues(teamid,current_gw):
	url = "http://fantasy.premierleague.com/entry/%s/event-history/%s/" % (teamid, current_gw)
	response = requests.get(url)
	html = response.read()
	tablestart = html.find('<h2 class="ismTableHeading">Classic leagues</h2>')
	tableend = html.find('<h2 class="ismTableHeading">Head-to-Head leagues</h2>')
	html = html[tablestart:tableend]
	soup = BeautifulSoup(html)

	for leagueid in soup.find_all('a'):
		leagueurl = leagueid.get('href')
		r.hset('team:%s:cleagues'%teamid,str(leagueid.get_text().strip()), str(leagueurl.strip('/').split('/')[1]))


def add_data(teamid,current_gw):
	get_classic_leagues(teamid, current_gw)
	for league in r.hvals('team:%s:cleagues'%teamid):
		getteams(league)
		if r.sismember('league:%s'%league, "toobig") == 0:
			for team in r.smembers('league:%s'%league):
				getlineup(team,current_gw)
				get_classic_leagues(team,current_gw)


def scrapper(fixture_id):
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


			
			r.hset(playername+':fresh:'+str(fixture_id),'TEAMNAME',str(teamname))
			keys = ['MP', 'GS', 'A', 'CS', 'GC', 'OG', 'PS', 'PM', 'YC', 'RC','S', 'B', 'ESP', 'TP']
			i = 1
			for key in keys:
				r.hset(playername+':fresh:'+str(fixture_id), key, int(players.find_all('td')[i].string.strip()))
				i += 1

	#Begin Differential between Scrap & push
	diff_update = {}
	for players in r.lrange('lineups:%s' %fixture_id, 0, -1):
		if r.hexists(players+':old:%s' %fixture_id, 'MP') == 1:
			old = r.hgetall(players+':old:%s' %fixture_id)
			fresh = r.hgetall(players+':fresh:%s' %fixture_id)
			if dict_diff(old,fresh):
				diff_update[players] = dict_diff(old,fresh)
				r.set('livefpl_status','live')
				push_data(players,dict_diff(old,fresh),fixture_id)
				
		else:
			r.rename(players+':fresh:%s' %fixture_id, players+':old:%s' %fixture_id)
			for team_id in r.smembers('allteams'):
				if r.hexists('team:%s:lineup'%team_id, players) and int(r.hget(players+':old:'+str(fixture_id), 'TP')) != 0: 
					r.hincrby('team:%s'%team_id, 'gwpts', int(r.hget(players+':old:'+str(fixture_id), 'TP')) ) 
	if diff_update:
		update_lineup_pts.delay(diff_update,fixture_id)
				

# print "deleting Old data..."
# for players in r.lrange('lineups:63' , 0, -1):
# 	if r.hexists(players+':old:63' , 'MP'):
# 		r.delete(players+':old:63' )

r.hset("Yaya Toure:old:63", "TP", 1)
r.hset("Hart:old:63", "TP", 1)
r.hset("Tezvez:old:63", "TP", 1)
r.hset("Milner:old:63", "TP", 1)

for team in r.smembers('allteams'):
	r.hset('team:%s'%team, 'gwpts', 0)

scrapper(63)
sleep(5)
for team in r.smembers('allteams'):
	print r.hgetall('team:%s'% team)







