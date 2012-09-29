from flask import Flask, request, render_template
import pusher
import redis
from bs4 import BeautifulSoup
import urllib2
import json
from celery import Celery
import os

app = Flask(__name__)


pusher.app_id = "28247"
pusher.key = "b2c9525770d59267a6a2"
pusher.secret = "12d6efe3c861e6ce372a"




@app.route("/", methods=['GET', 'POST'])
def index():
	msg = str(request.args.get('message'))
	print msg
	p['test_channel'].trigger('chatmessage', {'message': msg})

	return render_template("index.html")


@app.route("/live", methods=['GET', 'POST'])
def live():
	return render_template("live.html")


if __name__ == '__main__':
	p = pusher.Pusher()
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)