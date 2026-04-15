import json
from urllib.parse import quote_plus

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("outreach")

SACHIN = {
    "name": "Sachin Pandey",
    "email": "pandeys2023@gmail.com",
    "linkedin": "linkedin.com/in/pandey-s/",
}


@mcp.tool()
def find_recruiter(company: str, role: str) -> str:
    """
    Build LinkedIn search URLs to find recruiters and employees at a company.
    Does not scrape LinkedIn — returns search URLs for manual use.
    """
    company_enc = quote_plus(company)
    role_enc = quote_plus(role)

    recruiter_url = (
        f"https://www.linkedin.com/search/results/people/"
        f"?keywords={company_enc}+recruiter+OR+talent+acquisition"
    )
    employee_url = (
        f"https://www.linkedin.com/search/results/people/"
        f"?keywords={company_enc}+{role_enc}"
    )

    note = (
        f"Open these URLs in your browser (must be logged into LinkedIn):\n"
        f"1. Recruiters at {company}: {recruiter_url}\n"
        f"2. {role} employees at {company}: {employee_url}\n\n"
        f"Find a recruiter or hiring manager, get their name, then call draft_outreach()."
    )
    return note


@mcp.tool()
def draft_outreach(
    recruiter_name: str,
    company: str,
    role_applying: str,
    my_background: str,
    company_reason: str = "",
) -> str:
    """
    Generate a cold outreach email to a recruiter and return structured JSON
    ready to pipe into gmail_create_draft.

    recruiter_name: first name (or full name) of the recruiter.
    company: target company name.
    role_applying: job title you are applying for.
    my_background: 1-2 sentence summary (e.g. 'CS junior at Texas State, 4.0 GPA,
                   built full-stack apps and a RAG AI assistant').
    company_reason: why this company specifically (optional — if omitted a placeholder
                    is left so you can fill it in Gmail before sending).

    Returns JSON: { subject, body, to, word_count }
    Pass subject + body directly to gmail_create_draft.
    """
    reason = company_reason if company_reason else f"[FILL IN: why {company} specifically]"

    subject = f"{role_applying} at {company} — quick introduction"

    body = (
        f"Hi {recruiter_name},\n\n"
        f"{my_background} "
        f"I'm currently seeking a {role_applying} opportunity and {company} stood out to me.\n\n"
        f"I'm particularly drawn to {company} because {reason}. "
        f"I believe my background aligns well with what your team is building.\n\n"
        f"Would you be open to a 15-minute call? "
        f"No pressure — happy to connect asynchronously too.\n\n"
        f"Thank you for your time.\n\n"
        f"Best,\n"
        f"{SACHIN['name']}\n"
        f"{SACHIN['email']} | {SACHIN['linkedin']}"
    )

    word_count = len(body.split())
    return json.dumps({
        "subject": subject,
        "body": body,
        "to": "",
        "word_count": word_count,
        "note": "Pass subject + body to gmail_create_draft. Fill in recruiter email in 'to'. Fill in [FILL IN] if present.",
    }, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
