"""
ATS-safe resume PDF generator.
Reproduces the exact layout of context/resume.pdf (reference).
"""
import os, re, sys
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

W, H = LETTER          # 612 × 792 pt
MARGIN = 0.72 * inch   # ~0.75 in, matching reference
BODY_W = W - 2 * MARGIN

# Font sizes (calibrated to reference PDF)
SZ_NAME    = 22
SZ_CONTACT = 9.5
SZ_SECTION = 11.5
SZ_BODY    = 10
SZ_SUB     = 10        # ### headings (project/job title)
SZ_TECH    = 9.5       # tech stack line

# Skills table label column — wide enough for "AI & Automation:"
SKILL_LABEL_W = 1.55 * inch

# Date regex — matches "May 2027", "Jul 2024 – Present", "January 2024 – May 2024"
_DATE_RE = re.compile(
    r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|'
    r'Dec(?:ember)?)\s+\d{4}'
    r'(?:\s*[–\-]\s*(?:Present|\d{4}|'
    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|'
    r'Dec(?:ember)?)\s+\d{4}))?'
)


# ── Styles ───────────────────────────────────────────────────────────────────

def _st():
    def p(name, **kw):
        base = dict(
            fontName='Helvetica', fontSize=SZ_BODY,
            leading=SZ_BODY * 1.2, alignment=TA_LEFT,
            spaceAfter=0, spaceBefore=0,
        )
        base.update(kw)
        return ParagraphStyle(name, **base)

    return {
        # Header
        'name':    p('name',
                      fontName='Helvetica-Bold', fontSize=SZ_NAME,
                      leading=SZ_NAME * 1.1, alignment=TA_CENTER,
                      spaceAfter=3),
        'contact': p('contact',
                      fontSize=SZ_CONTACT, leading=SZ_CONTACT * 1.3,
                      alignment=TA_CENTER, spaceAfter=4),

        # Section heading (EDUCATION, SKILLS, PROJECTS …)
        'sec':     p('sec',
                      fontName='Helvetica-Bold', fontSize=SZ_SECTION,
                      leading=SZ_SECTION * 1.1,
                      spaceBefore=6, spaceAfter=0),

        # Body variants
        'body':    p('body',    spaceAfter=1),
        'bold':    p('bold',    fontName='Helvetica-Bold', spaceAfter=1),

        # ### sub-heading (project name, job title)
        'sub':     p('sub',     fontName='Helvetica-Bold',
                      fontSize=SZ_SUB, leading=SZ_SUB * 1.2,
                      spaceAfter=1),

        # Tech stack line below project name
        'tech':    p('tech',
                      fontSize=SZ_TECH, leading=SZ_TECH * 1.2,
                      spaceAfter=2),

        # Bullet point
        'bullet':  p('bullet',  leftIndent=0.18 * inch, spaceAfter=1),

        # Right-aligned (used inside date tables)
        'right':   p('right',   alignment=TA_RIGHT),

        # Skills box cells
        'sk_k':    p('sk_k',
                      fontName='Helvetica-Bold', fontSize=SZ_BODY,
                      leading=SZ_BODY * 1.3),
        'sk_v':    p('sk_v',
                      fontSize=SZ_BODY, leading=SZ_BODY * 1.3),
    }


# ── Low-level helpers ────────────────────────────────────────────────────────

def _esc(t: str) -> str:
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def _md(t: str) -> str:
    """Escape XML and convert **bold** to <b> tags."""
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', _esc(t))

def _hr(thickness=0.5, space_after=2, space_before=0, color=colors.black):
    return HRFlowable(
        width='100%', thickness=thickness, color=color,
        spaceBefore=space_before, spaceAfter=space_after,
    )

def _lr_row(left: str, right: str, st: dict, bold=False):
    """Single-row Table: left-aligned text | right-aligned date."""
    ls = st['bold'] if bold else st['body']
    tbl = Table(
        [[Paragraph(_md(left), ls), Paragraph(_esc(right), st['right'])]],
        colWidths=[BODY_W * 0.72, BODY_W * 0.28],
    )
    tbl.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return tbl

def _skills_box(lines: list, st: dict):
    """Render skill lines as a bordered table: **Label:** values."""
    rows = []
    for line in lines:
        if ':' in line:
            label, _, val = line.partition(':')
            rows.append([
                Paragraph(f'<b>{_esc(label.strip())}:</b>', st['sk_k']),
                Paragraph(_esc(val.strip()), st['sk_v']),
            ])
        elif line.strip():
            rows.append(['', Paragraph(_esc(line.strip()), st['sk_v'])])
    if not rows:
        return []
    tbl = Table(rows, colWidths=[SKILL_LABEL_W, BODY_W - SKILL_LABEL_W])
    tbl.setStyle(TableStyle([
        ('BOX',           (0, 0), (-1, -1), 0.5,  colors.black),
        ('INNERGRID',     (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return [tbl]


# ── Pre-processing ───────────────────────────────────────────────────────────

def _preprocess(raw_lines: list) -> list:
    """
    Returns list of (stripped_line, right_date | None).
    Moves 'Graduating: DATE' onto the preceding institution line
    so it renders right-aligned beside the university name.
    """
    result = [(ln.strip(), None) for ln in raw_lines]
    for i, (s, _) in enumerate(result):
        m = re.search(r'Graduating:\s*(.+?)(?:\s*\||\s*$)', s)
        if not m:
            continue
        date_str = m.group(1).strip()
        # Remove the "| Graduating: DATE" fragment from this line
        cleaned = re.sub(
            r'\s*\|?\s*Graduating:\s*' + re.escape(date_str), '', s
        ).strip().rstrip('|').strip()
        result[i] = (cleaned, None)
        # Attach date to the nearest preceding content line
        for j in range(i - 1, max(-1, i - 6), -1):
            ps, _ = result[j]
            if ps and not ps.startswith('#') and not ps.startswith('-'):
                result[j] = (ps, date_str)
                break
    return result


# ── Main markdown → flowable parser ─────────────────────────────────────────

def _parse(text: str, st: dict) -> list:
    lines   = _preprocess(text.splitlines())
    n       = len(lines)
    out     = []
    section = None          # current ## section (lowercase)
    skill_buf = []          # accumulates skill lines for box rendering
    contact_parts = []      # accumulates contact items for one combined line
    in_contact = False
    edu_header_done  = False   # True after first body line of Education
    sec_subhead_count = 0      # ### headings seen in current section
    expect_company   = False   # True right after ### in Experience

    def flush_skills():
        if skill_buf:
            out.extend(_skills_box(skill_buf, st))
            skill_buf.clear()

    def flush_contact():
        if contact_parts:
            out.append(Paragraph(_esc(' | '.join(contact_parts)), st['contact']))
            contact_parts.clear()

    i = 0
    while i < n:
        s, rdate = lines[i]

        # ── H1: name ────────────────────────────────────────────────────────
        if s.startswith('# '):
            out.append(Paragraph(_esc(s[2:].strip()), st['name']))
            in_contact = True
            i += 1
            continue

        # ── Contact block ────────────────────────────────────────────────────
        if in_contact:
            if not s or s.startswith('##'):
                in_contact = False
                flush_contact()
                if not s:
                    i += 1
                continue
            contact_parts.extend(p.strip() for p in s.split('|') if p.strip())
            i += 1
            continue

        # ── H2: section heading ──────────────────────────────────────────────
        if s.startswith('## '):
            flush_skills()
            section           = s[3:].strip().lower()
            edu_header_done   = False
            sec_subhead_count = 0
            expect_company    = False
            out.append(Paragraph(_esc(s[3:].strip().upper()), st['sec']))
            out.append(_hr(0.5, 2))
            i += 1
            continue

        # ── H3: sub-heading (project name, job title) ────────────────────────
        if s.startswith('### '):
            flush_skills()
            # Thin separator before the 2nd+ entry in same section
            if section in ('projects', 'experience') and sec_subhead_count > 0:
                out.append(_hr(0.3, 3, space_before=3))
            out.append(Paragraph(_esc(s[4:].strip()), st['sub']))
            sec_subhead_count += 1
            if section == 'experience':
                expect_company = True
            i += 1
            continue

        # ── Bullet ───────────────────────────────────────────────────────────
        if s.startswith('- '):
            flush_skills()
            expect_company = False
            out.append(Paragraph('• ' + _md(s[2:].strip()), st['bullet']))
            i += 1
            continue

        # ── Blank line ───────────────────────────────────────────────────────
        if not s:
            i += 1
            continue

        # ── Skills accumulation ──────────────────────────────────────────────
        if section == 'skills':
            skill_buf.append(s)
            i += 1
            continue

        # ── Education: first body line = institution name (bold + date) ──────
        if section == 'education' and not edu_header_done:
            edu_header_done = True
            if rdate:
                out.append(_lr_row(s, rdate, st, bold=True))
            else:
                out.append(Paragraph(_esc(s), st['bold']))
            i += 1
            continue

        # ── Pre-attached graduation date on a non-first edu line ─────────────
        if rdate:
            out.append(_lr_row(s, rdate, st))
            i += 1
            continue

        # ── Experience: company/date line immediately after ### ───────────────
        #    Render as plain body (NOT right-aligned) — matches reference PDF
        if expect_company:
            expect_company = False
            out.append(Paragraph(_md(s), st['body']))
            i += 1
            continue

        # ── Affiliations: bold left + right-aligned date ─────────────────────
        if section == 'affiliations':
            m = _DATE_RE.search(s)
            if m:
                date_str = m.group(0)
                before   = s[:m.start()].rstrip(' |:–-').strip()
                after    = s[m.end():].strip().strip('|').strip()
                if not after and before:
                    out.append(_lr_row(before, date_str, st, bold=True))
                    i += 1
                    continue
            out.append(Paragraph(_md(s), st['bold']))
            i += 1
            continue

        # ── Tech stack line (contains • or ·) ────────────────────────────────
        if '•' in s or '·' in s or '\u00b7' in s:
            out.append(Paragraph(_esc(s), st['tech']))
            i += 1
            continue

        # ── Default body ─────────────────────────────────────────────────────
        out.append(Paragraph(_md(s), st['body']))
        i += 1

    flush_skills()
    return out


# ── Public API ───────────────────────────────────────────────────────────────

def generate_resume_pdf(resume_text: str, output_path: str) -> str:
    """Convert tailored markdown resume to ATS-safe one-page PDF."""
    st = _st()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        output_path, pagesize=LETTER,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )
    doc.build(_parse(resume_text, st))
    return output_path


def generate_cover_letter_pdf(
    cover_letter_text: str, company: str, role: str, output_path: str
) -> str:
    """Convert cover letter text to PDF."""
    st = _st()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        output_path, pagesize=LETTER,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )
    header = f'Cover Letter — {role} at {company}'.upper()
    fl = [
        Paragraph(_esc(header), st['sec']),
        _hr(0.5, 8),
        Spacer(1, 4),
    ]
    for para in cover_letter_text.strip().split('\n\n'):
        p = para.strip()
        if p:
            fl.append(Paragraph(_esc(p), st['body']))
            fl.append(Spacer(1, 6))
    doc.build(fl)
    return output_path


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    resume_path = Path(__file__).parent.parent / 'context' / 'resume.md'
    out_dir     = Path(__file__).parent.parent / 'output'
    out_dir.mkdir(exist_ok=True)
    if not resume_path.exists():
        print(f'ERROR: {resume_path} not found')
        sys.exit(1)
    resume_text = resume_path.read_text()
    today = date.today().isoformat()
    out   = out_dir / f'Sachin_Pandey_resume_{today}.pdf'
    result = generate_resume_pdf(resume_text, str(out))
    print(f'Generated: {result} ({os.path.getsize(result):,} bytes)')
