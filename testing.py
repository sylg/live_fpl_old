import pusher
import redis
from bs4 import BeautifulSoup
from push import *
import requests
from tasks import *
from classictable import *

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



def getcap(teamid, gw):
	url = "http://fantasy.premierleague.com/entry/38861/event-history/8/"
	response = requests.get(url)
	html = response.text
	tablestart = html.find('<img width="16" height="16" alt="captain" src="http://cdn.ismfg.net/static/plfpl/img/icons/captain.png" title="captain" class="ismCaptain ismCaptainOn">')
	tableend = html.find('<!-- end ismPitch -->')
	soup = BeautifulSoup(html[tablestart:tableend])
	print str(soup.find('dt').span.string).strip()
		#r.rpush('team:%s:lineup'%teamid,str(row.td.string)) 
	

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



getlineup(38861,8)