import json
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

load_dotenv()

mcp = FastMCP("resume-pdf")

OUTPUT_DIR = Path(__file__).parent.parent / "output"

# Fixed contact / education — only the tailored sections change per job
CONTACT = {
    "name": "Sachin Pandey",
    "location": "San Marcos, TX",
    "phone": "+1-737-213-2760",
    "email": "ihn10@txstate.edu",
    "linkedin": "linkedin.com/in/pandey-s/",
}

EDUCATION = {
    "school": "Texas State University",
    "location": "San Marcos, TX",
    "degree": "Bachelor of Science in Computer Science",
    "gpa": "4.0 / 4.0",
    "graduation": "Expected Graduation: May 2027",
    "courses": (
        "Software Engineering, Data Structures & Algorithms, "
        "Systems Fundamentals, Computer Architecture, Object-Oriented Programming"
    ),
}

AFFILIATIONS = [
    "CodePath — Community Member & Student | February 2025 – Present"
]

# ── Colours ──────────────────────────────────────────────────────────────────
DARK = colors.HexColor("#1a1a1a")
MID = colors.HexColor("#333333")
LIGHT = colors.HexColor("#666666")
ACCENT = colors.HexColor("#1d4e89")  # deep navy — professional


# ── Style helpers ─────────────────────────────────────────────────────────────
def _s(name, **kw) -> ParagraphStyle:
    return ParagraphStyle(name, **kw)


NAME_S = _s("Name", fontName="Helvetica-Bold", fontSize=17,
            textColor=DARK, alignment=TA_CENTER, spaceBefore=6, spaceAfter=4)
CONTACT_S = _s("Contact", fontName="Helvetica", fontSize=8.5,
               textColor=LIGHT, alignment=TA_CENTER, spaceAfter=4)
SECTION_S = _s("Section", fontName="Helvetica-Bold", fontSize=10,
               textColor=ACCENT, spaceBefore=8, spaceAfter=3)
ENTRY_TITLE_S = _s("EntryTitle", fontName="Helvetica-Bold", fontSize=9.5,
                   textColor=DARK, spaceBefore=5, spaceAfter=1)
ENTRY_TITLE_R = _s("EntryTitleR", fontName="Helvetica", fontSize=9,
                   textColor=LIGHT, alignment=TA_RIGHT)
ENTRY_SUB_S = _s("EntrySub", fontName="Helvetica-Oblique", fontSize=8.5,
                 textColor=LIGHT, spaceAfter=2)
BULLET_S = _s("Bullet", fontName="Helvetica", fontSize=8.8,
              textColor=MID, leftIndent=10, spaceAfter=1, leading=12)
SKILL_S = _s("Skill", fontName="Helvetica", fontSize=8.8,
             textColor=MID, spaceAfter=1.5, leading=12)
AFF_S = _s("Aff", fontName="Helvetica", fontSize=8.8,
           textColor=MID, spaceAfter=1)

DIVIDER_STYLE = TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
])


def _hr(after=4):
    return HRFlowable(width="100%", thickness=0.4,
                      color=colors.HexColor("#cccccc"), spaceAfter=after)


def _two_col(left_text, right_text, left_style, right_style, widths=("78%", "22%")):
    t = Table(
        [[Paragraph(left_text, left_style), Paragraph(right_text, right_style)]],
        colWidths=widths,
    )
    t.setStyle(DIVIDER_STYLE)
    return t


# ── PDF builder ───────────────────────────────────────────────────────────────
def _build_pdf(path: str, skills: dict, projects: list, experience: list) -> None:
    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.5 * inch,
    )

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph(CONTACT["name"], NAME_S))
    contact_line = (
        f'{CONTACT["location"]}  |  {CONTACT["phone"]}  |  {CONTACT["email"]}'
        f'  |  {CONTACT["linkedin"]}'
    )
    story.append(Paragraph(contact_line, CONTACT_S))
    story.append(HRFlowable(width="100%", thickness=1.2,
                             color=ACCENT, spaceAfter=6))

    # ── Education ─────────────────────────────────────────────────────────────
    story.append(Paragraph("EDUCATION", SECTION_S))
    story.append(_hr())
    story.append(_two_col(
        f'<b>{EDUCATION["school"]}</b>',
        EDUCATION["location"],
        ENTRY_TITLE_S, ENTRY_TITLE_R,
    ))
    story.append(Paragraph(EDUCATION["degree"], ENTRY_SUB_S))
    story.append(Paragraph(
        f'GPA: {EDUCATION["gpa"]}  |  {EDUCATION["graduation"]}',
        _s("EGPA", fontName="Helvetica", fontSize=8.5,
           textColor=LIGHT, spaceAfter=1),
    ))
    story.append(Paragraph(
        f'<i>Relevant Courses:</i> {EDUCATION["courses"]}',
        _s("ECrs", fontName="Helvetica-Oblique", fontSize=8.2,
           textColor=LIGHT, spaceAfter=2),
    ))

    # ── Skills ────────────────────────────────────────────────────────────────
    story.append(Paragraph("SKILLS", SECTION_S))
    story.append(_hr())
    for category, value in skills.items():
        story.append(Paragraph(f"<b>{category}:</b> {value}", SKILL_S))

    # ── Projects ──────────────────────────────────────────────────────────────
    story.append(Paragraph("PROJECTS", SECTION_S))
    story.append(_hr())
    for proj in projects:
        story.append(Paragraph(f'<b>{proj["name"]}</b>', ENTRY_TITLE_S))
        story.append(Paragraph(
            f'<b>Stack:</b> {proj["stack"]}', ENTRY_SUB_S
        ))
        for bullet in proj.get("bullets", []):
            story.append(Paragraph(f"\u2022 {bullet}", BULLET_S))

    # ── Experience ────────────────────────────────────────────────────────────
    story.append(Paragraph("EXPERIENCE", SECTION_S))
    story.append(_hr())
    for exp in experience:
        story.append(_two_col(
            f'<b>{exp["title"]}</b>',
            exp["dates"],
            ENTRY_TITLE_S, ENTRY_TITLE_R,
        ))
        story.append(Paragraph(exp["company"], ENTRY_SUB_S))
        for bullet in exp.get("bullets", []):
            story.append(Paragraph(f"\u2022 {bullet}", BULLET_S))

    # ── Affiliations ──────────────────────────────────────────────────────────
    story.append(Paragraph("AFFILIATIONS", SECTION_S))
    story.append(_hr())
    for aff in AFFILIATIONS:
        story.append(Paragraph(aff, AFF_S))

    doc.build(story)


# ── MCP Tool ──────────────────────────────────────────────────────────────────
@mcp.tool()
def generate_resume_pdf(
    company: str,
    role: str,
    skills_json: str,
    projects_json: str,
    experience_json: str,
) -> str:
    """
    Generate a tailored, styled PDF resume for a specific job application.
    Returns the absolute path to the PDF so open_and_prefill() can use it.

    skills_json — JSON object: category → comma-separated skills string.
      Ordered top-to-bottom as you want them to appear.
      Example:
        {
          "Languages": "Python, Java, JavaScript, TypeScript, C++",
          "AI & Automation": "RAG, Generative AI, LLM APIs, Qdrant, MCP Servers",
          "Cloud & Deployment": "AWS EC2, Firebase, Vercel, Render",
          "Backend": "FastAPI, Django REST Framework, Node.js, Express",
          "Frontend": "React, Recharts, HTML, CSS",
          "Databases": "PostgreSQL, MongoDB",
          "Tools & Practices": "Git, Agile/Scrum, Jira, RESTful APIs, Pytest, JWT"
        }

    projects_json — JSON array of project objects.
      Each object: { "name": str, "stack": str, "bullets": [str, ...] }
      Example:
        [
          {
            "name": "RAG-Based AI Assistant",
            "stack": "Python · FastAPI · Qdrant · Gemini API",
            "bullets": [
              "Built a Retrieval-Augmented Generation assistant integrating Generative AI...",
              "Developed FastAPI microservices for document ingestion and query handling..."
            ]
          }
        ]

    experience_json — JSON array of experience objects.
      Each object: { "title": str, "company": str, "dates": str, "bullets": [str, ...] }
      Example:
        [
          {
            "title": "Undergraduate Research Assistant",
            "company": "Texas State University",
            "dates": "Jul 2024 – Present",
            "bullets": [
              "Developed Python automation pipelines to process IMU/EMG sensor datasets..."
            ]
          }
        ]
    """
    try:
        skills = json.loads(skills_json)
        projects = json.loads(projects_json)
        experience = json.loads(experience_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON: {e}"})

    OUTPUT_DIR.mkdir(exist_ok=True)
    today = date.today().isoformat()
    safe_co = company.replace(" ", "_").replace("/", "-")
    safe_role = role.replace(" ", "_").replace("/", "-")
    filename = f"{safe_co}_{safe_role}_{today}_resume.pdf"
    pdf_path = OUTPUT_DIR / filename

    try:
        _build_pdf(str(pdf_path), skills, projects, experience)
    except Exception as e:
        return json.dumps({"error": f"PDF generation failed: {e}"})

    return json.dumps({
        "pdf_path": str(pdf_path),
        "filename": filename,
        "message": f"Tailored resume PDF saved → {filename}",
    })


if __name__ == "__main__":
    mcp.run(transport="stdio")
