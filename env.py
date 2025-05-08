# env.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Determine the path to the .env file (assuming it's in the project root)
# This env.py file is in the project root.
env_path = Path(__file__).resolve().parent / '.env'

# Load the .env file. This will load variables into os.environ
load_dotenv(dotenv_path=env_path)

# Now, access the variables from os.environ
# Provide defaults if they might not be set.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Example

# You can add checks here to ensure keys are loaded, or print warnings/errors
if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not found in .env file or environment variables.")

# Other variables you might have previously defined directly in env.py can still exist,
# or you can move them to .env as well if they are environment-specific.