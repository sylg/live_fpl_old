from flask import Flask, request, render_template
from datetime import datetime
import os
app = Flask(__name__)


@app.route('/fixture/<int:fixtureid>/')
def fixture(fixtureid):

	return open(os.getcwd()+'/static/%s/update0.html'%int(fixtureid)).read()


if __name__ == '__main__':
	port = 5001
	app.run(host='0.0.0.0', port=port, debug=True)