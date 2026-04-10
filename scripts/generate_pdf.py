"""
ATS-safe resume PDF generator — one page, matches reference layout.
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

W, H = LETTER
MARGIN = 0.65 * inch
BODY_W = W - 2 * MARGIN

SZ_NAME    = 20
SZ_CONTACT = 9
SZ_SECTION = 10.5
SZ_BODY    = 9.5

# Matches dates like "May 2027", "Jul 2024 – Present", "January 2024 – May 2024"
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
    def p(n, **k):
        d = dict(fontName='Helvetica', fontSize=SZ_BODY, leading=SZ_BODY * 1.2,
                 alignment=TA_LEFT, spaceAfter=0, spaceBefore=0)
        d.update(k)
        return ParagraphStyle(n, **d)
    return {
        'name':    p('name', fontName='Helvetica-Bold', fontSize=SZ_NAME,
                      leading=SZ_NAME * 1.1, alignment=TA_CENTER, spaceAfter=2),
        'contact': p('contact', fontSize=SZ_CONTACT, leading=SZ_CONTACT * 1.3,
                      alignment=TA_CENTER, spaceAfter=2),
        'sec':     p('sec', fontName='Helvetica-Bold', fontSize=SZ_SECTION,
                      leading=SZ_SECTION * 1.1, spaceBefore=5, spaceAfter=1),
        'body':    p('body', spaceAfter=1),
        'bold':    p('bold', fontName='Helvetica-Bold', spaceAfter=1),
        'sub':     p('sub', fontName='Helvetica-Bold', spaceAfter=0),
        'tech':    p('tech', fontSize=SZ_BODY - 0.5, leading=(SZ_BODY - 0.5) * 1.2,
                      spaceAfter=1),
        'bullet':  p('bullet', leftIndent=0.12 * inch, spaceAfter=1),
        'right':   p('right', alignment=TA_RIGHT),
        'sk_k':    p('sk_k', fontName='Helvetica-Bold', fontSize=SZ_BODY,
                      leading=SZ_BODY * 1.25),
        'sk_v':    p('sk_v', fontSize=SZ_BODY, leading=SZ_BODY * 1.25),
    }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def _md(t):
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', _esc(t))

def _lr_row(left, right, st, bold=False):
    """Table row with left text and right-aligned date."""
    ls = st['bold'] if bold else st['body']
    t = Table(
        [[Paragraph(_md(left), ls), Paragraph(_esc(right), st['right'])]],
        colWidths=[BODY_W * 0.70, BODY_W * 0.30],
    )
    t.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    return t

def _skills_box(lines, st):
    """Render skill lines as a bordered table: bold label | values."""
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
    cw = 1.5 * inch
    t = Table(rows, colWidths=[cw, BODY_W - cw])
    t.setStyle(TableStyle([
        ('BOX',           (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID',     (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return [t]


# ── Pre-processing: move graduation date to university line ──────────────────

def _preprocess(raw_lines):
    """
    Returns list of (stripped_line, right_date | None).
    Finds 'Graduating: DATE' and attaches the date to the preceding
    institution line for right-aligned display.
    """
    result = [(l.strip(), None) for l in raw_lines]

    for i, (s, _) in enumerate(result):
        m = re.search(r'Graduating:\s*(.+?)(?:\s*\||\s*$)', s)
        if m:
            date_str = m.group(1).strip()
            # Strip "Graduating: DATE" from this line
            new_s = re.sub(
                r'\s*\|?\s*Graduating:\s*' + re.escape(date_str), '', s
            ).strip().rstrip('|').strip()
            result[i] = (new_s, None)
            # Attach date to the most recent non-blank, non-heading line
            for j in range(i - 1, max(-1, i - 6), -1):
                ps, pd = result[j]
                if ps and not ps.startswith('#') and not ps.startswith('-'):
                    result[j] = (ps, date_str)
                    break

    return result


# ── Main parser ──────────────────────────────────────────────────────────────

def _parse(text, st):
    raw_lines = text.splitlines()
    lines = _preprocess(raw_lines)
    n = len(lines)
    out = []
    section = None
    skill_buf = []
    contact_lines = []
    in_contact = False
    edu_header_done = False  # tracks if education institution line has been rendered

    def flush_skills():
        if skill_buf:
            out.extend(_skills_box(skill_buf, st))
            skill_buf.clear()

    def flush_contact():
        if contact_lines:
            combined = ' | '.join(contact_lines)
            out.append(Paragraph(_esc(combined), st['contact']))
            contact_lines.clear()

    i = 0
    while i < n:
        s, rdate = lines[i]

        # H1 → name
        if s.startswith('# '):
            flush_skills()
            out.append(Paragraph(_esc(s[2:].strip()), st['name']))
            in_contact = True
            i += 1
            continue

        # Contact block: accumulate lines, combine into one, until blank or ##
        if in_contact:
            if not s or s.startswith('##'):
                in_contact = False
                flush_contact()
                if not s:
                    i += 1
                continue
            # Split on " | " and collect individual items
            parts = [p.strip() for p in s.split('|') if p.strip()]
            contact_lines.extend(parts)
            i += 1
            continue

        # H2 → section heading + HR
        if s.startswith('## '):
            flush_skills()
            section = s[3:].strip().lower()
            edu_header_done = False  # reset for each new section
            out.append(Paragraph(_esc(s[3:].strip().upper()), st['sec']))
            out.append(HRFlowable(width='100%', thickness=0.5,
                                   color=colors.black, spaceAfter=2))
            i += 1
            continue

        # H3 → sub-heading (job title, project name)
        if s.startswith('### '):
            flush_skills()
            out.append(Paragraph(_esc(s[4:].strip()), st['sub']))
            i += 1
            continue

        # Bullet
        if s.startswith('- '):
            flush_skills()
            out.append(Paragraph('• ' + _md(s[2:].strip()), st['bullet']))
            i += 1
            continue

        # Blank line
        if not s:
            i += 1
            continue

        # Skills section: accumulate for box rendering
        if section == 'skills':
            skill_buf.append(s)
            i += 1
            continue

        # Education: first body line = institution name → bold + right date if present
        if section == 'education' and not edu_header_done:
            edu_header_done = True
            if rdate:
                out.append(_lr_row(s, rdate, st, bold=True))
            else:
                out.append(Paragraph(_esc(s), st['bold']))
            i += 1
            continue

        # Line with graduating date pre-attached → right-aligned row
        if rdate:
            out.append(_lr_row(s, rdate, st))
            i += 1
            continue

        # Affiliations: bold left text + right-aligned date
        if section == 'affiliations':
            m = _DATE_RE.search(s)
            if m:
                date_str = m.group(0)
                before = s[:m.start()].rstrip(' |:–-').strip()
                after = s[m.end():].strip().strip('|').strip()
                if not after and before:
                    out.append(_lr_row(before, date_str, st, bold=True))
                    i += 1
                    continue
            out.append(Paragraph(_md(s), st['bold']))
            i += 1
            continue

        # Lines ending with a date → right-aligned row
        m = _DATE_RE.search(s)
        if m:
            date_str = m.group(0)
            before = s[:m.start()].rstrip(' |:–-').strip()
            after = s[m.end():].strip().strip('|').strip()
            if not after and before:
                out.append(_lr_row(before, date_str, st))
                i += 1
                continue

        # Tech stack line (contains bullet separators • or ·)
        if '•' in s or '·' in s or '\u00b7' in s:
            out.append(Paragraph(_esc(s), st['tech']))
            i += 1
            continue

        # Default body
        out.append(Paragraph(_md(s), st['body']))
        i += 1

    flush_skills()
    return out


# ── Public API ───────────────────────────────────────────────────────────────

def generate_resume_pdf(resume_text, output_path):
    """Convert markdown resume text to an ATS-safe one-page PDF."""
    st = _st()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        output_path, pagesize=LETTER,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )
    doc.build(_parse(resume_text, st))
    return output_path


def generate_cover_letter_pdf(cover_letter_text, company, role, output_path):
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
        HRFlowable(width='100%', thickness=0.5, color=colors.black, spaceAfter=8),
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
    out_dir = Path(__file__).parent.parent / 'output'
    out_dir.mkdir(exist_ok=True)
    if not resume_path.exists():
        print(f'ERROR: {resume_path} not found')
        sys.exit(1)
    resume_text = resume_path.read_text()
    today = date.today().isoformat()
    out = out_dir / f'Sachin_Pandey_resume_{today}.pdf'
    result = generate_resume_pdf(resume_text, str(out))
    print(f'Generated: {result} ({os.path.getsize(result):,} bytes)')
