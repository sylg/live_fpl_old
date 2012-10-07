import pusher
import redis
from bs4 import BeautifulSoup
import urllib2
from push import *


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
		

getteams(29613)


# for team in r.smembers('league:29613'):
# 	r.delete('team:%s'%team)

#league = sorted(league.items(), key= lambda x: x[1]['totalpts'], reverse=True)