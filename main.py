
import os
import sys
import requests
import smtplib

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


def get_env_var(var_name):
    value = os.getenv(var_name)

    if not value:
        raise ValueError(
            f"Missing environment variable: {var_name}"
        )

    return value.strip()


# ============================================================
# CONFIGURATION
# ============================================================

CMS_URL = "https://cms.must.edu.pk:8082/login.aspx"

ASSIGNMENTS_URL = (
    "https://cms.must.edu.pk:8082/"
    "CoursePortalPendingAssignments.aspx"
)

ROLL_NO = get_env_var("ROLL_NO")
PASSWORD = get_env_var("PASSWORD")
EMAIL_SENDER = get_env_var("EMAIL_SENDER")
EMAIL_PASSWORD = get_env_var("EMAIL_PASSWORD")
EMAIL_TO = get_env_var("EMAIL_TO")
SESSION_VALUE = get_env_var("SESSION")
PROGRAM_VALUE = get_env_var("PROGRAM")


# ============================================================
# LOGIN
# ============================================================

def login_and_get_session():
    """Login to MUST CMS and return authenticated session."""

    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    })

    # --------------------------------------------------------
    # GET LOGIN PAGE
    # --------------------------------------------------------

    try:
        response = session.get(
            CMS_URL,
            timeout=30
        )

        print(
            f"Login page status: {response.status_code}"
        )

        response.raise_for_status()

    except requests.RequestException as e:
        print(
            f"Failed to open CMS login page: {e}"
        )
        return None

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    form = soup.find("form")

    if not form:
        print("Login form was not found.")
        return None

    print("Login form found.")

    # --------------------------------------------------------
    # SHOW ACTUAL SESSION VALUES
    # --------------------------------------------------------

    print("\n===== SESSION OPTIONS =====")

    for select in form.find_all("select"):

        name = select.get("name", "")

        if "session" in name.lower():

            for option in select.find_all("option"):

                print(
                    f"TEXT: {option.get_text(strip=True)} "
                    f"| VALUE: {option.get('value', '')}"
                )

    # --------------------------------------------------------
    # SHOW ACTUAL PROGRAM VALUES
    # --------------------------------------------------------

    print("\n===== PROGRAM OPTIONS =====")

    for select in form.find_all("select"):

        name = select.get("name", "")

        if "program" in name.lower():

            for option in select.find_all("option"):

                print(
                    f"TEXT: {option.get_text(strip=True)} "
                    f"| VALUE: {option.get('value', '')}"
                )

    print()

    # --------------------------------------------------------
    # COLLECT HIDDEN ASP.NET FIELDS
    # --------------------------------------------------------

    data = {}

    for element in form.find_all("input"):

        name = element.get("name")

        if not name:
            continue

        input_type = element.get(
            "type",
            "text"
        ).lower()

        if input_type == "hidden":

            data[name] = element.get(
                "value",
                ""
            )

    # --------------------------------------------------------
    # FIND ROLL NUMBER INPUT
    # --------------------------------------------------------

    roll_input = form.find(
        "input",
        {
            "name": "txt_RollNo"
        }
    )

    if roll_input:
        data["txt_RollNo"] = ROLL_NO
    else:
        print(
            "Warning: txt_RollNo was not found."
        )

    # --------------------------------------------------------
    # FIND PASSWORD INPUT
    # --------------------------------------------------------

    password_input = form.find(
        "input",
        {
            "name": "txt_Password"
        }
    )

    if password_input:
        data["txt_Password"] = PASSWORD
    else:
        print(
            "Warning: txt_Password was not found."
        )

    # --------------------------------------------------------
    # SESSION
    # --------------------------------------------------------

    session_select = form.find(
        "select",
        {
            "name": "ddl_Session"
        }
    )

    if session_select:

        session_value = None

        for option in session_select.find_all("option"):

            text_value = option.get_text(
                strip=True
            )

            option_value = option.get(
                "value",
                ""
            ).strip()

            if (
                text_value == SESSION_VALUE
                or option_value == SESSION_VALUE
            ):
                session_value = option_value
                break

        if session_value is None:
            print(
                f"Warning: Session '{SESSION_VALUE}' "
                "was not found."
            )

            session_value = SESSION_VALUE

        data["ddl_Session"] = session_value

    # --------------------------------------------------------
    # PROGRAM
    # --------------------------------------------------------

    program_select = form.find(
        "select",
        {
            "name": "ddl_Program"
        }
    )

    if program_select:

        program_value = None

        for option in program_select.find_all("option"):

            text_value = option.get_text(
                strip=True
            )

            option_value = option.get(
                "value",
                ""
            ).strip()

            if (
                text_value == PROGRAM_VALUE
                or option_value == PROGRAM_VALUE
            ):
                program_value = option_value
                break

        if program_value is None:
            print(
                f"Warning: Program '{PROGRAM_VALUE}' "
                "was not found."
            )

            program_value = PROGRAM_VALUE

        data["ddl_Program"] = program_value

    # --------------------------------------------------------
    # SUBMIT BUTTON
    # --------------------------------------------------------

    button = form.find(
        "input",
        {
            "name": "btn_StudentSignIn"
        }
    )

    if button:

        data["btn_StudentSignIn"] = button.get(
            "value",
            "Sign In"
        )

    # --------------------------------------------------------
    # DISPLAY SUBMITTED VALUES
    # --------------------------------------------------------

    print("===== LOGIN DATA =====")

    for key, value in data.items():

        # Don't print passwords
        if "password" in key.lower():
            print(f"{key}: ********")
        else:
            print(f"{key}: {value}")

    print("======================\n")

    # --------------------------------------------------------
    # POST LOGIN
    # --------------------------------------------------------

    try:

        response = session.post(
            CMS_URL,
            data=data,
            headers={
                "Referer": CMS_URL,
                "Origin": "https://cms.must.edu.pk"
            },
            timeout=30
        )

        print(
            f"Login POST status: {response.status_code}"
        )

    except requests.RequestException as e:

        print(
            f"Login POST request failed: {e}"
        )

        return None

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    if response.status_code == 200:

        if "DashBoard.aspx" in response.text:

            print("Login successful.")

            return session

        print(
            "Login POST completed, but login failed."
        )

        return None

    # --------------------------------------------------------
    # SERVER ERROR
    # --------------------------------------------------------

    print(
        f"Login failed with HTTP status: "
        f"{response.status_code}"
    )

    if response.status_code == 500:

        print(
            "\nMUST CMS returned HTTP 500."
        )

        print(
            "\nServer response:"
        )

        print(
            response.text[:3000]
        )

    return None

# ============================================================
# CHECK ASSIGNMENTS
# ============================================================

def check_assignments():

    session = login_and_get_session()

    if session is None:
        return

    try:

        response = session.get(
            ASSIGNMENTS_URL,
            timeout=30
        )

        response.raise_for_status()

    except requests.RequestException as e:

        print(
            f"Failed to fetch assignments page: {e}"
        )

        return

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    assignments_table = soup.find(
        "table",
        {
            "id": "ctl00_DataContent_gvPortalSummary"
        }
    )

    if not assignments_table:

        print(
            "No pending assignments table found."
        )

        return

    rows = assignments_table.find_all(
        "tr",
        class_=[
            "GridItem",
            "GridAlternatingItem"
        ]
    )

    assignments = []

    for row in rows:

        columns = row.find_all("td")

        if len(columns) < 4:
            continue

        course_title = columns[1].get_text(
            strip=True
        )

        assignment_title = columns[2].get_text(
            strip=True
        )

        deadline = columns[3].get_text(
            strip=True
        )

        assignment = (
            f"Course: {course_title}\n"
            f"Assignment: {assignment_title}\n"
            f"Deadline: {deadline}"
        )

        assignments.append(
            assignment
        )

    if assignments:

        print(
            f"Found {len(assignments)} "
            "pending assignment(s)."
        )

        send_email(assignments)

    else:

        print(
            "No pending assignments found."
        )


# ============================================================
# SEND EMAIL
# ============================================================

def send_email(assignments):

    subject = (
        "MUST Pending Assignments Notification"
    )

    body = (
        "You have pending assignments "
        "on MUST CMS.\n\n"
        + "\n\n".join(assignments)
    )

    message = MIMEMultipart()

    message["From"] = EMAIL_SENDER
    message["To"] = EMAIL_TO
    message["Subject"] = subject

    message.attach(
        MIMEText(
            body,
            "plain"
        )
    )

    try:

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=30
        ) as server:

            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(
                EMAIL_SENDER,
                EMAIL_PASSWORD
            )

            server.sendmail(
                EMAIL_SENDER,
                EMAIL_TO,
                message.as_string()
            )

        print(
            "Email notification sent successfully."
        )

    except smtplib.SMTPAuthenticationError:

        print(
            "Gmail authentication failed."
        )

        print(
            "Use your Gmail App Password, "
            "not your normal Gmail password."
        )

    except smtplib.SMTPException as e:

        print(
            f"Email sending failed: {e}"
        )

    except Exception as e:

        print(
            f"Unexpected email error: {e}"
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 50)
    print(
        "MUST Assignment Notification Agent"
    )
    print("=" * 50)

    try:

        check_assignments()

    except ValueError as e:

        print(
            f"Configuration error: {e}"
        )

        sys.exit(1)

    except KeyboardInterrupt:

        print(
            "\nAgent stopped by user."
        )

    except Exception as e:

        print(
            f"Unexpected error: {e}"
        )

        sys.exit(1)
