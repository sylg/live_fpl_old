from flask import Flask, request, render_template, jsonify
import os
import json
from collections import OrderedDict
from bs4 import BeautifulSoup
from classictable import *
from tasks import *
from settings import *
from push import *

app = Flask(__name__)


@app.route("/", methods=['GET'])
def index():
	return render_template("index.html")

@app.route("/live", methods=['GET'])
def live():
	league_id = str(request.args.get('league_id'))
	team_id = str(request.args.get('team_id'))
	leagues = []
	for league in r.hgetall('team:%s:leagues'%team_id):
		leagues.append([league,r.hgetall('league:%s:info'%league)])

	league_data = []
	if r.sismember('league:%s'%league_id, "toobig") == 0:
		for team in r.smembers('league:%s'%league_id):
			league_data.append(r.hgetall('team:%s'%str(team)))

		for team in league_data:
			team['totalpts'] = r.hget('team:%s:leagues'%team['id'], league_id)
			team['lineup'] = r.lrange('team:%s:lineup'%team['id'],0,-5)
		league_data = sorted(league_data, key=lambda k: k['totalpts'],reverse=True)
	else:
		league_data.append('None')

	leaguename = r.hget('league:%s:info'%league_id, 'leaguename')
	teamname = r.hget('team:%s'%team_id, 'teamname')
	return render_template("live.html",pushed_data=r.lrange('pushed_data',0,-1), league_data=league_data,currentgw=r.get('currentgw'), team_id=team_id,leagues=leagues, leaguename=leaguename,league_id=league_id, teamname=teamname)

@app.route("/status",methods=['GET'])
def status():
	return r.get('livefpl_status')

@app.route("/getleagues", methods=['GET'])
def add_to_db():
	team_id = str(request.args.get('team_id'))
	if r.exists('team:%s:scraptimer'%team_id) == 1 and r.ttl('team:%s:scraptimer'%team_id) == -1:
		print "refresh scrap"
		add_data_db.delay(team_id)
		r.expire('team:%s:scraptimer'%team_id, 300)
	elif r.exists('team:%s:leagues'%team_id) == 1 and r.exists('team:%s:scraptimer'%team_id) == 0:
		print "data already available"
		r.set('team:%s:scraptimer'%team_id, 'true')
		r.expire('team:%s:scraptimer'%team_id, 300)
		returned_data = {}
		for league in r.hgetall('team:%s:leagues'%team_id):
			returned_data[league] = r.hgetall('league:%s:info'%league)
		return jsonify(returned_data)
	elif r.exists('team:%s:leagues'%team_id) == 1:
		print "data already available"
		returned_data = {}
		for league in r.hgetall('team:%s:leagues'%team_id):
			returned_data[league] = r.hgetall('league:%s:info'%league)
		return jsonify(returned_data)

	elif r.exists('team:%s:scraptimer'%team_id) == 0:
		print "first scrap"
		r.set('team:%s:scraptimer'%team_id, 'true')
		add_data_db.delay(team_id)
		r.expire('team:%s:scraptimer'%team_id, 300)
	
	return "None"
		
@app.route("/updateclassic", methods=['GET'])
def update_classic():
	league_id = str(request.args.get('league_id'))
	league_data = []
	if r.sismember('league:%s'%league_id, "toobig") == 0:
		for team in r.smembers('league:%s'%league_id):
			league_data.append(r.hgetall('team:%s'%team))
		for team in league_data:
			# team['id']
			team['totalpts'] = r.hget('team:%s:leagues'%team['id'], league_id)
			team['lineup'] = r.lrange('team:%s:lineup'%team['id'],0,-5)
	return json.dumps(sorted(league_data, key=lambda k: k['totalpts'],reverse=True))



if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port, debug=True)