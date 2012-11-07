from flask import Flask, request, render_template
from datetime import datetime
import os
import redis

app = Flask(__name__)

r = redis.StrictRedis(host='localhost', port=6379, db=0)


@app.route('/fixture/<int:fixtureid>/')
def fixture(fixtureid):
	if r.exists('hit_counter:%s'%fixtureid):
		i = r.get('hit_counter:%s'%fixtureid)
	else:
		i = 0
		r.set('hit_counter:%s'%fixtureid, 0)
	
	if os.path.exists(os.getcwd()+'/static/%s/update%s.html'%(int(fixtureid), i)):
		print "scrap #%s"%i
		r.incr('hit_counter:%s'%fixtureid)
		return open(os.getcwd()+'/static/%s/update%s.html'%(int(fixtureid), i)).read()
	else:
		print "not good ( %s )"%i
		return "None"

if __name__ == '__main__':
	port = 5001
	app.run(host='0.0.0.0', port=port, debug=True)