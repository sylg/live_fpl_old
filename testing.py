from flask import Flask, request, render_template
import pusher
import redis
from bs4 import BeautifulSoup
import urllib2
import pickle
from tasks import scrapper

r = redis.StrictRedis(host='localhost', port=6379, db=0)

pusher.app_id = "28247"
pusher.key = "b2c9525770d59267a6a2"
pusher.secret = "12d6efe3c861e6ce372a"
p = pusher.Pusher()

class DictDiffer(object):
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        return self.set_current - self.intersect 
    def removed(self):
        return self.set_past - self.intersect 
    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])

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


def scrapper(fixture_id):
	url = 'http://fantasy.premierleague.com/fixture/%s/' %fixture_id
	response = urllib2.urlopen(url)
	html = response.read()
	soup = BeautifulSoup(html)
	datas = []
	datas_push = []
	for teams in soup.find_all('table'):
		teamname = teams.find('caption').string
		for players in teams.find('tbody').find_all('tr'):
			playername = str(players.td.string.strip())
			data = {}
			data['TEAMNAME'] = str(teamname)
			keys = ['MP', 'GS', 'A', 'CS', 'GC', 'OG', 'PS', 'PM', 'YC', 'RC','S', 'B', 'ESP', 'TP']
			i = 1
			for key in keys:
				data[key] = str(players.find_all('td')[i].string.strip())
				if data[key] == '0':
					del data[key]
				i += 1
			datas.append([playername, data])

	#check if 1st scrap do nothing, else do a diff.
	if r.exists('data_old:%s' %fixture_id):
		datas_old = pickle.loads(r.get('data_old:%s' % fixture_id))
		i = 0
		#start Differential
		for players in datas:
			#new stats
			new_stats = DictDiffer(players[1], datas_old[i][1])
			added = {}
			updated = {}
			for keys in new_stats.added():
				added[str(keys)] = players[1][keys]
				added['TEAMNAME'] = players[1]['TEAMNAME'] 
			#updated stats
			for keys in new_stats.changed():
				added[str(keys)] = players[1][keys]
			if added:
				datas_push.append([players[0],added])
			i += 1

	#save fresh data as old for next scrapping diff
	r.set('data_old:%s' % fixture_id,pickle.dumps(datas))

	msg_test = 'I just scrapped this url:%s' %url
	p['test_channel'].trigger('chatmessage', {'message': msg_test})


# 	# nlist = [['Szczesny', {'TEAMNAME': 'Arsenal', 'ESP': '13', 'TP': '2', 'S': '2', 'GC': '1', 'MP': '90'}], ['Vermaelen', {'MP': '90', 'GC': '1','TP': '2', 'TEAMNAME': 'Arsenal', 'ESP': '23'}], ['Gibbs', {'B': '1', 'ESP': '33', 'TP': '3', 'GC': '1', 'TEAMNAME': 'Arsenal', 'MP': '90'}], ['Jenkinson', {'MP': '90', 'GC': '1', 'TP': '2', 'TEAMNAME': 'Arsenal', 'ESP': '17'}], ['Mertesacker', {'MP': '90', 'GC': '1', 'TP': '2', 'TEAMNAME': 'Arsenal', 'ESP': '14'}], ['Walcott', {'MP': '17', 'GS': '1', 'TP': '6', 'TEAMNAME': 'Arsenal', 'ESP': '20'}], ['Ramsey', {'A': '1', 'MP': '24', 'TP': '4', 'TEAMNAME': 'Arsenal', 'ESP': '3'}], ['Arteta', {'A': '1', 'TEAMNAME': 'Arsenal', 'ESP': '21', 'TP': '5', 'GC': '1', 'MP': '90'}], ['Chamberlain', {'MP': '90', 'GC': '1', 'TP': '2', 'TEAMNAME': 'Arsenal', 'ESP': '9'}], ['Coquelin', {'A': '1', 'TEAMNAME': 'Arsenal', 'ESP': '14', 'TP': '5', 'GC': '1', 'MP': '66'}], ['Gervinho', {'B': '3', 'GS': '2', 'ESP': '40', 'TP': '15', 'GC': '1', 'TEAMNAME': 'Arsenal', 'MP': '73'}], ['Santi Cazorla', {'A': '1', 'TEAMNAME': 'Arsenal', 'ESP': '23', 'TP': '5', 'GC': '1', 'MP': '90'}], ['Podolski', {'B': '2', 'GS': '1', 'ESP': '37', 'TP': '8', 'GC': '1', 'TEAMNAME': 'Arsenal', 'MP': '73'}], ['Giroud', {'TEAMNAME': 'Arsenal', 'MP': '17', 'TP': '1', 'ESP': '2'}], ['Davis', {'S': '5', 'GC': '6', 'MP': '90', 'TEAMNAME': 'Southampton', 'ESP': '5'}], ['Fox', {'TEAMNAME': 'Southampton', 'GS': '1', 'ESP': '22', 'TP': '5', 'GC': '6', 'MP': '90'}], ['Hooiveld', {'TEAMNAME': 'Southampton', 'ESP': '1', 'TP': '2', 'GC': '1', 'MP': '27'}], ['Fonte', {'MP': '90', 'GC': '6', 'TP': '-1', 'TEAMNAME': 'Southampton', 'ESP': '10'}], ['Clyne', {'TEAMNAME': 'Southampton', 'ESP': '10', 'GC': '6', 'MP': '90'}], ['Yoshida', {'GC': '5', 'MP': '63', 'TEAMNAME': 'Southampton', 'ESP': '2'}], ['Lallana', {'MP': '90', 'GC': '6', 'TP': '2', 'TEAMNAME': 'Southampton', 'ESP': '4'}], ['Schneiderlin', {'GC': '6', 'TEAMNAME': 'Southampton', 'TP': '2', 'MP': '90'}], ['Puncheon', {'A': '1', 'TEAMNAME': 'Southampton', 'ESP': '8', 'TP': '5', 'GC': '6', 'MP': '90'}], ['Davis', {'MP': '45', 'GC': '4', 'TP': '1', 'TEAMNAME': 'Southampton', 'ESP': '7'}], ['Ward-Prowse', {'MP': '90', 'GC': '6', 'TP': '2', 'TEAMNAME': 'Southampton', 'ESP': '3'}], ['Ramirez', {'MP': '45', 'GC': '2', 'TP': '1', 'TEAMNAME': 'Southampton', 'ESP': '3'}], ['Lambert', {'MP': '75', 'GC': '5', 'TP': '2', 'TEAMNAME': 'Southampton', 'ESP': '-1'}], ['Rodriguez', {'MP': '15', 'GC': '1', 'TP': '1', 'TEAMNAME': 'Southampton', 'ESP': '1'}]]
# 	# r.set('data_old', pickle.dumps(nlist))


get_fixture_ids()
#create_scrapper()
