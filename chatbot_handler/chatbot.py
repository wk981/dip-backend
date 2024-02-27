import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class Chatbot:
    """
    This class handles the chatbot. It sends a prompt to the chat completions API and returns the response from the GPT.
    """
    def __init__(self) -> None:
        # INSERT PROMPT ENG / FINE TUNE HERE?
        self.client = OpenAI()
        self.COMMAND_PROMPT = """
        You are a helpful assistant. You are tasked with answering questions 
        provided by the user. The user is a Singaporean teenager keen on 
        learning more about the dangers of drugs and vaping. Your objective 
        is to be informative about these topics and discourage the user from 
        ever pursuing abuse of drugs or vaping. Please be polite and friendly.
        """
        # completion attribute, default is none
        self.completion = None

    def ask(self, text: str) -> str:
        # Set class's completion 
        self.completion = self.client.chat.completions.create(
            model = "gpt-3.5-turbo",
            messages = [
                {
                    "role": "system",
                    "content": self.COMMAND_PROMPT
                },
                {
                    "role": "user",
                    "content": text
                }           
            ],
            stream=True # Remove this if you do not want to stream the output
        )
        
    def answer(self) -> str:
        # check whether it's completion or completion.choices[0].message.content
        return self.completion.choices[0].message.content

    # def streaming(self):
    #     for chunk in self.completion:
    #         if chunk.choices[0].delta.content is not None:
    #             print(chunk.choices[0].delta.content, end="")
    #             yield chunk.choices[0].delta.content + ""
    def getCompletion(self):
        return self.completion
                