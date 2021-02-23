import git
from flask import Flask, request
import json
import os
import asyncio
import sys
import subprocess

app = Flask(__name__)
subprocess_handle = None
subprocess_file = ".\TravellerRoller.py"

def git_pull():
	g = git.cmd.Git(".")
	g.pull()

def start_subprocess():
	global subprocess_handle
	subprocess_handle = subprocess.Popen(
		[sys.executable, subprocess_file],
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT)
	print(f"Started: {subprocess_file}")
	#subprocess_handle.start()

def stop_subprocess():
	subprocess_handle.kill()
	print(f"Terminated: {subprocess_file}")

def update():
	print("Pulling and restarting.")
	git_pull()
	stop_subprocess()
	start_subprocess()
	#os.execl(sys.executable, f"{sys.executable}", *sys.args)

@app.route('/webhook',methods=['POST'])
def webhook():
	print("Webhook Triggered.")
	data = json.loads(request.data)
	if data["action"] == "closed" and data["pull_request"]["merged"] == True:
		update()
	return "OK"

if __name__ == '__main__':
	start_subprocess()
	app.run(host="0.0.0.0", port=8087)
