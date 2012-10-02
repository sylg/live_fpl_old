import pusher
import redis
from bs4 import BeautifulSoup
import urllib2
from push import *



old_data_test = [['Mannone', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '2', 'OG': '0', 'YC': '0', 'TP': '1', 'S': '1', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Koscielny', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '7', 'OG': '0', 'YC': '0', 'TP': '1', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Vermaelen', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '-2', 'OG': '0', 'YC': '1', 'TP': '0', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Gibbs', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '4', 'OG': '0', 'YC': '0', 'TP': '1', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Jenkinson', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '2', 'OG': '0', 'YC': '0', 'TP': '1', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Walcott', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '1', 'OG': '0', 'YC': '0', 'TP': '1', 'S': '0', 'GC': '0', 'MP': '25', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Diaby', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '6', 'OG': '0', 'YC': '0', 'TP': '1', 'S': '0', 'GC': '0', 'MP': '16', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Ramsey', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '-1', 'OG': '0', 'YC': '1', 'TP': '1', 'S': '0', 'GC': '1', 'MP': '65', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Arteta', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '6', 'OG': '0', 'YC': '0', 'TP': '2', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Chamberlain', {'A': '1', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '8', 'OG': '0', 'YC': '0', 'TP': '5', 'S': '0', 'GC': '1', 'MP': '74', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Gervinho', {'A': '0', 'PS': '0', 'B': '1', 'GS': '1', 'ESP': '20', 'OG': '0', 'YC': '0', 'TP': '8', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Santi Cazorla', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '-9', 'OG': '0', 'YC': '0', 'TP': '2', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Podolski', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '7', 'OG': '0', 'YC': '0', 'TP': '2', 'S': '0', 'GC': '1', 'MP': '66', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Giroud', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '0', 'OG': '0', 'YC': '0', 'TP': '1', 'S': '0', 'GC': '0', 'MP': '24', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Cech', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '14', 'OG': '0', 'YC': '0', 'TP': '3', 'S': '3', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Cahill', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '1', 'OG': '0', 'YC': '0', 'TP': '1', 'S': '0', 'GC': '0', 'MP': '10', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Luiz', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '15', 'OG': '0', 'YC': '1', 'TP': '1', 'S': '0', 'GC': '1', 'MP': '80', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Bertrand', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '1', 'OG': '0', 'YC': '0', 'TP': '1', 'S': '0', 'GC': '0', 'MP': '7', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Terry', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '13', 'OG': '0', 'YC': '0', 'TP': '2', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Ivanovic', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '14', 'OG': '0', 'YC': '0', 'TP': '2', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Cole A', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '14', 'OG': '0', 'YC': '0', 'TP': '2', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Ramires', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '18', 'OG': '0', 'YC': '1', 'TP': '1', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Mikel', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '10', 'OG': '0', 'YC': '0', 'TP': '2', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Mata', {'A': '1', 'PS': '0', 'B': '3', 'GS': '0', 'ESP': '39', 'OG': '0', 'YC': '0', 'TP': '13', 'S': '0', 'GC': '1', 'MP': '83', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Hazard', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '16', 'OG': '0', 'YC': '0', 'TP': '2', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Moses', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '-5', 'OG': '0', 'YC': '0', 'TP': '1', 'S': '0', 'GC': '0', 'MP': '18', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Oscar', {'A': '0', 'PS': '0', 'B': '0', 'GS': '0', 'ESP': '3', 'OG': '0', 'YC': '1', 'TP': '1', 'S': '0', 'GC': '1', 'MP': '72', 'RC': '0', 'CS': '0', 'PM': '0'}], ['Torres', {'A': '0', 'PS': '0', 'B': '2', 'GS': '1', 'ESP': '33', 'OG': '0', 'YC': '0', 'TP': '11', 'S': '0', 'GC': '1', 'MP': '90', 'RC': '0', 'CS': '0', 'PM': '0'}]]

def get_fixture_ids():
	url = 'http://fantasy.premierleague.com/fixtures/5/'
	response = urllib2.urlopen(url)
	html = response.read()
	tablestart = html.find('<div id="ism" class="ism">')
	tableend = html.find('<aside class="ismAside">')
	html = html[tablestart:tableend]
	soup = BeautifulSoup(html)
	for row in soup.find_all('tr', 'ismFixtureSummary'):
		fixture_id = str(row.find('a', text="Detailed stats")['data-id'])
		if r.lrem('fixture_ids', 0, fixture_id) == 0:
			r.lpush('fixture_ids', fixture_id)
			r.expire('fixture_ids', 39600)
		else:
			r.lpush('fixture_ids', fixture_id)


def create_scrapper():
	for ids in r.lrange('fixture_ids',0, -1):
		scrapper.delay(ids)


def dict_diff(dict_a, dict_b):
    return dict([
        (key, dict_b.get(key, dict_a.get(key)))
        for key in set(dict_a.keys()+dict_b.keys())
        if (
            (key in dict_a and (not key in dict_b or dict_a[key] != dict_b[key])) or
            (key in dict_b and (not key in dict_a or dict_a[key] != dict_b[key]))
        )
    ])


def scrapper(fixture_id):
	url = 'http://fantasy.premierleague.com/fixture/%s/' %fixture_id
	response = urllib2.urlopen(url)
	html = response.read()
	soup = BeautifulSoup(html)
	for teams in soup.find_all('table'):
		teamname = str(teams.find('caption').string)

		for players in teams.find('tbody').find_all('tr'):
			playername = str(players.td.string.strip())
			if r.lrem('lineups:%s' %fixture_id, 0, playername) == 0:
				r.rpush('lineups:%s' %fixture_id, playername)
			else:
				r.rpush('lineups:%s' %fixture_id, playername)

			
			r.hset(playername+':fresh:'+str(fixture_id),'TEAMNAME',str(teamname))
			keys = ['MP', 'GS', 'A', 'CS', 'GC', 'OG', 'PS', 'PM', 'YC', 'RC','S', 'B', 'ESP', 'TP']
			i = 1
			for key in keys:
				r.hset(playername+':fresh:'+str(fixture_id), key, int(players.find_all('td')[i].string.strip()))
				i += 1

	#Begin Differential between Scrap & push
	for players in r.lrange('lineups:%s' %fixture_id, 0, -1):
		old = r.hgetall(players+':old:%s' %fixture_id)
		fresh = r.hgetall(players+':fresh:%s' %fixture_id)
		if dict_diff(old,fresh):
			push_data(players,dict_diff(old,fresh))

	#Rename fresh data as old for next scrap
		# r.rename(players+':fresh:%s' %fixture_id, players+':fresh:%s' %fixture_id)




scrapper(51)
