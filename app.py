from flask import Flask, request, render_template, jsonify
import redis
import os
from push import *
from collections import OrderedDict
import urllib2
from bs4 import BeautifulSoup
from classictable import *
import json


app = Flask(__name__)
r.set('livefpl_status','')

@app.route("/", methods=['GET', 'POST'])
def index():
	return render_template("index.html")

@app.route("/live", methods=['GET', 'POST'])
def live():
	team_id = str(request.args.get('team_id'))
	if r.exists('team:%s:scraptimer'%team_id) == 1 and r.ttl('team:%s:scraptimer'%team_id) == -1:
		print "refresh scrap LIVE"
		add_data(team_id,r.get('currentgw'))
		r.expire('team:%s:scraptimer'%team_id, 300)
	elif r.exists('team:%s:scraptimer'%team_id) == 0:
		print "first scrap LIVE"
		r.set('team:%s:scraptimer'%team_id, 'true')
		add_data(team_id,r.get('currentgw'))
		r.expire('team:%s:scraptimer'%team_id, 300)
	else:
		print " i dont need scrapping LIVE"

	league = []
	if r.sismember('league:48483', "toobig") == 0:
		for team in r.smembers('league:48483'):
			league.append(r.hgetall('team:%s'%str(team)))
		league = sorted(league, key=lambda k: k['totalpts'],reverse=True)
	else:
		league.append('None')

	return render_template("live.html",pushed_data=r.lrange('pushed_data',0,-1), league=league,currentgw=r.get('currentgw'), teamid=team_id)

@app.route("/status",methods=['GET','POST'])
def status():
	return r.get('livefpl_status')

@app.route("/getleagues", methods=['GET','POST'])
def add_to_db():
	team_id = str(request.args.get('team_id'))
	if r.exists('team:%s:scraptimer'%team_id) == 1 and r.ttl('team:%s:scraptimer'%team_id) == -1:
		print "refresh scrap"
		add_data(team_id,r.get('currentgw'))
		r.expire('team:%s:scraptimer'%team_id, 300)
	elif r.exists('team:%s:scraptimer'%team_id) == 0:
		print "first scrap"
		r.set('team:%s:scraptimer'%team_id, 'true')
		add_data(team_id,r.get('currentgw'))
		r.expire('team:%s:scraptimer'%team_id, 300)
	else:
		print " i dont need scrapping"
	
	returned_data = {}
	for league in r.smembers('team:%s:leagues'%team_id):
		returned_data[league] = r.hgetall('league:%s:info'%league)
		
	return jsonify(returned_data)


if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port, debug=True)