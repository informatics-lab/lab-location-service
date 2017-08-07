from datetime import datetime
import os
import sys
import time

from flask import Flask, request
from flask import jsonify
from flask_cors import CORS, cross_origin
import pymongo
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)
db_connected = False

print("Connecting to database.")

while db_connected is not True:
    try:
        client = MongoClient(os.environ.get('MONGO_HOST', 'localhost'),
                             os.environ.get('MONGO_PORT', 27017))
        client.server_info()
    except pymongo.errors.ServerSelectionTimeoutError:
        print("Unable to connect to mongo, trying again in 5 seconds")
        time.sleep(5)
        continue
    db_connected = True

db = client[os.environ.get('MONGO_DB', 'lab-locations')]
locations = db['locations']

user_locations = {}

try:
    AUTH_TOKEN = os.environ['AUTH_TOKEN']
except KeyError:
    print("Need to set env var AUTH_TOKEN")
    sys.exit(1)

def check_connection():
    return db_connected

def get_location(username):
    location = locations.find_one({"username": username})
    if location is None:
        raise KeyError("Cannot find user %s", username)
    if location['update_time'].date() != datetime.today().date():
        location["location"] = "unknown"
        location["update_time"] = datetime.now()
    return location

def set_location(username, location):
    try:
        document = get_location(username)
    except KeyError:
        document = {}
    document['username'] = username
    document['location'] = location
    document['update_time'] = datetime.now()
    locations.update_one({"username": username}, {"$set": document}, upsert=True)

@app.route('/')
def hello_world():
    if check_connection() is False:
        return jsonify(message='Database is not connected'), 500
    return jsonify(message='Welcome to the Lab location service.')

@app.route('/user/<username>', methods=['GET'])
def show_user_location(username):
    if check_connection() is False:
        return jsonify(message='Database is not connected'), 500
    try:
        location = get_location(username)['location']
        update_time = get_location(username)['update_time'].isoformat()
    except (KeyError, ValueError):
        location = "unknown"
    return jsonify(username=username, location=location, update_time=update_time)

@app.route('/user/<username>', methods=['POST'])
def set_user_location(username):
    if check_connection() is False:
        return jsonify(message='Database is not connected'), 500
    if request.headers.get('Authorization') == "Bearer {}".format(AUTH_TOKEN):
        info = request.get_json()
        set_location(username, info["location"])
        print(info["location"])
        return "ok"
    else:
        return jsonify(message='You are not authorized to do this.'), 403
