import os
import openai
from opik import Opik
from opik.integrations.openai import track_openai
import streamlit as st

def initialize_openai_client():
    """Initializes the OpenAI client with the provided API key."""
    #client = Opik(project_name="BAA Thesis")
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY not found in environment variables.")
    #openai.api_key = api_key
    #openai_client = openai.OpenAI()
    client = openai.OpenAI(api_key=api_key)
    openai_client = track_openai(client)
    return openai_client

def initialize_opik_client():
    api_key = st.secrets["OPIK"]
    return Opik(api_key=api_key)