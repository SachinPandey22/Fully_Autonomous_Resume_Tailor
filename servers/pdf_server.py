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
    KeepInFrame,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

load_dotenv()

mcp = FastMCP("resume-pdf")

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "pdf"

# Fixed contact / education — only the tailored sections change per job
CONTACT = {
    "name": "Sachin Pandey",
    "location": "San Marcos, TX",
    "phone": "+1-737-213-2760",
    "email": "pandeys2023@gmail.com",
    "linkedin": "linkedin.com/in/pandey-s/",
    "github": "github.com/sachinpandey22",
}

EDUCATION = {
    "school": "Texas State University",
    "location": "San Marcos, TX",
    "degree": "Bachelor of Science in Computer Science",
    "gpa": "3.96 / 4.0",
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
            textColor=DARK, alignment=TA_CENTER, spaceBefore=4, spaceAfter=8)
CONTACT_S = _s("Contact", fontName="Helvetica", fontSize=8.5,
               textColor=LIGHT, alignment=TA_CENTER, spaceAfter=3)
SECTION_S = _s("Section", fontName="Helvetica-Bold", fontSize=11,
               textColor=DARK, spaceBefore=6, spaceAfter=2)
ENTRY_TITLE_S = _s("EntryTitle", fontName="Helvetica-Bold", fontSize=9.5,
                   textColor=DARK, spaceBefore=3, spaceAfter=1)
ENTRY_TITLE_R = _s("EntryTitleR", fontName="Helvetica", fontSize=9,
                   textColor=MID, alignment=TA_RIGHT)
ENTRY_SUB_S = _s("EntrySub", fontName="Helvetica-Oblique", fontSize=8.5,
                 textColor=MID, spaceAfter=1)
BULLET_S = _s("Bullet", fontName="Helvetica", fontSize=9,
              textColor=MID, leftIndent=28, firstLineIndent=-12,
              spaceAfter=0.5, leading=11)
SKILL_S = _s("Skill", fontName="Helvetica", fontSize=8.8,
             textColor=MID, spaceAfter=1, leading=11)
AFF_S = _s("Aff", fontName="Helvetica", fontSize=8.8,
           textColor=MID, spaceAfter=1)

DIVIDER_STYLE = TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
])


def _hr(after=3):
    return HRFlowable(width="100%", thickness=0.4,
                      color=colors.HexColor("#cccccc"), spaceAfter=after)


def _two_col(left_text, right_text, left_style, right_style, widths=(5.694 * inch, 1.606 * inch)):
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
        topMargin=0.5 * inch,
        bottomMargin=0.45 * inch,
    )

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph(CONTACT["name"], NAME_S))
    contact_line = (
        f'{CONTACT["location"]}  |  {CONTACT["phone"]}  |  {CONTACT["email"]}'
        f'  |  {CONTACT["linkedin"]}  |  {CONTACT["github"]}'
    )
    story.append(Paragraph(contact_line, CONTACT_S))
    story.append(HRFlowable(width="100%", thickness=1.2,
                             color=DARK, spaceAfter=6))

    # ── Education ─────────────────────────────────────────────────────────────
    story.append(Paragraph("<u>EDUCATION</u>", SECTION_S))
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
           textColor=MID, spaceAfter=1),
    ))
    story.append(Paragraph(
        f'<i>Relevant Courses:</i> {EDUCATION["courses"]}',
        _s("ECrs", fontName="Helvetica", fontSize=8.5,
           textColor=MID, spaceAfter=2),
    ))

    # ── Skills ────────────────────────────────────────────────────────────────
    story.append(Paragraph("<u>SKILLS</u>", SECTION_S))
    story.append(_hr())
    for category, value in skills.items():
        story.append(Paragraph(f"<b>{category}:</b> {value}", SKILL_S))

    # ── Projects ──────────────────────────────────────────────────────────────
    story.append(Paragraph("<u>PROJECTS</u>", SECTION_S))
    story.append(_hr())
    for proj in projects:
        story.append(Paragraph(f'<b>{proj["name"]}</b>', ENTRY_TITLE_S))
        story.append(Paragraph(
            f'<b>Stack:</b> {proj["stack"]}', ENTRY_SUB_S
        ))
        for bullet in proj.get("bullets", []):
            story.append(Paragraph(f'<font size="11">\u2022</font> {bullet}', BULLET_S))

    # ── Experience ────────────────────────────────────────────────────────────
    story.append(Paragraph("<u>EXPERIENCE</u>", SECTION_S))
    story.append(_hr())
    for exp in experience:
        story.append(_two_col(
            f'<b>{exp["title"]}</b>',
            exp["dates"],
            ENTRY_TITLE_S, ENTRY_TITLE_R,
        ))
        story.append(Paragraph(exp["company"], ENTRY_SUB_S))
        for bullet in exp.get("bullets", []):
            story.append(Paragraph(f'<font size="11">\u2022</font> {bullet}', BULLET_S))

    # ── Affiliations ──────────────────────────────────────────────────────────
    story.append(Paragraph("<u>AFFILIATIONS</u>", SECTION_S))
    story.append(_hr())
    for aff in AFFILIATIONS:
        story.append(Paragraph(aff, AFF_S))

    page_w, page_h = letter
    frame_w = page_w - 0.6 * inch - 0.6 * inch
    frame_h = page_h - 0.5 * inch - 0.45 * inch
    doc.build([KeepInFrame(frame_w, frame_h, story, mode="shrink")])


# ── MCP Tool ──────────────────────────────────────────────────────────────────
@mcp.tool()
def generate_resume_pdf(
    company: str,
    role: str,
    tailored_json_path: str,
) -> str:
    """
    Generate a tailored, styled PDF resume for a specific job application.
    Returns the absolute path to the PDF.

    tailored_json_path — absolute path to a JSON file with this schema:
      {
        "skills": {
          "Languages": "Python, Java, JavaScript",
          "Backend": "FastAPI, Node.js, Express",
          ...
        },
        "projects": [
          {
            "name": "Project Name",
            "stack": "React · Node.js · PostgreSQL",
            "bullets": ["bullet 1", "bullet 2"]
          }
        ],
        "experience": [
          {
            "title": "Job Title",
            "company": "Company Name",
            "dates": "Jan 2024 – Present",
            "bullets": ["bullet 1"]
          }
        ]
      }

    Write this file (output/[Company]_[Role]_tailored.json) before calling this tool.
    The user can edit it to tweak bullets or reorder skills before PDF generation.
    """
    try:
        data = json.loads(Path(tailored_json_path).read_text())
        skills = data["skills"]
        projects = data["projects"]
        experience = data["experience"]
    except (OSError, json.JSONDecodeError, KeyError) as e:
        return json.dumps({"error": f"Failed to read tailored JSON: {e}"})

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


# ── Cover Letter PDF builder ──────────────────────────────────────────────────
def _build_coverletter_pdf(path: str, company: str, role: str, body: str) -> None:
    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        leftMargin=1.0 * inch,
        rightMargin=1.0 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
    )

    story = []

    # Header
    story.append(Paragraph(CONTACT["name"], _s(
        "CLName", fontName="Helvetica-Bold", fontSize=14,
        textColor=DARK, alignment=TA_LEFT, spaceAfter=8,
    )))
    contact_line = (
        f'{CONTACT["location"]}  ·  {CONTACT["phone"]}  ·  {CONTACT["email"]}'
        f'  ·  {CONTACT["linkedin"]}'
    )
    story.append(Paragraph(contact_line, _s(
        "CLContact", fontName="Helvetica", fontSize=9,
        textColor=LIGHT, alignment=TA_LEFT, spaceAfter=2,
    )))
    story.append(HRFlowable(width="100%", thickness=0.8, color=ACCENT, spaceAfter=0))

    # Date + recipient
    story.append(Paragraph(date.today().strftime("%B %d, %Y"), _s(
        "CLDate", fontName="Helvetica", fontSize=10,
        textColor=MID, spaceBefore=16, spaceAfter=4,
    )))
    story.append(Paragraph(f"Hiring Team<br/>{company}", _s(
        "CLRecipient", fontName="Helvetica", fontSize=10,
        textColor=MID, spaceAfter=12,
    )))

    # Subject line
    story.append(Paragraph(f"Re: <b>{role}</b>", _s(
        "CLSubject", fontName="Helvetica-Bold", fontSize=10.5,
        textColor=DARK, spaceAfter=14,
    )))

    # Body paragraphs
    body_style = _s(
        "CLBody", fontName="Helvetica", fontSize=10.5,
        textColor=MID, leading=15, spaceAfter=10,
    )
    for para in [p.strip() for p in body.strip().split("\n\n") if p.strip()]:
        story.append(Paragraph(para.replace("\n", " "), body_style))

    # Closing
    story.append(Paragraph("Sincerely,", _s(
        "CLClosing", fontName="Helvetica", fontSize=10.5,
        textColor=MID, spaceBefore=8, spaceAfter=2,
    )))
    story.append(Paragraph(CONTACT["name"], _s(
        "CLSig", fontName="Helvetica-Bold", fontSize=10.5, textColor=DARK,
    )))

    doc.build(story)


@mcp.tool()
def generate_coverletter_pdf(
    company: str,
    role: str,
    cover_letter_text: str,
) -> str:
    """
    Generate a styled cover letter PDF.
    Returns the absolute path to the PDF.

    cover_letter_text — the full cover letter body (plain text, paragraphs
    separated by double newlines). Do NOT include a salutation or closing —
    those are added automatically.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    safe_co = company.replace(" ", "_").replace("/", "-")
    safe_role = role.replace(" ", "_").replace("/", "-")
    filename = f"{safe_co}_{safe_role}_{today}_coverletter.pdf"
    pdf_path = OUTPUT_DIR / filename

    try:
        _build_coverletter_pdf(str(pdf_path), company, role, cover_letter_text)
    except Exception as e:
        return json.dumps({"error": f"Cover letter PDF generation failed: {e}"})

    return json.dumps({
        "pdf_path": str(pdf_path),
        "filename": filename,
        "message": f"Cover letter PDF saved → {filename}",
    })


if __name__ == "__main__":
    mcp.run(transport="stdio")
