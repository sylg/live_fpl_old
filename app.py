from flask import Flask, request, render_template
import redis
import os

app = Flask(__name__)





@app.route("/", methods=['GET', 'POST'])
def index():
	return render_template("index.html")


@app.route("/live", methods=['GET', 'POST'])
def live():
	return render_template("live.html")


if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)