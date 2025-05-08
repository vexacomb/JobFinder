import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def generate_html_email(new_jobs, rejected_jobs, cost_this_run=None, remaining_balance=None):
    """
    Generate HTML email content for job report
    """
    css_styles = """
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }
        .container {
            width: 90%;
            max-width: 800px;
            margin: auto;
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1, h2, h3 {
            color: #333333;
        }
        .stats-box {
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            border: 1px solid #dddddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .job-title {
            color: #2b6cb0;
            font-weight: bold;
        }
        .location {
            color: #4a5568;
        }
        .description {
            max-height: 100px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .job-link {
            color: #2b6cb0;
            text-decoration: none;
        }
        .job-link:hover {
            text-decoration: underline;
        }
        .accepted {
            background-color: #f0fff4;
        }
    """

    html = f"""
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <style>
                {css_styles}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>SOC Analyst Job Search Report</h1>
                
                <div class="stats-box">
                    <h3>Search Statistics</h3>
                    <p>New Jobs Found: {len(new_jobs)}</p>
                    {f'<p>API Cost This Run: ${cost_this_run:.2f}</p>' if cost_this_run is not None else ''}
                    {f'<p>Remaining API Balance: ${remaining_balance:.2f}</p>' if remaining_balance is not None else ''}
                </div>
    """

    if new_jobs:
        html += """
                <h2>New Matching Jobs</h2>
                <table>
                    <tr>
                        <th>Job Title</th>
                        <th>Location</th>
                        <th>Action</th>
                    </tr>
        """
        
        for job in new_jobs:
            html += f"""
                    <tr class="accepted">
                        <td>
                            <div class="job-title">{job['title']}</div>
                            <div class="description">{job['description'][:200]}...</div>
                        </td>
                        <td class="location">{job['location']}</td>
                        <td><a href="{job['url']}" class="job-link" target="_blank">View Job</a></td>
                    </tr>
            """
        
        html += "</table>"

    html += """
            </div>
        </body>
    </html>
    """
    
    return html

def send_email(sender, receiver, smtp_server, smtp_port, login, password, html_body):
    """
    Sends an HTML formatted email with the job report
    """
    subject = "SOC Analyst Job Search Report"
    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(login, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")