import os
import sys

from flask import Flask, request
from flask import jsonify
app = Flask(__name__)

user_locations = {}

try:
    AUTH_TOKEN = os.environ['AUTH_TOKEN']
except KeyError:
    print("Need to set env var AUTH_TOKEN")
    sys.exit(1)

@app.route('/')
def hello_world():
    return jsonify(message='Welcome to the Lab location service.')

@app.route('/user/<username>', methods=['GET'])
def show_user_location(username):
    try:
        location = user_locations[username]
    except KeyError:
        location = "Unknown"
    return jsonify(username=username, location=location)

@app.route('/user/<username>', methods=['POST'])
def set_user_location(username):
    info = request.get_json()
    user_locations[username] = info["location"]
    if request.headers.get('Authorization') == "Bearer {}".format(AUTH_TOKEN):
        print(info["location"])
        return "ok"
    else:
        return "not ok"
