from bs4 import BeautifulSoup
from push import *
import unicodedata
import requests
from settings import *
import re
import pickle

def getteams(leagueid):
	url = 'http://fantasy.premierleague.com/my-leagues/%s/standings/' % leagueid
	response = requests.get(url, headers=headers)
	if response.status_code == 200:
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
				r.hset('team:%s:leagues'%team_id,leagueid, total_pts)
				if r.exists('team:%s'%team_id) == False:
					r.hmset('team:%s' %team_id,{'id':team_id, 'totalpts':total_pts, 'gwpts':gw_pts, 'teamname':teamname,'scrapped_gwpts':gw_pts})
		else:
			print "Too big. Skip."
			r.sadd('league:%s'%leagueid,"toobig")
			r.hset('league:%s:info'%leagueid,"players", 0)
	else:
			print "Error got status code:%s" % response.status_code
			print "Cant retry because I'm in getteams"		

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
		vcstart =html.find('<img width="16" height="16" alt="vice-captain" src="http://cdn.ismfg.net/static/plfpl/img/icons/vice_captain.png" title="vice-captain" class="ismViceCaptain ismViceCaptainOn">')
		vcend =html.find('<!-- end ismPitch -->')
		soup3 = BeautifulSoup(html[vcstart:vcend])
		captain = str(soup2.find('a')['href'].strip('#'))
		vc = str(soup3.find('a')['href'].strip('#'))
		lineup = []
		for row in soup1.find_all('tr'):
			r.rpush('team:%s:lineup'%teamid,re.findall(r"\d{1,3}", row["id"])[0])

		r.hset('team:%s'%teamid, 'captain', captain )
		r.hset('team:%s'%teamid,'vc',vc)
		r.hset('team:%s'%teamid,'cappts',0)
		print "finished getting lineup for team %s"%teamid
	else:
		print "Error got status code:%s" % response.status_code
		print "retrying... for team: %s"%teamid
		getlineup(teamid, gw)

	

def get_leagues(teamid,current_gw):
	url = "http://fantasy.premierleague.com/entry/%s/event-history/%s/" % (teamid, current_gw)
	response = requests.get(url, headers=headers)
	if response.status_code == 200:
		print response.status_code
		html = response.text
		tablestart = html.find('<h2 class="ismTableHeading">Classic leagues</h2>')
		tableend = html.find('<h2 class="ismTableHeading">Head-to-Head leagues</h2>')
		html1 = html[tablestart:tableend]
		soup = BeautifulSoup(html1)
		tablestart2 = html.find('<h2 class="ismTableHeading">Head-to-Head leagues</h2>')
		tableend2 = html.find('<h2 class="ismTableHeading">Global leagues</h2>')
		html2 = html[tablestart2:tableend2]
		soup2 = BeautifulSoup(html2)

		#classic Leagues
		for leagueid in soup.find_all('a'):
			leaguename = unicodedata.normalize('NFKD',leagueid.get_text().strip()).encode('ascii','ignore')
			leagueurl = leagueid.get('href')
			league_id = str(leagueurl.strip('/').split('/')[1])
			if r.exists('league:%s:info'%league_id) == False:
				r.hmset('league:%s:info'%league_id, {'leaguename': leaguename, 'type':'classic', 'id':league_id })
			if league_id not in r.hgetall('team:%s:leagues'%teamid):
				r.hset('team:%s:leagues'%teamid, league_id, 0)

		#H2H Leagues
		if len(soup2.find_all('a')) != 0:
			for leagueid in soup2.find_all('a'):
				leaguename = unicodedata.normalize('NFKD',leagueid.get_text().strip()).encode('ascii','ignore')
				leagueurl = leagueid.get('href')
				league_id = str(leagueurl.strip('/').split('/')[1])
				if r.exists('league:%s:info'%league_id) == False:
					r.hmset('league:%s:info'%league_id, {'leaguename': leaguename, 'type':'h2h', 'id':league_id })
				if league_id not in r.hgetall('team:%s:leagues'%teamid):
					r.hset('team:%s:leagues'%teamid, league_id, 0)
		else:
			print "team %s has no H2H leagues"%teamid

	else:
		print "Error got status code:%s" % response.status_code
		print "retrying...for team: %s"%teamid
		get_leagues(teamid,current_gw)

def add_data(teamid,current_gw):
	get_leagues(teamid, current_gw)
	for league in r.hgetall('team:%s:leagues'%teamid):
		if r.exists('league:%s'%league) == False:
			getteams(league)
			if r.sismember('league:%s'%league, "toobig") == False:
				for team in r.smembers('league:%s'%league):
					getlineup(team,current_gw)
					if r.get('currentgw') == r.get('newgw'):
						# We are in the GW, update the new team with the new data
						if r.hget('team:%s'%team, 'gwpts') != 0:
							# If its the 2nd or 3rd day of the GW, reset totalpts in team and league hash and update teams totalpts.
							gwpts = int(r.hget('team:%s'%team, 'gwpts'))
							r.hincrby('team:%s'%team, 'totalpts', - gwpts)
							print "total pts for %s is now %s"%(team, r.hget('team:%s'%team,'totalpts'))
							r.hincrby('team:%s:leagues'%team,league, - gwpts )
							print "total pts for %s in %s is now %s"%(team, league, r.hget('team:%s:leagues'%team,league))
							r.hincrby('team:%s'%team,'gwpts', - gwpts )
						update_gwpts(team)
					else:
						print "the GW hasn't started / Switched. Leaving the data from FPL"


		else:
			print "already exist"

def update_gwpts(team):
	for players in r.lrange('team:%s:lineup'%team,0, -5):
		if rp.exists('%s:old'%players):
			if players != r.hget('team:%s'%team,'captain'):
				print "%s is a player, updating gwpts by %s"%(players, rp.hget('%s:old'%players, 'TP'))
				r.hincrby('team:%s'%team, 'gwpts', rp.hget('%s:old'%players, 'TP')) 
			elif players == r.hget('team:%s'%team,'captain'):
				print "%s is the captain, updating cappts by %s"%(players, rp.hget('%s:old'%players, 'TP'))
				r.hincrby('team:%s'%team, 'cappts',  int(rp.hget('%s:old'%players, 'TP'))*2)
				
	print "updating point of %s | gwpts by Capts ( %s ) and totalpts by gwpts ( %s ) "%(team,r.hget('team:%s'%team, 'cappts'),r.hget('team:%s'%team, 'gwpts') )
	r.hincrby('team:%s'%team, 'gwpts', int(r.hget('team:%s'%team, 'cappts')) )
	print "Gwpts for team %s is now %s pts"%(team,r.hget('team:%s'%team, 'gwpts'))
	r.hincrby('team:%s'%team, 'totalpts', int(r.hget('team:%s'%team, 'gwpts')) )
	print "totalpts for team %s is now %s pts"%(team,r.hget('team:%s'%team, 'totalpts'))
	for league in r.hgetall('team:%s:leagues'%team):
		r.hincrby('team:%s:leagues'%team, league, r.hget('team:%s'%team, 'gwpts') )
	print "finished update gwpts for team %s"%team



