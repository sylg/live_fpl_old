import redis
from bs4 import BeautifulSoup
from push import *
import unicodedata
import requests

headers = {'User-agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}

def getteams(leagueid):
	url = 'http://fantasy.premierleague.com/my-leagues/%s/standings/' % leagueid
	response = requests.get(url, headers=headers)
	html = response.text
	tablestart = html.find('<!-- League tables -->')
	tableend = html.find('</section>')
	html = html[tablestart:tableend]
	soup = BeautifulSoup(html)
	if len(soup.find_all('tr')) <= 25:
		print "Scrapping..."
		for team in soup.find_all('tr'):

			if team.find('a') == None:
				continue
			teamname = unicodedata.normalize('NFKD', team.find('a').string).encode('ascii','ignore')
			team_id = int(team.a['href'].strip('/').split('/')[1])
			total_pts = int(team.td.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.string)
			gw_pts = int(team.td.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.string)
			r.sadd('league:%s'%leagueid, team_id)
			r.sadd('allteams', team_id)
			r.hset('league:%s:info'%leagueid, 'players', r.scard('league:%s'%leagueid))
			for team in r.smembers('league:%s'%leagueid):
				if r.exists('team:%s'%team) == False:
					r.hmset('team:%s' %team_id,{'id':team_id, 'totalpts':total_pts, 'gwpts':gw_pts, 'teamname':teamname})

	else:
		print "Too big. Skip."
		r.sadd('league:%s'%leagueid,"toobig")
		r.hset('league:%s:info'%leagueid,"players", 0)
		

def getlineup(teamid, gw):
	url = "http://fantasy.premierleague.com/entry/%s/event-history/%s/" % (teamid, gw)
	response = requests.get(url, headers=headers)
	if response.status_code == 200:
		html = response.text
		tablestart = html.find('<tbody id="ismDataElements">')
		tableend = html.find('<!-- sponsor -->')
		soup1 = BeautifulSoup(html[tablestart:tableend])
		capstart = html.find('<img width="16" height="16" alt="captain" src="http://cdn.ismfg.net/static/plfpl/img/icons/captain.png" title="captain" class="ismCaptain ismCaptainOn">')
		capend = html.find('<!-- end ismPitch -->')
		soup2 = BeautifulSoup(html[capstart:capend]) 
		captain = str(soup2.find('dt').span.string).strip()
		for row in soup1.find_all('tr'):
			r.rpush('team:%s:lineup'%teamid,str(row.td.string))
			r.hset('team:%s'%teamid, 'captain', captain )
	else:
		print "Error got status code:%s" % response.status_code

	

def get_classic_leagues(teamid,current_gw):
	url = "http://fantasy.premierleague.com/entry/%s/event-history/%s/" % (teamid, current_gw)
	response = requests.get(url, headers=headers)
	if response.status_code == 200:
		print response.status_code
		html = response.text
		tablestart = html.find('<h2 class="ismTableHeading">Classic leagues</h2>')
		tableend = html.find('<h2 class="ismTableHeading">Head-to-Head leagues</h2>')
		html = html[tablestart:tableend]
		soup = BeautifulSoup(html)

		for leagueid in soup.find_all('a'):
			leaguename = unicodedata.normalize('NFKD',leagueid.get_text().strip()).encode('ascii','ignore')
			leagueurl = leagueid.get('href')
			league_id = str(leagueurl.strip('/').split('/')[1])
			if r.exists('league:%s:info'%league_id) == False:
				r.hmset('league:%s:info'%league_id, {'leaguename': leaguename, 'type':'classic', 'id':league_id })
			if league_id not in r.smembers('team:%s:leagues'%teamid):
				r.sadd('team:%s:leagues'%teamid, league_id)
	else:
		print "Error got status code:%s" % response.status_code


def add_data(teamid,current_gw):
	get_classic_leagues(teamid, current_gw)
	for league in r.smembers('team:%s:leagues'%teamid):
		if r.exists('league:%s'%league) == False:
			print "league %s doesn't exists"% league
			getteams(league)
			if r.sismember('league:%s'%league, "toobig") == False:
				for team in r.smembers('league:%s'%league):
					getlineup(team,current_gw)
		else:
			print "already exist"