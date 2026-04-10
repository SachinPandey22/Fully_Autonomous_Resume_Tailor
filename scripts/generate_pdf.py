"""
ATS-safe resume and cover letter PDF generator using reportlab.
Uses only Helvetica (built-in, no external fonts) and pure text layout.
"""

import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER


# ── Styles ──────────────────────────────────────────────────────────────────

def _build_styles():
    name_style = ParagraphStyle(
        "Name",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    contact_style = ParagraphStyle(
        "Contact",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    section_style = ParagraphStyle(
        "Section",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=2,
        textTransform="uppercase",
    )
    body_style = ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=10,
        leading=11.5,  # 1.15 × 10
        alignment=TA_LEFT,
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        fontName="Helvetica",
        fontSize=10,
        leading=11.5,
        alignment=TA_LEFT,
        leftIndent=0.15 * inch,
        spaceAfter=2,
    )
    bold_body_style = ParagraphStyle(
        "BoldBody",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=11.5,
        alignment=TA_LEFT,
        spaceAfter=3,
    )
    return {
        "name": name_style,
        "contact": contact_style,
        "section": section_style,
        "body": body_style,
        "bullet": bullet_style,
        "bold_body": bold_body_style,
    }


# ── Inline bold conversion ───────────────────────────────────────────────────

def _md_inline_to_xml(text: str) -> str:
    """Convert **bold** markdown to reportlab XML <b> tags. Escapes & < > first."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return text


# ── Markdown parser → flowable list ─────────────────────────────────────────

def _parse_resume_markdown(text: str, styles: dict) -> list:
    flowables = []
    lines = text.splitlines()
    i = 0
    name_done = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # H1 → name
        if stripped.startswith("# ") and not name_done:
            name = stripped[2:].strip()
            flowables.append(Paragraph(_md_inline_to_xml(name), styles["name"]))
            name_done = True
            i += 1
            continue

        # Line immediately after name that looks like contact info
        if name_done and i > 0 and not stripped.startswith("#") and not stripped.startswith("-"):
            prev_was_name = lines[i - 1].strip().startswith("# ")
            if prev_was_name and stripped:
                flowables.append(Paragraph(_md_inline_to_xml(stripped), styles["contact"]))
                i += 1
                continue

        # H2 → section heading + HR
        if stripped.startswith("## "):
            heading = stripped[3:].strip().upper()
            flowables.append(Spacer(1, 4))
            flowables.append(Paragraph(heading, styles["section"]))
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceAfter=3))
            i += 1
            continue

        # H3 → bold body (sub-heading like job title or project name)
        if stripped.startswith("### "):
            text_content = stripped[4:].strip()
            flowables.append(Paragraph(_md_inline_to_xml(text_content), styles["bold_body"]))
            i += 1
            continue

        # Bullet
        if stripped.startswith("- "):
            bullet_text = "• " + stripped[2:].strip()
            flowables.append(Paragraph(_md_inline_to_xml(bullet_text), styles["bullet"]))
            i += 1
            continue

        # Blank line → small spacer
        if not stripped:
            flowables.append(Spacer(1, 2))
            i += 1
            continue

        # Everything else → body
        flowables.append(Paragraph(_md_inline_to_xml(stripped), styles["body"]))
        i += 1

    return flowables


# ── Public API ───────────────────────────────────────────────────────────────

def generate_resume_pdf(resume_text: str, output_path: str) -> str:
    """Convert markdown resume text to an ATS-safe PDF. Returns output_path."""
    styles = _build_styles()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    flowables = _parse_resume_markdown(resume_text, styles)
    doc.build(flowables)
    return output_path


def generate_cover_letter_pdf(
    cover_letter_text: str,
    company: str,
    role: str,
    output_path: str,
) -> str:
    """Convert cover letter text to PDF. Returns output_path."""
    styles = _build_styles()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    header = f"Cover Letter — {role} at {company}".upper()
    flowables = [
        Paragraph(header, styles["section"]),
        HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceAfter=10),
        Spacer(1, 6),
    ]

    for para in cover_letter_text.strip().split("\n\n"):
        stripped = para.strip()
        if stripped:
            flowables.append(Paragraph(_md_inline_to_xml(stripped), styles["body"]))
            flowables.append(Spacer(1, 8))

    doc.build(flowables)
    return output_path


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    from datetime import date

    resume_path = Path(__file__).parent.parent / "context" / "resume.md"
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    if not resume_path.exists():
        print(f"ERROR: {resume_path} not found.")
        sys.exit(1)

    resume_text = resume_path.read_text()
    today = date.today().isoformat()
    out = output_dir / f"Sachin_Pandey_resume_{today}.pdf"
    result = generate_resume_pdf(resume_text, str(out))
    size = os.path.getsize(result)
    print(f"Generated: {result} ({size:,} bytes)")
