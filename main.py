import os, json, time
import openai

from flask import Flask, request
from werkzeug.exceptions import HTTPException
from firebase_admin import initialize_app
from firebase_functions import https_fn

# Import the chatbot class from "chatbot.py"
from chatbot_handler import chatbot

# Let's call the chatbot greg or smth
greg = chatbot.Chatbot()

# firebase initialization
initialize_app()

# Initialize flask
app = Flask(__name__)
app.debug = True # UNCOMMENT FOR DEVELOPMENT, TODO: MOVE TO ENV VARIABLE

# Error handling, this will be invoked when the user tries to invoke a non existing route
@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

# / Get route that returns hello world
@app.route("/")
def hello_world():
    # Return JSON and status 200
    return {
        "message": "Hello World",
    }, 200

# A POST route to /chatbot. It will take in a json req body and send it to openai api. Take in a json {message:}
@app.route("/chatbot/send", methods=["POST"])
def send_chatbot():
    try:
        # get value from request body. Only accept message
        request_data = request.get_json()
        # return bad request
        if 'message' not in request_data:
            return {
                "message": "Bad Request"
            }, 400
        else:
            # print(request_data['message'])
            
            # Ask Greg the message from user
            greg.ask(request_data["message"])

            answer = greg.answer()
            # No reply from gpt
            if answer == "":
                response_message = "No message received"
            else:
                response_message = answer
            # return the relevant response code and message
            return {
                "message": response_message
            }, 204 if answer == "" else None

    except openai.AuthenticationError:
        return {
            "error": {
                "message": "Incorrect API key provided"
            }
        }, 401
    except Exception as e:
        # Log any other exceptions
        print(e)

# Expose Flask app as a single Cloud Function:

@https_fn.on_request()
def httpsflaskexample(req: https_fn.Request) -> https_fn.Response:
    with app.request_context(req.environ):
        return app.full_dispatch_request()
