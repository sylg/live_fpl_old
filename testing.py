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
	league = []

	for team in soup.find_all('tr'):
		if team.find('a') == None:
			continue
		teamnanme = str(team.find('a').string)
		team_id = int(team.a['href'].strip('/').split('/')[1])
		total_pts = int(team.td.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.string)
		league.append([total_pts,{'id':team_id, 'teamnanme':teamnanme}])

		
	print league
getteams(48483)