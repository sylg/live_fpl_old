from flask import Flask, request, render_template
from datetime import datetime
import os
app = Flask(__name__)


@app.route('/')
def fixture():
	i = 3
	return render_template('updating.html') 


if __name__ == '__main__':
	port = 5001
	app.run(host='0.0.0.0', port=port, debug=True)