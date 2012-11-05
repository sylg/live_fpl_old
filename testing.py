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
	i = 1
	while i <= 20:
		url = "http://fantasy.premierleague.com/web/api/elements/%s/" %i
		print url
		response = requests.get(url, headers=headers)
		if response.status_code == 200:
			json = response.json
			web_name = json['web_name']
			position = json['type_name']
			teamname = json['team_name']
	 		rdb.hmset(i,{'web_name':web_name, 'position':position,'teamname':teamname})
	 	else:
	 		print "got errore %s"%response.status_code
		i += 1


fill_playerdb()