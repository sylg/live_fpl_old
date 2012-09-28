from flask import Flask, request, render_template
import pusher
import redis
from bs4 import BeautifulSoup
import urllib2
import json
from celery import Celery

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

def get_fixture():
	url = 'http://fantasy.premierleague.com/fixture/49/'
	response = urllib2.urlopen(url)
	html = response.read()
	soup = BeautifulSoup(html)
	print soup.prettify()






@app.route("/live", methods=['GET', 'POST'])
def live():
	return render_template("live.html")








if __name__ == '__main__':
  p = pusher.Pusher()
  app.run(debug=True)