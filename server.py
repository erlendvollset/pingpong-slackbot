from flask import Flask
import pingpong.db_services as db_services

app = Flask(__name__)

@app.route("/scorecard", methods=['GET'])
def scorecard():
    total_matches, scorecard = db_services.get_stats()
    return {
        'total_matches': total_matches,
        'scorecard': scorecard
    }

if __name__ == "__main__":
    app.run()