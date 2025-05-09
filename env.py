# env.py
import os
from dotenv import load_dotenv
from utils import ENV_FILE_PATH # MODIFIED: Import from utils.py

# Load the .env file. This will load variables into os.environ
# load_dotenv will also try to find .env on its own, but providing a direct path is more explicit.
if ENV_FILE_PATH.exists():
    load_dotenv(dotenv_path=ENV_FILE_PATH)
else:
    # This case should ideally be handled by utils.py creating it,
    # or by setup.py ensuring it's there.
    print(f"Warning: .env file not found at {ENV_FILE_PATH}. API keys may be missing.")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not GOOGLE_API_KEY:
    # This print might be noisy if it's expected that setup.py or the Inputs page handles it.
    # Consider making it a log or a more subtle warning.
    # print("Warning: GOOGLE_API_KEY not found in .env file or environment variables.")
    pass