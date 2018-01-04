import json

from flask import Flask
from flask_cors import CORS, cross_origin

import pingpong.services.db_services as db_services

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/hello", methods=['GET'])
@cross_origin()
def hello():
    response = {'message': 'hello'}
    return json.dumps(response)

@app.route("/scoreboard", methods=['GET'])
@cross_origin()
def scorecard():
    total_matches, scoreboard = db_services.get_stats()
    response = {
        'total_matches': total_matches,
        'scoreboard': scoreboard
    }
    return json.dumps(response)

@app.route("/leaderboard", methods=['GET'])
@cross_origin()
def leaderboard():
    leaderboard = db_services.get_leaderboard()
    response = {
        'leaderboard': leaderboard
    }
    return json.dumps(response)

@app.route("/matches", methods=['GET'])
@cross_origin()
def matches():
    matches = db_services.get_matches()
    response = {
        'matches': matches
    }
    return json.dumps(response)

if __name__ == "__main__":
    app.run()