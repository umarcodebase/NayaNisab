# NayaNisab — Curriculum Intelligence MVP

**Tagline:** Bringing Pakistani curricula up to tomorrow's standards.

NayaNisab is a Streamlit MVP for university teachers across Pakistan. The teacher enters the **university name** and **programme/subject**, then uploads an official curriculum PDF plus learning objectives PDF. NayaNisab compares the material against a transparent, **subject-specific** modern global benchmark, locates the first meaningful gap, generates priority recommendations, and produces a teacher-reviewable modernised curriculum draft.

The first hackathon demonstration can use Computer Science, but the interface is **not locked to Computer Science**. A teacher can enter subjects such as Computer Science, Mechanical Engineering, Business Administration, Electrical Engineering, Medicine, Economics, etc. The AI adapts the benchmark interpretation to the selected subject.

## 1. Project structure

```text
NayaNisab/
├── app.py
├── ai_workflow.py
├── benchmarks.py
├── pdf_utils.py
├── scoring.py
├── requirements.txt
├── NayaNisab logo.jpg
├── .gitignore
└── README.md
```

## 2. Streamlit Cloud setup

Deploy the repository to Streamlit Community Cloud and add this secret under **Settings → Secrets**:

```toml
GROQ_API_KEY = "PASTE_YOUR_GROQ_API_KEY_HERE"
```

No key belongs in GitHub. The app reads `GROQ_API_KEY` from `st.secrets`.

## 3. AI model

The MVP uses:

```text
openai/gpt-oss-120b
```

The model is an open-weight model released under Apache 2.0 and available through Groq. It is used for the five sequential workflow stages.

## 4. Agent workflow

1. **Extract** — turns uploaded PDFs into a structured curriculum representation.
2. **Benchmark** — scores the selected subject against a transparent, subject-agnostic benchmark framework interpreted for the teacher's chosen subject.
3. **Diagnose** — identifies the first meaningful gap and the most important missing areas.
4. **Recommend** — proposes realistic course/module/lab/project/assessment improvements.
5. **Draft** — creates a revised curriculum draft for teacher review.

## 5. Subject flexibility

The app deliberately asks the teacher to enter:

- **University name**
- **Programme / subject**
- **Official curriculum PDF**
- **Learning objectives PDF**

The benchmark framework is not hard-coded to Computer Science. Instead, the AI interprets each broad benchmark dimension according to the selected discipline.

## 6. Score interpretation

This is a prototype decision-support score, not an accreditation score:

- **0–49:** High Warning — immediate modernisation priority
- **50–80:** Improvement Required — mandatory improvement areas
- **81–100:** Future-Ready — optional enhancement areas

## 7. PDF limitation for the hackathon

The MVP expects text-based PDFs. Scanned image-only PDFs are not OCR'ed in this first version. Keep the demo documents reasonably focused so the workflow is fast and reliable.
