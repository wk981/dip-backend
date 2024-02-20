import os
import json
from flask import Flask, request, abort
from werkzeug.exceptions import HTTPException
from firebase_admin import initialize_app
from firebase_functions import https_fn

# Import necessaries libs, taken from Omar repo
from instructor import patch
from openai import OpenAI
from dotenv import load_dotenv

#firebase initialization
initialize_app()
load_dotenv()
# Initialize flask
app = Flask(__name__)

client = patch(OpenAI())

assistant = client.beta.assistants.retrieve(os.getenv('ASSISTANCE'))

thread = client.beta.threads.create()

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
            # Credit to Omar
            message = client.beta.threads.messages.create(
                thread_id = thread.id,
                role="user",
                content=request_data["message"]
            )

            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions="You are a helpful assistant."
            )

            # while true is required for the api to keep runing while the api server is processing the message
            while True:
                run_status = client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                print(run_status.status)
                if run_status.status == 'completed':
                    messages = client.beta.threads.messages.list(
                        thread_id=thread.id
                    )
                    # print(messages)
                    # Response from api server
                    assistant_response = messages.data[0].content[0].text.value
                    if assistant_response == "":
                        response_message = "No message received"
                    else:
                        response_message = assistant_response
                    # return the relevant response code and message
                    return {
                        "message": response_message
                    }, 204 if assistant_response == "" else None
            #Return "No message received, please try again" if there is not completed
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