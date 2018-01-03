from flask import Flask
from flask import send_from_directory
from flask_cors import CORS, cross_origin
import pingpong.db_services as db_services
import json

app = Flask(__name__, static_url_path="/frontend/dist")
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/')
def root():
    return send_from_directory("/frontend/dist", "index.html")

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory("/frontend/dist", path)

@app.route('/static/js/<path:path>')
def serve_static_js(path):
    return send_from_directory("frontend/dist/static/js", path)

@app.route('/static/css/<path:path>')
def serve_static_css(path):
    return send_from_directory("frontend/dist/static/css", path)

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