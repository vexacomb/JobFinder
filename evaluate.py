# evaluate.py
# import env # Removed as API keys are now managed via config.toml

import re
from config import load

import os
import json
from typing import List, Dict, Any, Callable

import openai
import google.generativeai as genai
from google.generativeai import types as gen_types




config = load()
# print(f"DEBUG: Loaded config keys: {config.keys()}")
if 'search_parameters' in config:
    # print(f"DEBUG: search_parameters keys: {config['search_parameters'].keys()}")
    locations = config['search_parameters'].get('locations', [])
else:
    print("DEBUG: search_parameters key NOT FOUND in config")
exclusions = config["search_parameters"]["exclusion_keywords"]
default_resume = config["resume"]["text"]

#_OPENAI_MODEL = "gpt-4.1-mini"  # OpenAI model identifier
_OPENAI_MODEL = "gpt-4o"  # OpenAI model identifier
_GEMINI_MODEL = "models/gemini-2.5-flash-preview-04-17"

_FENCE_RE = re.compile(r"^```(?:json)?\n|\n```$", re.S)



def contains_exclusions(title):
    return any(re.search(rf"(?<!\w){re.escape(word)}(?!\w)", title, re.I)
               for word in exclusions)

def sanitize_text(text: str) -> str:
    """
    Remove or replace non-ASCII characters.
    Replaces common Unicode punctuation with ASCII equivalents.
    """
    # Dictionary of Unicode to ASCII replacements
    replacements = {
        '\u2011': '-',  # Non-breaking hyphen
        '\u2013': '-',  # En dash
        '\u2014': '-',  # Em dash
        '\u2018': "'",  # Left single quote
        '\u2019': "'",  # Right single quote
        '\u201c': '"',  # Left double quote
        '\u201d': '"',  # Right double quote
    }
    
    # Replace known Unicode characters
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    
    # Remove any remaining non-ASCII characters
    return ''.join(char for char in text if ord(char) < 128)
    
def prompt_eligibility(job_description: str, resume: str | None = None) -> str:
    base = (
        "You are an AI recruiter assistant.\n"
        "You are a helpful assistant that evaluates job postings with a realistic understanding of hiring practices. "
        "Remember that many job 'requirements' are actually preferences, and hiring managers often consider candidates who meet 70-80% of listed requirements. "
        "Analyse the following LinkedIn job description and determine whether the "
        "candidate is eligible for the role."
        "Assume the candidate is eligible via US citizenship or residency requirements."
    )
    if resume:
        base += f"\n\nJob Description:\n{sanitize_text(job_description.strip())}\n\nCandidate Resume:\n{sanitize_text(resume.strip())}"
    else:
        base += f"\n\nJob Description:\n{sanitize_text(job_description.strip())}"
    base += (
        "\n\nRespond using ONLY valid JSON with the following schema:\n"
        "{\n"
        "  \"eligible\": bool,\n"
        "  \"reasoning\": str,\n"
        "  \"missing_requirements\": [str]\n"
        "}"
    )
    return base

def call_openai(prompt: str, temperature: float = 0) -> Dict[str, Any]:
    # Ensure the prompt is ASCII-only
    sanitized_prompt = sanitize_text(prompt)
    
    response = openai.chat.completions.create(
        model=_OPENAI_MODEL,
        messages=[{"role": "user", "content": sanitized_prompt}],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

def call_gemini(prompt: str, temperature: float = 0) -> dict:
    current_config = load() # Load config, potentially cached
    google_api_key = current_config.get("api_keys", {}).get("google_api_key")

    if not google_api_key or google_api_key == "YOUR_GOOGLE_API_KEY_HERE":
        raise ValueError("Google API Key not configured in config.toml or is a placeholder.")
    
    # Configure Gemini API key before making a call
    # This configuration is sticky for the genai module until changed again or process ends.
    try:
        genai.configure(api_key=google_api_key)
    except Exception as e:
        # genai.configure can raise if api_key is invalid format, etc.
        raise ValueError(f"Failed to configure Google Gemini API: {e}")

    model = genai.GenerativeModel(_GEMINI_MODEL)
    resp = model.generate_content(
        prompt,
        generation_config={"temperature": temperature},
    )
    txt = _FENCE_RE.sub("", resp.text.strip())
    return json.loads(txt)


def analyze_job(
    job_description: str,
    resume: str | None = default_resume,
    provider: str = "gemini",
    temperature: float = 0,
) -> Dict[str, Any]:

    prompt = prompt_eligibility(job_description, resume)

    # Ensure config is loaded to get API keys if needed by call_openai or call_gemini
    # The functions themselves will handle fetching the keys from the loaded config.
    # config.load.cache_clear() # This should be called elsewhere, e.g., after saving in UI
    # load() # Ensure config is loaded if not already

    call: Callable[[str, float], Dict[str, Any]]
    if provider.lower() == "openai":
        # Configure OpenAI API key before making a call
        current_config = load()
        openai_api_key = current_config.get("api_keys", {}).get("openai_api_key")
        if not openai_api_key or openai_api_key == "YOUR_OPENAI_API_KEY_HERE":
            raise ValueError("OpenAI API Key not configured in config.toml or is a placeholder.")
        openai.api_key = openai_api_key # Set the API key for the openai module
        call = call_openai
    elif provider.lower() == "gemini":
        # Gemini configuration is handled within call_gemini itself to ensure it happens just before model instantiation
        call = call_gemini
    else:
        raise ValueError("provider must be 'openai' or 'gemini'")

    return call(prompt, temperature)


def batch_analyse_jobs(
    job_descriptions: List[str],
    resume: str | None = None,
    provider: str = "openai",
    temperature: float = 0,
) -> List[Dict[str, Any]]:
    return [
        analyse_job(desc, resume=resume, provider=provider, temperature=temperature)
        for desc in job_descriptions
    ]