import os
import json
from flask import Flask, request, abort, Response
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
        if('message' not in request_data):
            return {
                    "message": "Bad Request"
            }, 400
        
        else:
            # Ask Greg the message from user
            greg.ask(request_data["message"])

            # Normal answer
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
            

    except Exception as e:
        # If authentication error, return 401
        print(e)
        if(type(e).__name__ is "AuthenticationError"):
            return {
                "error":{
                    "message": "Incorrect API key provided"
                }
            },401
        # Otherwise return 500
        else:
            return {
                "error":{
                    "message": "Internal Server Error"
                }
            }, 500


@app.route('/chatbot/sse', methods=["POST"])
def stream():
    request_data = request.get_json()
    if('message' not in request_data):
        return {
                "message": "Bad Request"
        }, 400
    greg.ask(request_data["message"])
    try:
        def eventStream():
            # while True:
                # wait for source data to be available, then push it
            completion = greg.getCompletion()
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    yield 'data: {}\n\n'.format(chunk.choices[0].delta.content)
        return Response(eventStream(), mimetype="text/event-stream")
    except Exception as e:
        print(e)
        return {
                "error":{
                    "message": "Internal Server Error"
                }
        }, 500


# Expose Flask app as a single Cloud Function:
@https_fn.on_request()
def httpsflaskexample(req: https_fn.Request) -> https_fn.Response:
    with app.request_context(req.environ):
        return app.full_dispatch_request()
