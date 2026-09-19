"""NayaNisab - AI curriculum intelligence for Pakistani universities.

Created by: Umar Shahzad
"""

from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from ai_workflow import MODEL_DEFAULT, flatten_text, run_workflow
from benchmarks import score_band
from nayanisab_pdf_style import build_curriculum_report
from nayanisab_theme import CSS, ORANGE, ORANGE_SOFT
from pdf_utils import extract_pdf_text

BASE_DIR = Path(__file__).parent
LOGO_PATH = BASE_DIR / "NayaNisab logo.jpg"
AUTHOR = "Umar Shahzad"

st.set_page_config(
    page_title="NayaNisab | Curriculum Intelligence",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)


# --------------------------------------------------------------- tolerant readers
# The AI workflow returns compact JSON where several lists hold plain strings,
# while older/richer payloads held dictionaries. These helpers render either
# shape instead of raising "'str' object has no attribute 'get'".

def _field(item, *keys, default=""):
    """Read a key from a dict item; return the default for anything else."""
    if isinstance(item, dict):
        for key in keys:
            value = item.get(key)
            if value not in (None, "", [], {}):
                return flatten_text(value) or default
    return default


def _label(item, *keys, default=""):
    """Headline text for an item that may be a plain string or a dict."""
    if isinstance(item, str):
        return flatten_text(item).strip() or default
    if isinstance(item, dict):
        return _field(item, *keys, default="") or flatten_text(item) or default
    return flatten_text(item) or default


def _sublist(item, key):
    """A list of strings from a dict item; empty for anything else."""
    value = item.get(key) if isinstance(item, dict) else None
    if not isinstance(value, list):
        return []
    return [text for text in (flatten_text(x) for x in value) if text]


# ------------------------------------------------------------------- UI helpers

def html(markup: str):
    """Render one line of component markup (blank lines break st.markdown)."""
    st.markdown(markup, unsafe_allow_html=True)


def word_reveal(text: str, start: float = 0.35, step: float = 0.045) -> str:
    """Animate a sentence in word by word, the way a model streams an answer."""
    words = []
    for i, word in enumerate(text.split()):
        words.append(f'<span class="w" style="animation-delay:{start + i * step:.2f}s">{escape(word)}</span>')
    return " ".join(words)


def meter(name: str, score: float, detail: str = "") -> str:
    """One animated benchmark bar."""
    cls = "m-low" if score < 50 else "m-mid" if score <= 80 else "m-high"
    tip = f'<div class="small" style="margin-top:6px">{escape(detail)}</div>' if detail else ""
    return (
        f'<div class="meter-row {cls}"><div class="meter-top"><b>{escape(name)}</b>'
        f'<span>{score:.0f}/100</span></div><div class="meter">'
        f'<i style="--w:{max(2, min(100, score)):.0f}%"></i></div>{tip}</div>'
    )


def priority_pill(priority: str) -> str:
    key = (priority or "").strip().lower()
    cls = "p-imm" if key == "immediate" else "p-opt" if key == "optional" else "p-man"
    return f'<span class="pill {cls}">{escape(priority or "Mandatory")}</span>'


def feature_card(number: int, title: str, body: str, lit: bool = False) -> str:
    return (
        f'<div class="card eq{" lit" if lit else ""} anim d{min(number, 6)}">'
        f'<div class="num">{number:02d}</div><h4>{escape(title)}</h4>'
        f'<div class="rule"></div><p>{escape(body)}</p></div>'
    )


def get_secret(name: str, default: str = ""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def render_band(score: float):
    b = score_band(score)
    cls = "b-low" if score < 50 else "b-mid" if score <= 80 else "b-high"
    html(
        f'<div class="band {cls}"><div class="bar"></div><div><b>{escape(b["label"])}</b> '
        f'<span style="color:#C9C9D6"> &mdash; {escape(b["headline"])}</span>'
        f'<div class="small" style="margin-top:3px">{escape(b["action"])}</div></div></div>'
    )


def render_footer():
    html(
        '<div class="foot"><div class="by">Created by: <b>' + escape(AUTHOR) + '</b>'
        '<div class="small" style="margin-top:2px">NayaNisab &middot; AI curriculum intelligence for Pakistan</div></div>'
        '<div class="note">The modernisation score is a decision-support heuristic produced by an AI workflow. '
        'It is not accreditation, and every proposal requires teacher review and institutional approval.</div></div>'
    )


# ----------------------------------------------------------------------- sidebar
with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    else:
        st.markdown("### NayaNisab")
    html('<div class="small" style="margin:10px 0 4px">AI-powered curriculum intelligence for Pakistani universities.</div>')
    st.markdown("---")
    html('<div style="font-weight:700;font-size:.82rem;letter-spacing:.14em;text-transform:uppercase;color:#8C8CA1;margin-bottom:8px">The pipeline</div>')
    for i, step in enumerate([
        "Reads the submitted curriculum",
        "Benchmarks it against modern practice",
        "Finds where the gap begins",
        "Recommends practical improvements",
        "Drafts a teacher-reviewable update",
    ], start=1):
        html(f'<div class="side-item"><i>0{i}</i><div>{escape(step)}</div></div>')
    st.markdown("---")
    html(f'<div class="small">Engine<br><span class="accent" style="font-family:var(--mono);font-size:.8rem">{escape(MODEL_DEFAULT)}</span></div>')
    html('<div class="small" style="margin-top:14px">Open-source models, free tier. Built for teachers, not for auditors.</div>')


# -------------------------------------------------------------------------- hero
html(
    '<div class="hero">'
    '<div class="hero-code">def modernise(curriculum):<br>&nbsp;&nbsp;gaps = benchmark(curriculum)<br>'
    '&nbsp;&nbsp;return proposal(gaps)</div>'
    '<div class="eyebrow">Curriculum Intelligence &bull; Pakistan</div>'
    '<h1>Naya<span class="grad">Nisab</span></h1>'
    f'<p class="hero-sub">{word_reveal("Bringing Pakistani curricula up to tomorrow’s standards.")}'
    '<span class="caret"></span></p></div>'
)

if "result" not in st.session_state:
    st.session_state.result = None


# ================================================================= INPUT SCREEN
if st.session_state.result is None:
    st.write("")
    c1, c2 = st.columns([1.25, 1], gap="large")
    with c1:
        html('<div class="anim d1" style="font-size:1.35rem;font-weight:750;margin-bottom:2px">Analyse a university curriculum</div>')
        html('<div class="small anim d2" style="margin-bottom:16px">Enter the university and subject, upload the curriculum and its learning objectives, and NayaNisab returns a scored benchmark, the gaps that matter, and a modernised draft.</div>')
        university = st.text_input("University name", placeholder="e.g., International Islamic University Islamabad")
        subject = st.text_input("Subject / programme", placeholder="e.g., Power Distribution and Utilization")
    with c2:
        html('<div class="small anim d2" style="margin-bottom:8px;font-weight:700;letter-spacing:.12em;text-transform:uppercase">Source documents</div>')
        curriculum_file = st.file_uploader("Official curriculum PDF", type=["pdf"], key="curriculum")
        objectives_file = st.file_uploader("Learning objectives PDF", type=["pdf"], key="objectives")

    st.write("")
    analyze = st.button("Analyse & Modernise Curriculum", type="primary", use_container_width=True)

    st.write("")
    html('<div class="anim d3" style="font-size:1.1rem;font-weight:750;margin:14px 0 12px">What NayaNisab returns</div>')
    cards = [
        ("Modernisation score", "A transparent 0-100 score across eleven weighted dimensions."),
        ("Gap starting point", "Where modernisation pressure first appears in the programme."),
        ("Priority actions", "Immediate, mandatory and optional steps, each one concrete."),
        ("Updated curriculum", "A teacher-reviewable proposal that keeps strong foundations."),
        ("Change log & PDF", "What changed and why, exported as a four-page report."),
    ]
    cols = st.columns(len(cards), gap="medium")
    for i, (col, (title, body)) in enumerate(zip(cols, cards), start=1):
        with col:
            html(feature_card(i, title, body, lit=(i == 1)))

    if analyze:
        if not university.strip():
            st.error("Enter the university name first.")
        elif not subject.strip():
            st.error("Enter the subject / programme first.")
        elif not curriculum_file or not objectives_file:
            st.error("Upload both PDFs before starting the analysis.")
        else:
            api_key = get_secret("GROQ_API_KEY")
            if not api_key:
                st.error("GROQ_API_KEY is missing. Add it in Streamlit Cloud -> Settings -> Secrets.")
            else:
                stage = st.empty()
                progress = st.progress(0, text="Preparing your documents...")
                try:
                    with st.spinner("Reading the uploaded PDFs..."):
                        curriculum_text, c_pages, _ = extract_pdf_text(curriculum_file)
                        objectives_text, o_pages, _ = extract_pdf_text(objectives_file)

                    def report(p, msg):
                        stage.markdown(
                            f'<div class="card" style="padding:15px 18px"><div style="font-weight:700">{escape(msg)}</div>'
                            f'<div class="scan"><i></i></div>'
                            f'<div class="small" style="font-family:var(--mono)">stage {p:03d}%</div></div>',
                            unsafe_allow_html=True,
                        )
                        progress.progress(p, text=msg)

                    result = run_workflow(
                        api_key,
                        university.strip(),
                        subject.strip(),
                        curriculum_text,
                        objectives_text,
                        progress=report,
                    )
                    st.session_state.result = result
                    st.session_state.pdf_report = None
                    st.session_state.pdf_report_error = None
                    stage.empty()
                    progress.empty()
                    st.rerun()
                except Exception as exc:
                    stage.empty()
                    progress.empty()
                    st.error(f"Analysis failed: {exc}")
                    st.caption("Please check that both PDFs contain selectable text and try again.")

    render_footer()


# ================================================================ RESULT SCREEN
else:
    result = st.session_state.result
    score = float(result["score"])
    dims = result["benchmark"]["dimension_scores"]
    band = score_band(score)

    html(
        f'<div class="anim d1" style="display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:10px;margin-bottom:14px">'
        f'<div><div style="font-size:1.5rem;font-weight:750">{escape(result["university"])}</div>'
        f'<div class="small">{escape(result["subject"])} &middot; analysed {datetime.now().strftime("%d %b %Y, %H:%M")}</div></div>'
        f'<div class="chip">Engine: {escape(MODEL_DEFAULT)}</div></div>'
    )

    high = sum(1 for d in dims if d["score"] < 50)
    mid = sum(1 for d in dims if 50 <= d["score"] <= 80)
    strong = sum(1 for d in dims if d["score"] > 80)

    k1, k2, k3 = st.columns([1.15, 1, 1], gap="medium")
    with k1:
        html(
            f'<div class="card anim d1"><div class="ring-wrap">'
            f'<div class="ring" style="--target:{min(360, max(0, score * 3.6)):.0f}deg"><b>{score:.0f}</b></div>'
            f'<div><div class="ring-label">Modernisation score</div>'
            f'<div class="ring-big">{escape(band["label"].title())}</div>'
            f'<div class="small">out of 100, weighted across {len(dims)} dimensions</div></div></div></div>'
        )
    with k2:
        html(
            f'<div class="card anim d2"><div class="ring-label">Domain breakdown</div>'
            f'<div style="display:flex;gap:18px;margin-top:12px">'
            f'<div><div style="font-size:1.9rem;font-weight:800;color:var(--red)">{high}</div><div class="small">high gap</div></div>'
            f'<div><div style="font-size:1.9rem;font-weight:800;color:var(--amber)">{mid}</div><div class="small">to improve</div></div>'
            f'<div><div style="font-size:1.9rem;font-weight:800;color:var(--green)">{strong}</div><div class="small">strong</div></div>'
            f'</div></div>'
        )
    with k3:
        html(
            '<div class="card anim d3"><div class="ring-label">Teacher decision</div>'
            '<p style="margin-top:10px">Review the proposed changes, then seek institutional approval before formal '
            'curriculum adoption. Nothing here is auto-approved.</p></div>'
        )

    st.write("")
    render_band(score)
    st.write("")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Dashboard", "Gap map", "Recommendations", "Updated draft", "Evidence"]
    )

    # ---------------------------------------------------------------- dashboard
    with tab1:
        left, right = st.columns([1.15, 1], gap="large")
        with left:
            html('<div style="font-weight:700;margin:6px 0 10px">Benchmark alignment</div>')
            for d in sorted(dims, key=lambda x: x["score"]):
                html(meter(d["name"], float(d["score"])))
        with right:
            frame = pd.DataFrame(dims)
            fig = px.bar(
                frame.sort_values("score"),
                x="score", y="name", orientation="h",
                range_x=[0, 100], color="score",
                color_continuous_scale=[(0, "#FF5A4E"), (0.5, ORANGE), (1, "#37D89A")],
            )
            fig.update_layout(
                height=520, margin=dict(l=10, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#B9B9CB", family="Plus Jakarta Sans"),
                xaxis_title="Alignment score", yaxis_title="",
                coloraxis_showscale=False,
                xaxis=dict(gridcolor="rgba(255,255,255,.07)", zerolinecolor="rgba(255,255,255,.12)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0)"),
            )
            fig.update_traces(marker_line_width=0, hovertemplate="%{y}: %{x:.0f}/100<extra></extra>")
            st.plotly_chart(fig, use_container_width=True)

        note = _label(result["benchmark"].get("benchmark_note"))
        if note:
            html(f'<div class="block anim"><p>{escape(note)}</p></div>')

    # ------------------------------------------------------------------ gap map
    with tab2:
        html('<div style="font-weight:700;margin:6px 0 10px">Where does the gap begin?</div>')
        first_point = _label(
            result["benchmark"].get("first_gap_point"),
            default="The analysis could not confidently identify a first gap point.",
        )
        html(f'<div class="card lit anim d1" style="margin-bottom:16px"><div class="num">!</div><h4>First meaningful gap</h4><div class="rule"></div><p>{escape(first_point)}</p></div>')

        gaps = result["benchmark"].get("top_global_gaps", [])
        if gaps:
            html('<div style="font-weight:700;margin:18px 0 10px">Top benchmark gaps</div>')
            gap_cols = st.columns(2, gap="medium")
            for i, gap in enumerate(gaps[:4]):
                reason = _field(gap, "reason")
                courses = _sublist(gap, "affected_courses")
                extra = f'<div style="margin-top:9px">{"".join(f"<span class=chip>{escape(c)}</span>" for c in courses[:4])}</div>' if courses else ""
                with gap_cols[i % 2]:
                    html(
                        f'<div class="card anim d{min(i + 1, 6)}" style="margin-bottom:12px"><div class="num">{i + 1:02d}</div>'
                        f'<h4>{escape(_label(gap, "title", default="Gap"))}</h4><div class="rule"></div>'
                        f'<p>{escape(reason) if reason else "Flagged as a priority gap by the benchmark comparison."}</p>{extra}</div>'
                    )

        critical = result.get("gaps", {}).get("critical_gaps", [])
        if critical:
            html('<div style="font-weight:700;margin:22px 0 10px">Priority gaps</div>')
            for i, gap in enumerate(critical[:5]):
                html(f'<div class="block" style="animation-delay:{i * .06:.2f}s"><h5>{escape(_label(gap, "title", default="Gap"))}</h5>'
                     f'<p>{escape(_field(gap, "recommended_change", "desired_state", "action"))}</p></div>')

        html('<div style="font-weight:700;margin:22px 0 10px">Domain-by-domain diagnosis</div>')
        for d in sorted(dims, key=lambda x: x["score"]):
            with st.expander(f"{d['name']}  ·  {d['score']:.0f}/100  ·  {d['status']}"):
                html(meter(d["name"], float(d["score"])))
                html(f'<p class="small"><b style="color:#D3D3DE">Evidence found:</b> {escape(str(d["evidence"]))}</p>')
                html(f'<p class="small"><b style="color:#D3D3DE">Missing / weak:</b> {escape(str(d["missing"]))}</p>')
                html(f'<div style="margin-top:8px">{priority_pill(str(d["priority"]))}</div>')

        teacher_message = _label(result.get("gaps", {}).get("teacher_message"))
        if teacher_message:
            html('<div style="font-weight:700;margin:22px 0 10px">Teacher-facing explanation</div>')
            html(f'<div class="card anim"><p style="color:#D3D3DE;font-size:.95rem;line-height:1.7">{escape(teacher_message)}</p></div>')

    # ---------------------------------------------------------- recommendations
    with tab3:
        recs = result.get("recommendations", {}).get("recommendations", [])
        if not recs:
            st.info("No recommendations were returned.")
        else:
            html('<div style="font-weight:700;margin:6px 0 12px">Priority actions</div>')
            order = {"immediate": 0, "mandatory": 1, "optional": 2}
            recs = sorted(recs, key=lambda r: order.get(_field(r, "priority", default="Mandatory").lower(), 1))
            for i, rec in enumerate(recs):
                priority = _field(rec, "priority", default="Mandatory")
                title = _label(rec, "title", "change", default="Curriculum change")
                detail = _field(rec, "action", "implementation") or _field(rec, "reason") or "Apply at programme level during the next review."
                where = _field(rec, "where_to_apply")
                where_html = f'<div class="small" style="margin-top:8px"><b style="color:#D3D3DE">Where:</b> {escape(where)}</div>' if where else ""
                html(
                    f'<div class="card anim" style="margin-bottom:12px;animation-delay:{i * .07:.2f}s">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:9px">'
                    f'<h4 style="margin:0">{escape(title)}</h4>{priority_pill(priority)}</div>'
                    f'<p>{escape(detail)}</p>{where_html}</div>'
                )

        updates = result.get("recommendations", {}).get("proposed_course_updates", [])
        if updates:
            html('<div style="font-weight:700;margin:24px 0 12px">Proposed course updates</div>')
            for i, update in enumerate(updates):
                body = _field(update, "updated_focus", "current_focus")
                topics = _sublist(update, "new_topics")
                chips = "".join(f'<span class="chip">{escape(t)}</span>' for t in topics[:6])
                html(
                    f'<div class="block" style="animation-delay:{i * .06:.2f}s">'
                    f'<h5>{escape(_label(update, "course", default="Course area"))}</h5>'
                    + (f'<p>{escape(body)}</p>' if body else "")
                    + (f'<div style="margin-top:9px">{chips}</div>' if chips else "")
                    + '</div>'
                )

    # ----------------------------------------------------------- updated draft
    with tab4:
        draft = result.get("draft", {})
        html(f'<div style="font-weight:750;font-size:1.2rem;margin:6px 0 4px">{escape(_label(draft.get("title"), default="Proposed modernised curriculum"))}</div>')
        summary = _label(draft.get("executive_summary"))
        if summary:
            html(f'<div class="card anim d1" style="margin-bottom:16px"><p style="color:#D3D3DE;font-size:.95rem;line-height:1.7">{escape(summary)}</p></div>')

        principles = draft.get("principles", [])
        if principles:
            html('<div style="font-weight:700;margin:16px 0 9px">Design principles</div>')
            html("".join(f'<span class="chip">{escape(_label(p))}</span>' for p in principles))

        revised = [r for r in draft.get("revised_curriculum", []) if isinstance(r, dict)]
        if revised:
            html('<div style="font-weight:700;margin:22px 0 9px">Revised curriculum</div>')
            table = pd.DataFrame(revised)
            cols = [c for c in ["course_or_area", "status", "updated_scope", "practical_work", "assessment"] if c in table.columns]
            table = table[cols].rename(columns={
                "course_or_area": "Course / area", "status": "Status", "updated_scope": "Updated scope",
                "practical_work": "Practical work", "assessment": "Assessment",
            })
            st.dataframe(table, use_container_width=True, hide_index=True)

        changes = draft.get("change_log", [])
        if changes:
            html('<div style="font-weight:700;margin:22px 0 12px">Change log</div>')
            items = []
            for i, change in enumerate(changes):
                old, new = _field(change, "old_state"), _field(change, "new_state")
                reason = _field(change, "reason")
                line = f'<span class="from-to">{escape(old)} &rarr; {escape(new)}</span>' if (old or new) else ""
                why = f'<p style="margin-top:5px">{escape(reason)}</p>' if reason else ""
                items.append(
                    f'<div class="tl-item" style="animation-delay:{i * .07:.2f}s">'
                    f'<b>{escape(_label(change, "change", default="Change"))}</b>{line}{why}</div>'
                )
            html('<div class="timeline">' + "".join(items) + '</div>')

        points = draft.get("teacher_review_points", [])
        if points:
            html('<div style="font-weight:700;margin:20px 0 10px">Teacher review points</div>')
            for i, point in enumerate(points):
                html(f'<div class="block" style="animation-delay:{i * .06:.2f}s"><p>{escape(_label(point))}</p></div>')

        html(f'<div class="card" style="margin-top:20px;border-color:rgba(255,176,32,.35)"><p style="color:#FFB020">{escape(_label(draft.get("disclaimer"), default="AI-generated proposal requiring academic review and institutional approval."))}</p></div>')

    # ---------------------------------------------------------------- evidence
    with tab5:
        structure = result.get("structure", {})
        summary = _label(structure.get("program_summary"))
        if summary:
            html(f'<div class="card anim d1" style="margin-bottom:16px"><p>{escape(summary)}</p></div>')

        e1, e2 = st.columns(2, gap="large")
        with e1:
            html('<div style="font-weight:700;margin:6px 0 10px">Course inventory</div>')
            inventory = structure.get("course_inventory", [])
            if inventory:
                for course in inventory[:25]:
                    level = _field(course, "level_or_semester")
                    html(f'<div class="block" style="padding:10px 14px;margin-bottom:8px"><h5 style="margin:0">{escape(_label(course, "course", default="Unknown"))}'
                         + (f' <span class="small">&middot; {escape(level)}</span>' if level else "") + '</h5></div>')
            else:
                html('<div class="small">No course inventory was extracted.</div>')
        with e2:
            html('<div style="font-weight:700;margin:6px 0 10px">Tools / technologies detected</div>')
            tools = structure.get("tools_and_technologies", [])
            html("".join(f'<span class="chip">{escape(_label(t))}</span>' for t in tools[:40])
                 if tools else '<div class="small">No explicit technologies detected.</div>')

            outcomes = structure.get("learning_outcomes", [])
            if outcomes:
                html('<div style="font-weight:700;margin:22px 0 10px">Learning outcomes read</div>')
                for outcome in outcomes[:10]:
                    html(f'<div class="block" style="padding:10px 14px;margin-bottom:8px"><p>{escape(_label(outcome))}</p></div>')

    # ------------------------------------------------------------------ export
    st.write("")
    st.markdown("---")
    download_col, new_col = st.columns([2, 1], gap="medium")
    with download_col:
        if st.session_state.get("pdf_report") is None:
            try:
                st.session_state.pdf_report = build_curriculum_report(result, LOGO_PATH)
            except Exception as exc:
                st.session_state.pdf_report_error = str(exc)
        if st.session_state.get("pdf_report"):
            st.download_button(
                "Download the NayaNisab report (4-page PDF)",
                data=st.session_state.pdf_report,
                file_name=f"NayaNisab_{result['subject'].replace(' ', '_')}_Curriculum_Report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            html('<div class="small" style="margin-top:6px">Standard NayaNisab report format, designed for teacher review and institutional discussion.</div>')
        elif st.session_state.get("pdf_report_error"):
            st.error(f"Could not prepare the PDF report: {st.session_state.pdf_report_error}")
    with new_col:
        if st.button("Start a new analysis", use_container_width=True):
            st.session_state.result = None
            st.session_state.pdf_report = None
            st.session_state.pdf_report_error = None
            st.rerun()

    render_footer()
