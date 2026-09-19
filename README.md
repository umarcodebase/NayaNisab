# NayaNisab

**Bringing Pakistani curricula up to tomorrow's standards.**

NayaNisab is a Streamlit-based curriculum intelligence prototype for Pakistani universities. A teacher enters the university and subject, then uploads the official curriculum and learning objectives. The application analyses the documents, compares the content with a subject-aware modern benchmark, identifies the most important gaps and where they begin, recommends practical improvements, and generates a teacher-reviewable modernised curriculum draft.

## User-facing flow

1. Enter the university name.
2. Enter any subject or programme.
3. Upload the official curriculum PDF.
4. Upload the learning objectives PDF.
5. Select **Analyse & Modernise Curriculum**.
6. Review the dashboard, gap map, recommendations and proposed updated curriculum.
7. Download the standard **4-page NayaNisab PDF report**.

## Standard PDF design

`nayanisab_pdf_style.py` is the single source of truth for the PDF design. All subjects use the same NayaNisab branding, page structure, colours, typography, logo placement and four-page output format. Only the analysis content changes.

The four pages cover:

- Page 1: executive overview and modernisation score
- Page 2: where the curriculum gap begins and priority gaps
- Page 3: recommended improvements and course updates
- Page 4: proposed modernised curriculum and change log

The generated PDF is designed for teacher review. It is not presented as formal accreditation or automatic academic approval.

## Project files

- `app.py` - Streamlit interface
- `nayanisab_theme.py` - dark / amber design system (CSS, animations, components)
- `.streamlit/config.toml` - Streamlit theme so native widgets match the design system
- `ai_workflow.py` - staged AI analysis workflow
- `benchmarks.py` - subject-aware benchmark framework
- `scoring.py` - transparent score logic
- `pdf_utils.py` - PDF text extraction
- `nayanisab_pdf_style.py` - standard four-page PDF report design
- `requirements.txt` - Streamlit Cloud dependencies
- `NayaNisab logo.jpg` - brand logo

## Streamlit secret

In Streamlit Cloud -> App settings -> Secrets:

```toml
GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"
```

Do not commit the API key to GitHub.

## Interface

The interface uses a dark, amber-accented design system defined in `nayanisab_theme.py`:
staged entrance animations, an animated score ring, animated benchmark meters, priority
pills and a live "scanning" indicator while the workflow runs. All motion is pure CSS and
respects `prefers-reduced-motion`, so nothing depends on JavaScript that Streamlit would strip.

## Engine

The analysis runs on the free, open-source `openai/gpt-oss-20b` model through the Groq API,
in four schema-bound stages (structure, benchmark, plan, draft). Every stage is validated and
repaired before rendering, so a malformed model response degrades one field instead of failing
the whole analysis.

## Credits

Created by **Umar Shahzad**, built with my team during the PakAngels hackathon under the
Generative & Agentic AI course.
