# resume-tailor

## What this does
I paste a job URL. You fetch the description, tailor my resume,
write a cover letter, generate PDFs of both, and draft recruiter
outreach. That is the entire workflow.

## My resume
Source of truth: context/resume.md
Read it every session before doing anything.

## MCP servers
- scraper_server.py  → fetch_job(url)
- outreach_server.py → find_recruiter(), draft_outreach()
- pdf_server.py      → generate_resume_pdf(company, role, tailored_json_path)

## PDF generation
Call the generate_resume_pdf() MCP tool from servers/pdf_server.py.

---

## FULL WORKFLOW — runs automatically when I paste a URL

### Step 1 — Fetch the job
Call fetch_job(url)
If it fails → ask me to paste the job description text
Extract: company, title, location, required skills, preferred
skills, tech stack, any keywords they repeat

### Step 2 — Score fit
Read context/resume.md
Score 1–10:
  - Count skill matches vs requirements
  - Assess how well my projects map to their needs
  - Be honest about gaps

  8–10 → continue automatically
  6–7  → continue, note gaps clearly
  4–5  → show score, ask me before continuing
  < 4  → tell me it's a weak fit and why, ask to override

Show score + 2 sentence reason before moving on.

### Step 3 — Keyword extraction
Before writing anything, list:
  a) Every tech keyword from the job description
  b) Which ones I have: [have] [somewhat] [gap]
  c) Their exact phrases I will mirror in bullets
This becomes the foundation for Step 4.

### Step 4 — Tailor the resume
Rewrite context/resume.md for this specific job and write the result to:
  output/json/[Company]_[Role]_tailored.json

Use this schema:
  {
    "skills":     { "Category": "skill1, skill2, ..." },
    "projects":   [{ "name": "...", "stack": "...", "bullets": ["..."] }],
    "experience": [{ "title": "...", "company": "...", "dates": "...", "bullets": ["..."] }]
  }

The user can edit this file to tweak bullets or reorder skills before Step 6.
The output/json/ directory is created automatically if it doesn't exist.

BULLETS — every bullet must:
  - Start with a strong past-tense action verb
  - Mirror the job's exact keywords naturally
  - Include a metric or outcome where one exists
  - Be a specific accomplishment, not a duty
  - Be 100% true — reframe only, never fabricate

SKILLS — reorder so their stack appears first

PROJECTS — include exactly 2 most relevant projects for this job.
  Do NOT include more — this keeps the PDF at a readable size.

EDUCATION — keep as-is, add relevant coursework only if
  it directly maps to a requirement

Do NOT use:
  Generic verbs like "helped", "worked on", "assisted"
  Vague claims like "improved performance significantly"
  Fabricated tools or skills I don't have

### Step 5 — Write cover letter
3 paragraphs, under 250 words.

Para 1: Who I am + why this specific company/role
  (reference their actual product or problem they solve)
Para 2: My strongest relevant experience with specifics
Para 3: Short confident close, soft CTA

NEVER use:
  "I am writing to express my interest"
  "I am passionate about"
  "team player" / "fast learner" / "hard worker"
  "I believe I would be a great fit"
  "Thank you for your consideration"

### Step 6 — Generate PDFs
Call generate_resume_pdf(company, role, tailored_json_path)
from the pdf_server MCP tool.

tailored_json_path is the absolute path to the file written in Step 4 (output/json/...).
The tool returns the PDF path — print it.

Cover letter:
Call generate_coverletter_pdf(company, role, cover_letter_text)
from the pdf_server MCP tool.
Pass the full cover letter body as cover_letter_text (paragraphs separated by double newlines).
The tool returns the PDF path — print it.
Do NOT save a .txt file — the MCP tool is the only step needed.

Print both PDF paths when done.

### Step 7 — Recruiter outreach
Call find_recruiter(company, role)
Print the 3 LinkedIn search URLs.

Call draft_outreach(
  recruiter_name = "[Name]",
  company = company,
  role = title,
  my_background = "CS student at Texas State University,
  3.96 GPA, graduating May 2027. Built full-stack apps with
  React, Node.js, Django, PostgreSQL. Built a RAG AI assistant
  using FastAPI and Qdrant. Research Assistant doing Python
  data analysis."
)
Print the full email.

Ask: "Send this via Gmail or save to file?"
  Send → use Gmail MCP to create a draft
  Save → save to output/[Company]_outreach_[Date].txt

### Final output summary
Print exactly this when workflow is complete:

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DONE — [Job Title] @ [Company]
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Fit score:    X/10
  Resume PDF:   output/pdf/[filename].pdf
  Cover letter: output/pdf/[filename].pdf

  To apply:
  1. Open [url] in Chrome
  2. Simplify auto-fills the form
  3. Upload resume PDF from output/pdf/
  4. Paste cover letter for free-text fields
  5. Submit
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

---

## Hard rules
- Never fabricate skills or experience
- Never use banned cover letter phrases
- Always run PDF generation — the PDF is the deliverable
- Commit after each build step
