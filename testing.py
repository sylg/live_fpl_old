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


fill_playerdb()

# for ids in rdb.lrange('player_ids',0,-1):
# 	if player_update == rdb.hget(ids, 'web_name'):
# 		print "%s is in the db"%player_update
# 	else:
# 		print "%s != %s"%(player_update,rdb.hget(ids, 'web_name') )