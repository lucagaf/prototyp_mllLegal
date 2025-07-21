import os
import openai
from opik import Opik
from opik.integrations.openai import track_openai

def initialize_openai_client():
    """Initializes the OpenAI client with the provided API key."""
    client = Opik(project_name="BAA Thesis")
    openai.api_key = os.getenv('OPENAI_API_KEY')
    openai_client = openai.OpenAI()
    openai_client = track_openai(openai_client)
    return openai_client