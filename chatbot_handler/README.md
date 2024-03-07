## Chatbot Handler

`chatbot.py` contains a Class object of Chatbot(). Basically what it does is it takes the input from the user, sends that input to the GPT model via Chat Completions API, then returns the response from the GPT model.

### How to use in your Python code

```
from chatbot import Chatbot

example_variable = Chatbot()

# Let's say you have a user input as an example.
user_input = input("Enter input here: ")

# Now you wanna send that input to the GPT model via the Chatbot() class object, which we have previously initialised as "example_variable".
chatbot_output = example_variable.ask(user_input)
```

The folder `fine-tune` contains a jsonl file used for fine-tuning the AI model.
