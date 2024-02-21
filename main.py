import os
import json
from flask import Flask, request, abort
from werkzeug.exceptions import HTTPException
from firebase_admin import initialize_app
from firebase_functions import https_fn

"""
Removed: importing of certain libraries. Not needed as they are in "chatbot.py".
Added: importing Chatbot() class from "chatbot.py" file.
"""

# Import the chatbot class from "chatbot.py"
from chatbot import Chatbot

# Let's call the chatbot greg or smth
greg = Chatbot()


"""
Removed: load_dotenv(). Not needed as it is in "chatbot.py".
"""

# firebase initialization
initialize_app()

# Initialize flask
app = Flask(__name__)

"""
Removed: client = patch(OpenAI()), assistant, and thread. Not needed as everything is in Chatbot() in "chatbot.py".
"""

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
            # print(request_data['message'])
            
            """
            Removed: message and run. No need anymore since we are not using Assistants API, we are using Chat Completions API.
            Added: greg.ask() , this will send the Chatbot() the message input from user.
            """
            
            # Ask Greg the message from user
            greg.ask(request_data["message"])

            # while true is required for the api to keep runing while the api server is processing the message
            while True:
                
                """
                Removed: run_status, and getting messages (aka response).
                Added: answer = greg.answer()
                Edited backend code also, if it's wrong then feel free to edit.
                """
                
                    answer = greg.answer()
                    if answer == "":
                        response_message = "No message received"
                    else:
                        response_message = answer
                    # return the relevant response code and message
                    return {
                        "message": response_message
                    }, 204 if answer == "" else None
            #Return "No message received, please try again" if there is not completed
                
                """
                Over here, need to remove "if run_status.status == 'failed' ".
                But I don't know how to edit the code here.
                But basically it's just supposed to give error if the bot didn't execute.
                """

                if run_status.status == 'failed':
                    print(run_status)
                    return {
                        "message": "Something went wrong, please try again"
                    }, 503
            

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

# Expose Flask app as a single Cloud Function:

@https_fn.on_request()
def httpsflaskexample(req: https_fn.Request) -> https_fn.Response:
    with app.request_context(req.environ):
        return app.full_dispatch_request()
