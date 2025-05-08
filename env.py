# env.py
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(usecwd=True), override=True)

import os, sys
k = os.getenv("OPENAI_API_KEY")
if not k:
    sys.exit("OPENAI_API_KEY missing")

import openai, google.generativeai as genai
openai.api_key = k
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))