from urllib.parse import quote_plus
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("outreach")


@mcp.tool()
def find_recruiter(company: str, role: str) -> dict:
    """Build LinkedIn search URLs to find a recruiter, hiring manager, or team member."""
    recruiter_url = (
        "https://www.linkedin.com/search/results/people/?keywords="
        + quote_plus(f"{company} recruiter OR talent acquisition")
    )
    manager_url = (
        "https://www.linkedin.com/search/results/people/?keywords="
        + quote_plus(f"{company} {role} manager OR director OR lead")
    )
    engineer_url = (
        "https://www.linkedin.com/search/results/people/?keywords="
        + quote_plus(f"{company} {role} engineer")
    )

    return {
        "urls": [
            {
                "label": "1. Recruiter / Talent Acquisition (open this first)",
                "url": recruiter_url,
            },
            {
                "label": "2. Hiring Manager",
                "url": manager_url,
            },
            {
                "label": "3. Team Member",
                "url": engineer_url,
            },
        ],
        "note": (
            "Open URL #1 first — finding a recruiter or TA person gives you the "
            "fastest path to the hiring team. If no recruiter is visible, try #2."
        ),
    }


@mcp.tool()
def draft_outreach(
    recruiter_name: str,
    company: str,
    role: str,
    my_background: str,
) -> dict:
    """Draft a cold outreach email to a recruiter. Keep it under 150 words."""
    subject = f"{role} at {company} — quick intro"

    body = f"""Hi {recruiter_name},

I'm a CS student at Texas State University (4.0 GPA, May 2027) with hands-on experience building full-stack web apps and AI systems. I came across the {role} role at {company} and was drawn in because [COMPANY_REASON].

Most relevant to this role: I built a RAG-based AI assistant using FastAPI and Qdrant, and a full-stack fitness tracker with React, Node.js, and PostgreSQL — shipping both end-to-end. I also do Python data analysis as a Research Assistant, which maps directly to {company}'s backend-heavy environment.

Happy to share more or connect briefly — no pressure either way.

Sachin Pandey
pandeys2023@gmail.com
linkedin.com/in/pandey-s/
github.com/[github]"""

    word_count = len(body.split())

    return {
        "subject": subject,
        "body": body,
        "word_count": word_count,
        "note": "Replace [COMPANY_REASON] with a specific reason you want to work there.",
    }


if __name__ == "__main__":
    mcp.run()
