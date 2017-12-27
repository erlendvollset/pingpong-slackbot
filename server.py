from flask import Flask
import pingpong.db_services as db_services
import json

app = Flask(__name__)

@app.route("/scoreboard", methods=['GET'])
def scorecard():
    total_matches, scoreboard = db_services.get_stats()
    response = {
        'total_matches': total_matches,
        'scoreboard': scoreboard
    }
    return json.dumps(response)

@app.route("/leaderboard", methods=['GET'])
def leaderboard():
    leaderboard = db_services.get_leaderboard()
    response = {
        'leaderboard': leaderboard
    }
    return json.dumps(response)

@app.route("/matches", methods=['GET'])
def matches():
    matches = db_services.get_matches()
    response = {
        'matches': matches
    }
    return json.dumps(response)

if __name__ == "__main__":
    app.run()