from langchain_core.tools import tool
from typing import Optional
from datetime import datetime

@tool
def check_calendar_availability(date: str) -> str:
    """
    Checks the calendar for available slots on a given date.

    Args:
        date: The date to check for availability, in YYYY-MM-DD format.
    """
    # This is a simulated tool. In a real application, this would
    # interact with a calendar API (e.g., Google Calendar, Outlook).
    print(f"---TOOL: Checking calendar for {date}---")

    # Simulate some logic
    try:
        requested_date = datetime.strptime(date, "%Y-%m-%d").date()
        if requested_date.weekday() >= 5: # Saturday or Sunday
            return f"No availability on {date} as it is a weekend. Please suggest a weekday."
        else:
            return f"The calendar shows open slots at 10:00 AM, 2:00 PM, and 4:00 PM on {date}."
    except ValueError:
        return "Error: Please provide the date in YYYY-MM-DD format."

@tool
def create_calendar_invite(
    date: str,
    time: str,
    title: str,
    participants: Optional[list] = None
) -> str:
    """
    Creates a new calendar invite for a specific date and time.

    Args:
        date: The date for the event in YYYY-MM-DD format.
        time: The time for the event in HH:MM AM/PM format.
        title: The title of the event.
        participants: A list of email addresses to invite.
    """
    # This is a simulated tool.
    print(f"---TOOL: Creating invite for {title} at {time} on {date}---")

    # Simulate success
    return f"Success: The calendar invite '{title}' has been created for {date} at {time}."

# A list of all available tools for the agent
all_tools = [check_calendar_availability, create_calendar_invite]
