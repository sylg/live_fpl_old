from bs4 import BeautifulSoup
from push import *
import unicodedata
import requests
from settings import *

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
				if gw_pts != 0:
						total_pts = total_pts - gw_pts
						gw_pts = 0
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
		captain = str(soup2.find('dt').span.string).strip()
		vc = str(soup3.find('dt').span.string).strip()
		for row in soup1.find_all('tr'):
			r.rpush('team:%s:lineup'%teamid,str(row.td.string))

		r.hset('team:%s'%teamid, 'captain', captain )
		r.hset('team:%s'%teamid,'vc',vc)
		r.hset('team:%s'%teamid,'cappts',0)
		print "finished getting lineup for team %s"%teamid
	else:
		print "Error got status code:%s" % response.status_code
		print "retrying... for team: %s"%teamid
		getlineup(teamid, gw)

	

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
			if league_id not in r.hgetall('team:%s:leagues'%teamid):
				r.hset('team:%s:leagues'%teamid, league_id, 0)
	else:
		print "Error got status code:%s" % response.status_code
		print "retrying...for team: %s"%teamid
		get_classic_leagues(teamid,current_gw)

def add_data(teamid,current_gw):
	get_classic_leagues(teamid, current_gw)
	for league in r.hgetall('team:%s:leagues'%teamid):
		if r.exists('league:%s'%league) == False:
			getteams(league)
			if r.sismember('league:%s'%league, "toobig") == False:
				for team in r.smembers('league:%s'%league):
					getlineup(team,current_gw)
					update_gwpts(team)
		else:
			print "already exist"

def update_gwpts(team):
	if int(r.hget('team:%s'%team, 'gwpts')) == int(r.hget('team:%s'%team, 'scrapped_gwpts')) and r.get('livefpl_status') == 'Live'
	#if int(r.hget('team:%s'%team, 'gwpts')) == int(r.hget('team:%s'%team, 'scrapped_gwpts')):
		for players in r.lrange('team:%s:lineup'%team,0, -5):
			for ids in r.lrange('fixture_ids',0,-1):
				if rp.exists('%s:old:%s'%(players,ids)):
					if players != r.hget('team:%s'%team,'captain'):
						print "%s is a player, updating gwpts by %s"%(players, rp.hget('%s:old:%s'%(players,ids), 'TP'))
						r.hincrby('team:%s'%team, 'gwpts', rp.hget('%s:old:%s'%(players,ids), 'TP')) 
					elif players == r.hget('team:%s'%team,'captain'):
						print "%s is the captain, updating cappts by %s"%(players, rp.hget('%s:old:%s'%(players,ids), 'TP'))
						r.hincrby('team:%s'%team, 'cappts',  int(rp.hget('%s:old:%s'%(players,ids), 'TP'))*2)
					
		print "updating point of %s | gwpts by Capts ( %s ) and totalpts by gwpts ( %s ) "%(team,r.hget('team:%s'%team, 'cappts'),r.hget('team:%s'%team, 'gwpts') )
		r.hincrby('team:%s'%team, 'gwpts', int(r.hget('team:%s'%team, 'cappts')) )
		print "Gwpts for team %s is now %s pts"%(team,r.hget('team:%s'%team, 'gwpts'))
		r.hincrby('team:%s'%team, 'totalpts', int(r.hget('team:%s'%team, 'gwpts')) )
		print "totalpts for team %s is now %s pts"%(team,r.hget('team:%s'%team, 'totalpts'))
		for league in r.hgetall('team:%s:leagues'%team):
			r.hincrby('team:%s:leagues'%team, league, r.hget('team:%s'%team, 'gwpts') )
		print "finished update gwpts for team %s"%team
	else:
		if int(r.hget('team:%s'%team, 'gwpts')) != int(r.hget('team:%s'%team, 'scrapped_gwpts')):
			print "the gwpts and scrapped_gwpts are different "
		else:
			print "not updating because livefpl_status:%s"%r.get('livefpl_status')




