import pusher
import redis
from bs4 import BeautifulSoup
from push import *
import requests
from tasks import *
from classictable import *
import mechanize
import re
import lxml
from settings import *

rdb = redis.StrictRedis(host='localhost', port=6379, db=2)

def fill_playerdb():
	i = 0
	no_more = 0
	while i <= 622 and no_more <= 5:
		url = "http://fantasy.premierleague.com/web/api/elements/%s/" %i
		response = requests.get(url, headers=headers)
		if response.status_code == 200:
			json = response.json
			web_name = json['web_name']
			position = json['type_name']
			teamname = json['team_name']
	 		rdb.hmset(i,{'web_name':web_name, 'position':position,'teamname':teamname})
	 		rdb.rpush('player_ids', i)
	 	elif response.status_code == 500:
	 		no_more +=1
		i += 1


# for ids in rdb.lrange('player_ids',0,-1):
# 	if player_update == rdb.hget(ids, 'web_name'):
# 		print "%s is in the db"%player_update
# 	else:
# 		print "%s != %s"%(player_update,rdb.hget(ids, 'web_name') )



def scrapteam(teamid,currentgw):
	team = {}
	lineup = {}
	url = "http://fantasy.premierleague.com/entry/%s/event-history/%s/"%(teamid,currentgw)
	html = requests.get(url).text
	soup = BeautifulSoup(html,'lxml')

	#find Team Info
	teamname = str(soup.find(class_='ismSection3').string)
	oldtotal = int(soup.find(class_='ismModBody').find(class_='ismRHSDefList').dd.string)
	oldgwpts = int(soup.find(class_='ismModBody').find(class_='ismRHSDefList').find_all('dd')[3].a.string)
	transfers = int(soup.find(class_='ismSBDefList').find_all('dd')[1].string)

	#find lineup
	for player in soup.find_all(class_="ismPlayerContainer"):
		playername = str(player.find(class_="ismPitchWebName").string.strip())
		points = player.find('a', class_="ismTooltip").string.strip()
		#if player hasn't played yet. Convert his points to 0 and mark him as not played
		if not points.isdigit():
			points = 0
			played = True
		else:
			played = False
		#check if he's the captain
		if player.find(class_='ismCaptainOn'):
			captain = True
		else:
			captain = False
		#check if he's the Vice-captain
		if player.find(class_='ismViceCaptainOn'):
			vc = True
		else:
			vc = False
		#check if he's on the bench
		if player.find_parents(class_='ismBench'):
 			bench = True
		else:
			bench = False
		lineup[playername] = {'pts':points, 'captain':captain,'vc':vc,'bench':bench,'played':played}

	#Calcultating Current GW Points
	currentgwpts = 0
	for player in lineup:
		if lineup[player]['bench'] == False:
			currentgwpts += int(lineup[player]['pts'])

	teamtotal = oldtotal - oldgwpts + currentgwpts
	team['lineup'] = lineup
	team['totalpts'] = teamtotal
	return team





scrapteam(37828,12)


		
