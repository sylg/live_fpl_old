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
		vcstart =html.find('<img width="16" height="16" alt="vice-captain" src="http://cdn.ismfg.net/static/plfpl/img/icons/vice_captain.png" title="vice-captain" class="ismViceCaptain ismViceCaptainOn">')
		vcend =html.find('<!-- end ismPitch -->')
		soup3 = BeautifulSoup(html[vcstart:vcend])
		captain = str(soup2.find('dt').span.string).strip()
		vc = str(soup3.find('dt').span.string).strip()
		for row in soup1.find_all('tr'):
			r.rpush('team:%s:lineup'%teamid,str(row.td.string))
		r.hset('team:%s'%teamid, 'captain', captain )
		r.hset('team:%s'%teamid,'vc',vc)
	else:
		print "Error got status code:%s" % response.status_code



def vc(teamid):
	cap = r.hget('team:%s'%teamid, 'captain')
	vc = r.hget('team:%s'%teamid, 'vc')
	capmp = 0
	vcmp = 0
	capfid = 0
	vcfid = 0
	for fixture_id in r.lrange('fixture_ids',0,-1):

		if cap in r.lrange('lineups:%s'%fixture_id,0,-5):
			capmp = r.hget('%s:old:%s'%(cap,fixture_id), 'MP')
			capfid = fixture_id

		if vc in r.lrange('lineups:%s'%fixture_id, 0, -5):
			vcmp = r.hget('%s:old:%s'%(vc,fixture_id), 'MP')
			vcfid = fixture_id

	if capmp == 0 and vcmp > 0:
		r.hincrby('team:%s'%team_id, 'cappts', r.hget('%s:old:%s'%(vc,vcfid), 'T')*2)
	else:
		r.hincrby('team:%s'%team_id, 'cappts', r.hget('%s:old:%s'%(cap,capfid), 'T')*2)


def reset():
	for teamid in r.smembers('allteams'):
		r.hset('team:%s'%teamid,'cappts',0)
		print "changed cappts of %s"%teamid

reset()