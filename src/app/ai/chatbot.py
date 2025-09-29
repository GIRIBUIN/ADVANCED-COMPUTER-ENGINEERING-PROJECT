import google.generativeai as genai
import os
from dotenv import load_dotenv

class ChatBot:
    def __init__(self, model, system_message="You are a helpful assistant."):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)

        self.model_name = model
        self.system_message = system_message
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=self.system_message,
        )
        self.chat = self.model.start_chat()

    def get_response(self, user_input, response_format=None):
        response = self.chat.send_message(user_input)
        return response.text

    def reset(self):
        self.chat = self.model.start_chat()
