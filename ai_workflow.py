import json
import re
from typing import Callable, Optional

from groq import Groq

from benchmarks import BENCHMARKS
from scoring import calculate_overall_score, normalise_dimension_scores

# Open-weight, Apache 2.0 model. Smaller than 120B and much easier to run on the free
# Groq tier once the workflow keeps each request compact.
MODEL_DEFAULT = "openai/gpt-oss-20b"

# Groq's free/on-demand limit shown in the user's error is 8,000 TPM.
# Keep request sizes comfortably below that ceiling.
MAX_SOURCE_CHARS = 18_000
MAX_CONTEXT_ITEMS = 10


def _clean_json(text: str) -> dict:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            value = json.loads(text[start:end + 1])
        else:
            raise
    if isinstance(value, dict):
        return value
    # Prevent downstream .get() errors if the model returns an unexpected JSON type.
    return {"value": value}


def _compact(value, max_chars: int = 12_000):
    """Compact nested model output so later workflow stages do not resend huge prompts."""
    if isinstance(value, dict):
        compact = {}
        for key, item in value.items():
            if isinstance(item, list):
                compact[key] = item[:MAX_CONTEXT_ITEMS]
            else:
                compact[key] = item
        value = compact
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if len(text) <= max_chars:
        return value
    return {
        "truncated_context": text[:max_chars],
        "note": "Some low-priority context was shortened to keep the analysis within API limits."
    }


def _trim_source(text: str, limit: int = MAX_SOURCE_CHARS) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    head = int(limit * 0.72)
    tail = limit - head
    return (
        text[:head]
        + "\n\n[...middle of source shortened for API limits... ]\n\n"
        + text[-tail:]
    )


def _chat(client: Groq, messages: list[dict], *, max_tokens: int = 2200, temperature: float = 0.1) -> str:
    response = client.chat.completions.create(
        model=MODEL_DEFAULT,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def run_workflow(
    api_key: str,
    university: str,
    subject: str,
    curriculum_text: str,
    learning_objectives_text: str,
    progress: Optional[Callable[[int, str], None]] = None,
) -> dict:
    client = Groq(api_key=api_key)

    def update(p, msg):
        if progress:
            progress(p, msg)

    # Keep the first request deliberately small. This is the main fix for the 8K TPM error.
    curriculum_input = _trim_source(curriculum_text, 12_000)
    objectives_input = _trim_source(learning_objectives_text, 6_000)

    # STAGE 1 — understand the supplied curriculum
    update(10, "Reading and structuring the submitted curriculum")
    structure_prompt = f"""
You are NayaNisab's curriculum analyst.
University: {university}
Subject: {subject}

Extract only the information needed for later gap analysis. Do not judge the curriculum yet.
Return JSON with:
{{
  "program_summary":"...",
  "course_inventory":[{{"course":"...","level_or_semester":"...","topics":["..."],"practical_component":"..."}}],
  "learning_outcomes":["..."],
  "tools_and_technologies":["..."],
  "assessment_or_project_signals":["..."],
  "explicit_emerging_topics":["..."],
  "obvious_age_or_version_markers":["..."]
}}

CURRICULUM:
{curriculum_input}

LEARNING OBJECTIVES:
{objectives_input}
"""
    structure = _clean_json(_chat(
        client,
        [{"role": "system", "content": "Return valid JSON only."}, {"role": "user", "content": structure_prompt}],
        max_tokens=1900,
    ))
    structure_context = _compact(structure, 10_000)

    # STAGE 2 — benchmark comparison
    update(28, "Comparing the curriculum with modern global benchmarks")
    benchmark_text = "\n".join(
        f"- {b['id']}: {b['name']} — {b['signals']}" for b in BENCHMARKS
    )
    comparison_prompt = f"""
You are NayaNisab's benchmarking specialist for the subject: {subject}.
Assess alignment with current global knowledge, skills, practices and future-facing expectations.
Do not rank the university. Use present/partial/missing evidence and avoid treating any single vendor tool as mandatory.

BENCHMARK DIMENSIONS:
{benchmark_text}

STRUCTURED CURRICULUM:
{json.dumps(structure_context, ensure_ascii=False, separators=(",", ":"))}

Return JSON:
{{
  "dimension_scores":[{{"id":"...","score":0,"evidence":"...","missing":"...","priority":"High|Medium|Low"}}],
  "top_global_gaps":[{{"title":"...","reason":"...","affected_courses":["..."]}}],
  "first_gap_point":"...",
  "benchmark_note":"..."
}}
"""
    comparison = _clean_json(_chat(
        client,
        [{"role": "system", "content": "Return valid JSON only."}, {"role": "user", "content": comparison_prompt}],
        max_tokens=2200,
    ))
    dims = normalise_dimension_scores(comparison.get("dimension_scores", []))
    overall = calculate_overall_score(dims)
    comparison_context = _compact(comparison, 10_000)

    # STAGE 3 — diagnose the most important gaps
    update(48, "Finding the most important gaps and where they begin")
    gap_prompt = f"""
You are NayaNisab's diagnostic analyst.
University: {university}
Subject: {subject}
Overall modernisation score: {overall}/100

Return JSON:
{{
  "first_gap":{{"course_or_stage":"...","what_is_missing":"...","why_it_matters":"..."}},
  "critical_gaps":[{{"title":"...","severity":"Critical|High|Medium","current_state":"...","desired_state":"...","why_now":"...","evidence":"...","recommended_change":"..."}}],
  "quick_wins":["..."],
  "keep_as_is":["..."],
  "teacher_message":"..."
}}

STRUCTURE:
{json.dumps(structure_context, ensure_ascii=False, separators=(",", ":"))}

BENCHMARK:
{json.dumps(comparison_context, ensure_ascii=False, separators=(",", ":"))}
"""
    gaps = _clean_json(_chat(
        client,
        [{"role": "system", "content": "Return valid JSON only."}, {"role": "user", "content": gap_prompt}],
        max_tokens=2000,
    ))
    gaps_context = _compact(gaps, 9_000)

    # STAGE 4 — recommendations
    update(66, "Designing practical curriculum improvements")
    rec_prompt = f"""
You are NayaNisab's academic curriculum modernisation specialist.
Create realistic changes for a Pakistani university. Prefer updating course content, labs, projects, prerequisites, assessments and electives rather than adding many new courses.

Return JSON:
{{
  "recommendations":[{{"priority":"Immediate|Mandatory|Optional","change":"...","where_to_apply":"...","reason":"...","implementation":"..."}}],
  "proposed_course_updates":[{{"course":"...","current_focus":"...","updated_focus":"...","new_topics":["..."],"practical_component":"...","assessment_update":"..."}}],
  "new_or_strengthened_components":[{{"name":"...","type":"course|module|lab|project|elective","reason":"...","suggested_position":"..."}}]
}}

STRUCTURE:
{json.dumps(structure_context, ensure_ascii=False, separators=(",", ":"))}

GAPS:
{json.dumps(gaps_context, ensure_ascii=False, separators=(",", ":"))}
"""
    recommendations = _clean_json(_chat(
        client,
        [{"role": "system", "content": "Return valid JSON only."}, {"role": "user", "content": rec_prompt}],
        max_tokens=2200,
    ))
    recommendations_context = _compact(recommendations, 9_000)

    # STAGE 5 — concise teacher-reviewable revised curriculum
    update(84, "Preparing the proposed modernised curriculum")
    rewrite_prompt = f"""
You are NayaNisab's curriculum drafting specialist.
Create a concise teacher-reviewable modernised curriculum draft for {university}'s {subject} programme.
Preserve strong content. Do not claim official approval.

Return JSON:
{{
  "title":"Proposed Modernised Curriculum Draft",
  "executive_summary":"...",
  "principles":["..."],
  "revised_curriculum":[{{"course_or_area":"...","status":"Keep|Update|Strengthen|Add","updated_scope":"...","key_topics":["..."],"practical_work":"...","assessment":"..."}}],
  "change_log":[{{"change":"...","old_state":"...","new_state":"...","reason":"..."}}],
  "teacher_review_points":["..."],
  "disclaimer":"AI-generated proposal requiring academic review and institutional approval."
}}

STRUCTURE:
{json.dumps(structure_context, ensure_ascii=False, separators=(",", ":"))}

BENCHMARK:
{json.dumps(comparison_context, ensure_ascii=False, separators=(",", ":"))}

GAPS:
{json.dumps(gaps_context, ensure_ascii=False, separators=(",", ":"))}

RECOMMENDATIONS:
{json.dumps(recommendations_context, ensure_ascii=False, separators=(",", ":"))}
"""
    draft = _clean_json(_chat(
        client,
        [{"role": "system", "content": "Return valid JSON only."}, {"role": "user", "content": rewrite_prompt}],
        max_tokens=2600,
    ))
    update(100, "Analysis complete")

    return {
        "university": university,
        "subject": subject,
        "score": overall,
        "band": "HIGH WARNING" if overall < 50 else "IMPROVEMENT REQUIRED" if overall <= 80 else "FUTURE-READY",
        "structure": structure,
        "benchmark": {
            "dimension_scores": dims,
            "top_global_gaps": comparison.get("top_global_gaps", []),
            "first_gap_point": comparison.get("first_gap_point", ""),
            "benchmark_note": comparison.get("benchmark_note", ""),
        },
        "gaps": gaps,
        "recommendations": recommendations,
        "draft": draft,
    }
