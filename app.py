from flask import Flask, request, render_template
import redis
import os
from push import *
from collections import OrderedDict
import urllib2
from bs4 import BeautifulSoup


app = Flask(__name__)
r.set('livefpl_status','')


def getteams(leagueid):
	url = 'http://fantasy.premierleague.com/my-leagues/%s/standings/' % leagueid
	response = urllib2.urlopen(url)
	html = response.read()
	tablestart = html.find('<!-- League tables -->')
	tableend = html.find('</section>')
	html = html[tablestart:tableend]
	soup = BeautifulSoup(html)
	if len(soup.find_all('tr')) <= 25:
		for team in soup.find_all('tr'):

			if team.find('a') == None:
				continue
			teamname = str(team.find('a').string)
			team_id = int(team.a['href'].strip('/').split('/')[1])
			total_pts = int(team.td.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.string)
			gw_pts = int(team.td.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.string)
			r.sadd('league:%s'%leagueid, team_id)
			for team in r.smembers('league:%s'%leagueid):
				r.hmset('team:%s' %team_id,{'id':team_id, 'totalpts':total_pts, 'gwpts':gw_pts, 'teamname':teamname})
	else:
		r.sadd('league:%s'%leagueid,"toobig")


@app.route("/", methods=['GET', 'POST'])
def index():
	return render_template("index.html")

@app.route("/live", methods=['GET', 'POST'])
def live():
	lid = str(request.args.get('league_id'))
	getteams(lid)
	league = []
	if r.sismember('league:%s'%lid, "toobig") == 0:
		for team in r.smembers('league:%s' % lid):
			league.append(r.hgetall('team:%s'%str(team)))
		league = sorted(league, key=lambda k: k['totalpts'],reverse=True)
	else:
		league.append('None')
	return render_template("live.html",pushed_data=r.lrange('pushed_data',0,-1), league=league)

@app.route("/status",methods=['GET','POST'])
def status():
	return r.get('livefpl_status')





if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port, debug=True)