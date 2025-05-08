# JobFinder

JobFinder is a Python application designed to automate the process of finding relevant job postings from LinkedIn. It scrapes job listings, uses AI (Google Gemini) to evaluate them against your defined criteria and resume, and then presents approved jobs in an interactive web dashboard where you can manage them.

## Features

*   Automated job scraping from LinkedIn based on configurable keywords and locations.
*   AI-powered evaluation of job descriptions for eligibility.
*   Web-based dashboard (built with Streamlit) to:
    *   View and manage approved job postings.
    *   Mark jobs as "applied."
    *   View a separate list of applied-to jobs.
    *   Edit search parameters, AI prompts, and your default resume via a configuration page.
    *   Initiate new job scans.
    *   Clear outdated job data.
*   Local SQLite database for persisting job information.
*   Automated setup process for virtual environment and dependencies.

## Prerequisites

*   Python 3.8 or newer.
*   Git (for cloning the repository).
*   Access to Google AI Gemini API and a `GOOGLE_API_KEY`.

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/vexacomb/JobFinder.git
    cd JobFinder
    ```

2.  **Set up API Key:**
    *   The application requires a Google API Key for the Gemini AI model to evaluate job descriptions.
    *   You need to make this key available to the application. The `env.py` file is intended for this.
    *   Create or ensure `env.py` exists in the project root and set your `GOOGLE_API_KEY` within it:
        ```python
        # env.py
        GOOGLE_API_KEY = "YOUR_ACTUAL_GOOGLE_API_KEY_HERE"
        # You can also add OPENAI_API_KEY if you plan to use OpenAI models
        # OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"
        ```
    *   Alternatively, you can set it as an environment variable in your system. The application (specifically `evaluate.py`) will try to load it.

3.  **Run the Setup Script:**
    This script will create a Python virtual environment (`.venv/`), install all required dependencies into it, and initialize the local SQLite database (`database.db`).
    ```bash
    python setup.py
    ```
    *   Follow any prompts from the script.
    *   Ensure this script completes successfully. It handles the installation of packages like `requests`, `beautifulsoup4`, `streamlit`, `google-generativeai`, `toml`, etc.

## Running the Application

Once the setup is complete, you have two primary ways to run the JobFinder application:

**Option 1: Using the provided runner scripts (recommended for ease of use):**

*   **On Windows:** Double-click `run_app.bat` in the project's root directory.
*   **On Linux/macOS:** Open your terminal in the project's root directory and run:
    ```bash
    chmod +x run_app.sh  # Run this once to make the script executable
    ./run_app.sh
    ```

**Option 2: Manually using `python main.py` (after activating the virtual environment):**

1.  **Activate the virtual environment:**
    *   On Windows (PowerShell):
        ```powershell
        .\.venv\Scripts\Activate.ps1
        ```
        (If you encounter an execution policy error, you might need to run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` once in that PowerShell session.)
    *   On Windows (Command Prompt):
        ```cmd
        .\.venv\Scripts\activate.bat
        ```
    *   On Linux/macOS:
        ```bash
        source .venv/bin/activate
        ```
2.  **Run the application:**
    Once the virtual environment is active (your terminal prompt should change), run:
    ```bash
    python main.py
    ```

Either method will launch the JobFinder Streamlit web dashboard in your default web browser (typically at `http://localhost:8501`).

## Using the Dashboard

The JobFinder dashboard provides several pages accessible via the sidebar navigation:

*   **01 Dashboard:**
    *   Displays a list of jobs that have been scraped and approved by the AI.
    *   For each job, you can:
        *   View details (title, location, approval reason).
        *   Click the job title to open the original LinkedIn posting in a new tab.
        *   "Mark as Applied": Updates the job's status.
        *   "Delete": Removes the job from the approved list.
    *   **Sidebar Actions:**
        *   "Start New Job Scan": Initiates the process of scraping LinkedIn and evaluating jobs. Progress will be shown in the terminal running the application.
        *   "Clear All Approved Jobs": Removes all entries from the approved jobs list in the database.

*   **02 Applied Jobs:**
    *   Shows a list of all jobs you have previously marked as "applied."

*   **03 Inputs:**
    *   Allows you to view and modify the application's configuration (`config.toml` file).
    *   You can edit:
        *   Search locations and keywords.
        *   Exclusion keywords to filter out unwanted jobs.
        *   The default resume text used by the AI.
        *   The AI evaluation prompt.
    *   Click "Save Configuration" in the sidebar on this page to save your changes.

## Stopping the Application

To stop the JobFinder application, go to the terminal window where it's running (either the one launched by the runner scripts or the one where you ran `python main.py`) and press `Ctrl+C`.

## Troubleshooting

*   **`ModuleNotFoundError`:** Ensure you have run `python setup.py` successfully and that you are running the application using the virtual environment (either via the runner scripts or by activating it manually before `python main.py`).
*   **API Key Errors:** Double-check that your `GOOGLE_API_KEY` is correctly set in `env.py` or as an environment variable.
*   **Streamlit Errors:** If the dashboard doesn't launch, check the terminal for error messages from Streamlit.
