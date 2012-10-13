from flask import Flask, request, render_template, jsonify
import redis
import os
from push import *
from collections import OrderedDict
import urllib2
from bs4 import BeautifulSoup
from classictable import *
from tasks import *


app = Flask(__name__)
r.set('livefpl_status','')

@app.route("/", methods=['GET'])
def index():
	return render_template("index.html")

@app.route("/live", methods=['GET'])
def live():
	league_id = str(request.args.get('league_id'))

	league = []
	if r.sismember('league:%s'%league_id, "toobig") == 0:
		for team in r.smembers('league:%s'%league_id):
			league.append(r.hgetall('team:%s'%str(team)))
		league = sorted(league, key=lambda k: k['totalpts'],reverse=True)
	else:
		league.append('None')

	return render_template("live.html",pushed_data=r.lrange('pushed_data',0,-1), league=league,currentgw=r.get('currentgw'))

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
	elif r.exists('team:%s:scraptimer'%team_id) == 0:
		print "first scrap"
		r.set('team:%s:scraptimer'%team_id, 'true')
		add_data_db.delay(team_id)
		r.expire('team:%s:scraptimer'%team_id, 300)
	elif r.exists('team:%s:leagues'%team_id) == 1:
		returned_data = {}
		for league in r.smembers('team:%s:leagues'%team_id):
			returned_data[league] = r.hgetall('league:%s:info'%league)
		return jsonify(returned_data)
	
	return "None"
		


@app.route("/testing", methods=['GET'])
def test():
	scrapper = add_data_db.delay()
	print scrapper.ready()
	return "good"


if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port, debug=True)