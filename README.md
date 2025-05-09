# JobFinder

JobFinder is a Python application designed to automate the process of finding relevant job postings from LinkedIn. It scrapes job listings, uses AI (Google Gemini) to evaluate them against your defined criteria and resume, and then presents approved jobs in an interactive web dashboard where you can manage them.

## Prerequisites

*   Python 3.8 or newer.
*   Git (for cloning the repository).
*   Access to Google AI Gemini API and a `GOOGLE_API_KEY`.

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/mbusbee505/JobFinder.git
    cd JobFinder
    ```

2.  **Run the Setup Script:**
    This script will create a Python virtual environment (`.venv/`), install all required dependencies into it, and initialize the local SQLite database (`database.db`).
    ```bash
    python setup.py
    ```
    *   Follow any prompts from the script.
    *   Ensure this script completes successfully. It handles the installation of packages like `requests`, `beautifulsoup4`, `streamlit`, `google-generativeai`, `toml`, etc.

## Running the Application

### Windows

```powershell
.\run_app.bat
```

### Linux \ MacOS

```bash
sudo chmod +x run_app.sh
./run_app.sh
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


