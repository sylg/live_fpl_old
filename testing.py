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
	teams = []
	for team in soup.find_all('tr'):
		for data in team.find_all('td'):
			print data.string

getteams(48483)