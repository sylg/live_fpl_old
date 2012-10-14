import pusher
import redis
from bs4 import BeautifulSoup
from push import *
import requests

headers = {'User-agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}


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



getlineup(37828,7)




# for team in r.smembers('league:29613'):
# 	r.delete('team:%s'%team)

#league = sorted(league.items(), key= lambda x: x[1]['totalpts'], reverse=True)