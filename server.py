from flask import Flask
from flask import send_from_directory
app = Flask(__name__, static_url_path="/fe/")

@app.route("/")
def hello():
    return send_from_directory("fe", "index.html")

if __name__ == "__main__":
    app.run()