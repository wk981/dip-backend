from flask import Flask

app = Flask(__name__)

# / Get route that returns hello world
@app.route("/")
def hello_world():
    # Return JSON
    return {
        "message": "Hello World"
    }   