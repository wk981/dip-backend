import os, json, time
import openai

from flask import Flask, request, Response
from werkzeug.exceptions import HTTPException
import firebase_admin
from firebase_functions import https_fn, options
from dotenv import load_dotenv
from functools import wraps

# Import the chatbot class from "chatbot.py"
from chatbot_handler import chatbot
from flask_cors import CORS

# load env
load_dotenv()
env = os.getenv('PYTHON_ENV')

# firebase initialization
if env != "production":
    credential_path = "./ntu-eee-dip-e028-firebase-adminsdk-vzsra-c405749a40.json" #IMPORTANT
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

default_app = firebase_admin.initialize_app()

# Initialize flask
app = Flask(__name__)

# CORS
CORS(app, cors_origins=["*"])
app.debug = True # UNCOMMENT FOR DEVELOPMENT, TODO: MOVE TO ENV VARIABLE
# logging.getLogger('flask_cors').level = logging.DEBUG


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

# Middleware
def IdToken_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        idToken = None

        # check for authorization in header
        if "Authorization" in request.headers:
            authHeader = request.headers['Authorization']
            idToken = authHeader[len('Bearer '):]
        if not idToken:
            return {
                "message": "Authentication Token is missing"
            }, 401
        try:
            # Decode it
            decoded_token = firebase_admin.auth.verify_id_token(idToken)
            
            # return unauthorized if nth in decoded_token
            if decoded_token is None:
                return {
                    "errors": {
                        "message" : "Invalid token"
                    }
                }, 401
            
        except firebase_admin._token_gen.ExpiredIdTokenError as e:
            #Expired token
            print(e)
            return{
                "errors":{
                    "message": "Token Expired"
                }
            }, 401

        except Exception as e:
            print(e)
            print(type(e))
            return{
                "error":{
                    "message": str(e)
                }
            }, 500
        return f(decoded_token, *args, **kwargs)

    return decorated

# / Get route that returns hello world
@app.route("/")
def hello_world():
    # Return JSON and status 200
    return {
        "message": "Hello World",
    }, 200

# A POST route to /chatbot. It will take in a json req body and send it to openai api. Take in a json {message:}
@app.route("/chatbot/send", methods=["POST"])
@IdToken_required
def send_chatbot(decoded_token):
    try:
        # get value from request body. Only accept message
        request_data = request.get_json()
        # return bad request
        if 'message' not in request_data:
            return {
                "message": "Bad Request"
            }, 400
        else:
            # Log current user
            print("User" + str(decoded_token))
            # Let's call the chatbot greg or smth
            greg = chatbot.Chatbot()
            # Ask Greg the message from user
            greg.setCompletion(request_data["message"],streamChoice=False)

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

    except openai.AuthenticationError:
        return {
            "error": {
                "message": "Incorrect API key provided"
            }
        }, 401
    except Exception as e:
        # Log any other exceptions
        print(e)

# A route to test idtoken
@app.route("/testIdToken")
@IdToken_required
def test_idToken(decoded_token):
    return decoded_token, 200


@app.route('/chatbot/sse', methods=["POST"])
@IdToken_required
def stream(decoded_token):
    request_data = request.get_json()
    if('message' not in request_data):
        return {
                "message": "Bad Request"
        }, 400
    # Log current user
    print("User" + str(decoded_token))
    # Let's call the chatbot greg or smth
    greg = chatbot.Chatbot()
    greg.setCompletion(request_data["message"],streamChoice=True)
    try:
        def eventStream():
            # while True:
                # wait for source data to be available, then push it
            completion = greg.getCompletion()
            prevChunk = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        return Response(eventStream(), mimetype="text/event-stream")
    except Exception as e:
        print(e)
        return {
                "error":{
                    "message": "Internal Server Error"
                }
        }, 500


# Expose Flask app as a single Cloud Function:
# CORS configured to firebase.com and localhost
@https_fn.on_request()
def httpsflaskexample(req: https_fn.Request) -> https_fn.Response:
    with app.request_context(req.environ):
        return app.full_dispatch_request()
