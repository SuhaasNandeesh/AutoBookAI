from langchain_core.tools import tool
from typing import Optional
from datetime import datetime
from autobook_ai.rag import create_rag_chain, create_retriever

# --- RAG Tool ---
# We create the RAG chain once and wrap it in a tool.
rag_chain = create_rag_chain(create_retriever())

@tool
def search_knowledge_base(query: str) -> str:
    """
    Use this tool to get information about services, availability, and general policies.
    This should be your first step to answer any user question.
    For example: 'What are the clinic's hours?' or 'What kind of food does The Gourmet Table serve?'

    Args:
        query: The user's question to search for in the knowledge base.
    """
    print(f"---TOOL: Searching knowledge base for '{query}'---")
    return rag_chain.invoke(query)

# --- Calendar Tools ---

@tool
def check_calendar_availability(date: str) -> str:
    """
    Checks the calendar for available appointment slots on a given date.
    Use this *after* you have confirmed the service's general availability from the knowledge base.

    Args:
        date: The date to check for availability, in YYYY-MM-DD format.
    """
    print(f"---TOOL: Checking calendar for {date}---")
    try:
        requested_date = datetime.strptime(date, "%Y-%m-%d").date()
        if requested_date.weekday() >= 5:
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
    Only use this tool when you have all the necessary information and the user has confirmed the booking.

    Args:
        date: The date for the event in YYYY-MM-DD format.
        time: The time for the event in HH:MM AM/PM format.
        title: The title of the event.
        participants: A list of email addresses to invite.
    """
    print(f"---TOOL: Creating invite for '{title}' at {time} on {date}---")
    return f"Success: The calendar invite '{title}' has been created for {date} at {time}."

# A list of all available tools for the agent
all_tools = [search_knowledge_base, check_calendar_availability, create_calendar_invite]
