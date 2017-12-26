from flask import Flask
from flask import jsonify
import pingpong.db_services as db_services

app = Flask(__name__)

@app.route("/scorecard", methods=['GET'])
def scorecard():
    total_matches, scorecard = db_services.get_stats()
    response = {
        'total_matches': total_matches,
        'scorecard': scorecard
    }
    return jsonify(response)

if __name__ == "__main__":
    app.run()