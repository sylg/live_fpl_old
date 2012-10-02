from flask import Flask, request, render_template
import redis
import os

app = Flask(__name__)



r = redis.StrictRedis(host='localhost', port=6379, db=0)

@app.route("/", methods=['GET', 'POST'])
def index():
	return render_template("index.html")


@app.route("/live", methods=['GET', 'POST'])
def live():
	return render_template("live.html",pushed_data=r.lrange('pushed_data',0,-1))

@app.route("/status",methods=['GET','POST'])
def status():
	return r.get('livefpl_status')



if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)