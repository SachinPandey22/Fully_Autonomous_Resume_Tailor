# resume-tailor

A focused tool that takes a job URL, tailors your resume, generates ATS-safe PDFs, and drafts recruiter outreach — all in one automated workflow driven by Claude Code.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

## Usage

Paste a job URL into Claude Code. The full 7-step workflow runs automatically:
1. Fetch job description
2. Score fit (1–10)
3. Extract keywords
4. Tailor resume
5. Write cover letter
6. Generate PDFs
7. Draft recruiter outreach

## Output

All generated files land in `output/`:
- `[Company]_[Role]_resume_[YYYY-MM-DD].pdf`
- `[Company]_[Role]_coverletter_[YYYY-MM-DD].pdf`
- `[Company]_outreach_[Date].txt` (optional)
