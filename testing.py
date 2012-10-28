import pusher
import redis
from bs4 import BeautifulSoup
from push import *
import requests
from tasks import *
from classictable import *
import mechanize
import re
from settings import *

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


def livefpl_status():
	url = "http://fantasy.premierleague.com/"
	br = mechanize.Browser()
	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
	br.open(url)
	br.select_form(nr=0)
	br.form['email'] = "baboo2@yopmail.com"
	br.form['password'] = "bibi2000"
	br.submit()
	html = br.back().read()
	
	start = html.find('<table class="ismTable ismEventStatus ismHomeMarginTop">')
	stop =  html.find('<div class="ismHomeMarginTop">')
	html = html[start:stop]
	soup = BeautifulSoup(html)
	if "Live" in [str(td.string) for td in soup.find_all('td', {'class':'ismFinished'})]:
		r.set('livefpl_status','Offline')
	else:
		r.set('livefpl_status','Live')

	# soup.prettify()
	

def fplupdating():
	url = 'http://fantasy.premierleague.com/fixtures/'
	response = requests.get(url, headers=headers)
	if len(response.history) != 0:
		print "livefpl website is updating do nothing"
		r.set('scrapmode', 'OFF')
	else:
		r.set('scrapmode', 'ON')
		livefpl_status.delay()
		getgw.delay()






fplupdating()

