from flask import Flask, request, render_template
import redis
import os
from push import *

app = Flask(__name__)
r.set('livefpl_status','')
league = [[307, {'id': 37828, 'rank': 12, 'teamname':'PEDD United','gw_score':42 }],
[356, {'id': 205633, 'rank': 6, 'teamname':'Fc Mbonabushia','gw_score':42 }],
[312, {'id': 933573, 'rank': 11, 'teamname':'FC Slurp','gw_score':42 }],
[362, {'id': 38861, 'rank': 5, 'teamname':'KFC_Overijse','gw_score':42 }],
[396, {'id': 1538051, 'rank': 2, 'teamname':'Fc Paris','gw_score':42 }]]
#league = {'PEDD United': {'id': 37828, 'rank': 12, 'totalpts': 307}, 'Fc Mbonabushia': {'id': 205633, 'rank': 6, 'totalpts': 356}, 'FC Slurp': {'id': 933573, 'rank': 11, 'totalpts': 312}, 'KFC_Overijse': {'id': 38861, 'rank': 5, 'totalpts': 362}, 'Fc Paris': {'id': 1538051, 'rank': 2, 'totalpts': 396}, 'CP Rangers': {'id': 194801, 'rank': 9, 'totalpts': 334}, 'FC Van Nico': {'id': 321564, 'rank': 7, 'totalpts': 342}, 'FC Lasne': {'id': 688922, 'rank': 1, 'totalpts': 407}, 'RSC Swarlz': {'id': 694831, 'rank': 4, 'totalpts': 383}, 'MonacoDiBaviera': {'id': 378429, 'rank': 3, 'totalpts': 388}, 'FC Jaboulani': {'id': 303108, 'rank': 8, 'totalpts': 337}, 'FC Gamos': {'id': 175286, 'rank': 10, 'totalpts': 317}}
league = sorted(league, reverse=True)

@app.route("/", methods=['GET', 'POST'])
def index():
	return render_template("index.html")


@app.route("/live", methods=['GET', 'POST'])
def live():
	return render_template("live.html",pushed_data=r.lrange('pushed_data',0,-1), league=league)

@app.route("/status",methods=['GET','POST'])
def status():
	return r.get('livefpl_status')




if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port, debug=True)