import git
from flask import Flask, request
import json
import os
import sys

app = Flask(__name__)

def git_pull():
	g = git.cmd.Git(".")
	g.pull()

def update():
	git_pull()
	os.execl(sys.executable, f"{sys.executable}", *sys.args)

@app.route('/webhook',methods=['POST'])
def webhook():
	data = json.loads(request.data)
	print(f"New commit by: {data['commits'][0]['author']['name']}")
	if data["action"] == "closed":
		update()
	return "OK"

if __name__ == '__main__':
	app.run(host="0.0.0.0", port=8087)