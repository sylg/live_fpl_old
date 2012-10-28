import pusher
import redis
from bs4 import BeautifulSoup
from push import *
import requests
from tasks import *
from classictable import *
import mechanize
import re

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
			print str(row.td.string)
		print "captation is %s"%captain
		print "vc is %s"%vc
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



def update_gwpts(team):
	print "adding gwpts for team %s ..."%team
	for players in r.lrange('team:%s:lineup'%team,0, -5):
		for ids in r.lrange('fixture_ids',0,-1):
			if rp.exists('%s:old:%s'%(players,ids)):
				print "%s is in the %s"%(players,ids)
				if players != r.hget('team:%s'%team,'captain'):
					print "%s is player with %s TP"%(players,rp.hget('%s:old:%s'%(players,ids), 'TP'))
					r.hincrby('team:%s'%team, 'gwpts', rp.hget('%s:old:%s'%(players,ids), 'TP')) 
				elif players == r.hget('team:%s'%team,'captain'):
					print "%s is the captaion with %s TP"%(players, int(rp.hget('%s:old:%s'%(players,ids), 'TP'))*2)
					r.hset('team:%s'%team, 'cappts', 0)
					r.hincrby('team:%s'%team, 'cappts',  int(rp.hget('%s:old:%s'%(players,ids), 'TP'))*2)
				r.hincrby('team:%s'%team, 'totalpts', r.hget('team:%s'%team, 'gwpts') )
	print "Gwpts : (%s + %s ) pts & totalpts : %s pts"%(int(r.hget('team:%s'%team, 'gwpts')), int(r.hget('team:%s'%team, 'cappts')), r.hget('team:%s'%team, 'totalpts'))


def getgw():
	url = "http://fantasy.premierleague.com/"
	br = mechanize.Browser()
	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
	br.open(url)
	br.select_form(nr=0)
	br.form['email'] = "baboo2@yopmail.com"
	br.form['password'] = "bibi2000"
	br.submit()
	html = br.back().read()
	#soup = BeautifulSoup(html)
	start = html.find('ismMegaLarge')
	html = html[start+14:start+25]
	currentgw = re.findall(r"\d{1,2}", html)[0]
	r.set('currentgw',currentgw)
	
getgw()

getlineup(37828,r.get('currentgw'))

