import json
import re
from typing import Callable, Optional

from groq import Groq

from benchmarks import BENCHMARKS
from scoring import calculate_overall_score, normalise_dimension_scores

MODEL_DEFAULT = "openai/gpt-oss-120b"


def _clean_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise


def _chat(client: Groq, messages: list[dict], *, max_tokens: int = 6500, temperature: float = 0.15) -> str:
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

    # STAGE 1 — curriculum intelligence / parsing
    update(10, "Reading and structuring the submitted curriculum")
    structure_prompt = f"""
You are NayaNisab Agent 1, a curriculum analyst. The product is helping a Pakistani university modernise a {subject} curriculum.

University: {university}
Subject: {subject}

Your job is to turn the uploaded curriculum and learning objectives into a reliable structured representation. Do not judge it yet.

Return JSON with:
{{
  "program_summary": "...",
  "course_inventory": [{{"course": "...", "level_or_semester": "...", "topics": ["..."], "practical_component": "..."}}],
  "learning_outcomes": ["..."],
  "tools_and_technologies": ["..."],
  "assessment_or_project_signals": ["..."],
  "explicit_emerging_topics": ["..."],
  "obvious_age_or_version_markers": ["..."],
  "uncertainties": ["..."]
}}

CURRICULUM PDF:
{curriculum_text}

LEARNING OBJECTIVES PDF:
{learning_objectives_text}
"""
    structure = _clean_json(_chat(client, [{"role": "system", "content": "Return valid JSON only."}, {"role": "user", "content": structure_prompt}], max_tokens=8000))

    # STAGE 2 — benchmark comparison
    update(28, "Comparing the curriculum with modern global benchmarks")
    benchmark_text = "\n".join(f"- {b['id']}: {b['name']} — {b['signals']} (weight {b['weight']})" for b in BENCHMARKS)
    comparison_prompt = f"""
You are NayaNisab Agent 2, a curriculum benchmarking specialist.

Compare this Pakistani university curriculum against a transparent, subject-specific modern global benchmark framework for the chosen subject. This is not a ranking of the university. It is an alignment assessment against current knowledge, skills, practices and future-facing expectations relevant to the selected subject.

IMPORTANT:
- Use only evidence reasonably supported by the uploaded content.
- Do not claim a topic is absent if the document clearly covers it under another name.
- Distinguish between 'present', 'partial', and 'missing'.
- Treat tools that can age quickly (specific programming languages, frameworks, cloud products) as examples rather than permanent curriculum requirements.
- Focus on durable capabilities plus relevant current/emerging domains.

BENCHMARKS:
{benchmark_text}

STRUCTURED CURRICULUM:
{json.dumps(structure, ensure_ascii=False)}

Return JSON:
{{
  "dimension_scores": [
    {{
      "id": "benchmark id",
      "score": 0-100,
      "evidence": "specific curriculum evidence",
      "missing": "what is missing or weak",
      "priority": "High|Medium|Low"
    }}
  ],
  "top_global_gaps": [{{"title":"...","reason":"...","affected_courses":["..."]}}],
  "first_gap_point": "Explain the earliest point in the programme where modernisation pressure becomes visible.",
  "benchmark_note": "One sentence explaining that this is a heuristic benchmark, not a formal accreditation judgement."
}}
"""
    comparison = _clean_json(_chat(client, [{"role": "system", "content": "Return valid JSON only."}, {"role": "user", "content": comparison_prompt}], max_tokens=9000))
    dims = normalise_dimension_scores(comparison.get("dimension_scores", []))
    overall = calculate_overall_score(dims)

    # STAGE 3 — gap diagnosis
    update(48, "Finding the most important gaps and where they begin")
    gap_prompt = f"""
You are NayaNisab Agent 3, a diagnostic analyst. Identify the most important curriculum gaps revealed by the benchmark.

University: {university}
Overall modernisation score: {overall}/100

Return JSON:
{{
  "first_gap": {{"course_or_stage":"...","what_is_missing":"...","why_it_matters":"..."}},
  "critical_gaps": [
    {{"title":"...","severity":"Critical|High|Medium","current_state":"...","desired_state":"...","why_now":"...","evidence":"...","recommended_change":"..."}}
  ],
  "quick_wins": ["..."],
  "keep_as_is": ["..."],
  "teacher_message": "A concise human explanation a university teacher can understand immediately."
}}

STRUCTURED CURRICULUM:
{json.dumps(structure, ensure_ascii=False)}

BENCHMARK RESULTS:
{json.dumps(comparison, ensure_ascii=False)}
"""
    gaps = _clean_json(_chat(client, [{"role": "system", "content": "Return valid JSON only."}, {"role": "user", "content": gap_prompt}], max_tokens=8500))

    # STAGE 4 — recommendations
    update(66, "Designing practical curriculum improvements")
    rec_prompt = f"""
You are NayaNisab Agent 4, an academic curriculum modernisation specialist.

Create changes that a Pakistani university can realistically discuss and approve. Prefer updating course content, labs, projects, prerequisites, tools, assessments, and elective choices instead of simply adding many new courses.

Return JSON:
{{
  "recommendations": [
    {{"priority":"Immediate|Mandatory|Optional","change":"...","where_to_apply":"course or programme area","reason":"...","implementation":"..."}}
  ],
  "proposed_course_updates": [
    {{"course":"...","current_focus":"...","updated_focus":"...","new_topics":["..."],"practical_component":"...","assessment_update":"..."}}
  ],
  "new_or_strengthened_components": [
    {{"name":"...","type":"course|module|lab|project|elective","reason":"...","suggested_position":"..."}}
  ]
}}

STRUCTURE:
{json.dumps(structure, ensure_ascii=False)}

GAPS:
{json.dumps(gaps, ensure_ascii=False)}
"""
    recommendations = _clean_json(_chat(client, [{"role": "system", "content": "Return valid JSON only."}, {"role": "user", "content": rec_prompt}], max_tokens=9000))

    # STAGE 5 — revised curriculum draft
    update(84, "Preparing the proposed modernised curriculum")
    rewrite_prompt = f"""
You are NayaNisab Agent 5, the curriculum drafting agent.

Generate a concise teacher-reviewable revised curriculum draft for {university}'s {subject} programme. Do not pretend this is officially approved. Preserve strong existing material, add or modernise where justified, and make the changes easy to compare.

Return JSON:
{{
  "title": "Proposed Modernised Curriculum Draft",
  "executive_summary": "...",
  "principles": ["..."],
  "revised_curriculum": [
    {{"course_or_area":"...","status":"Keep|Update|Strengthen|Add","updated_scope":"...","key_topics":["..."],"practical_work":"...","assessment":"..."}}
  ],
  "change_log": [
    {{"change":"...","old_state":"...","new_state":"...","reason":"..."}}
  ],
  "teacher_review_points": ["..."],
  "disclaimer": "AI-generated proposal requiring academic review and institutional approval."
}}

ORIGINAL STRUCTURE:
{json.dumps(structure, ensure_ascii=False)}

BENCHMARK RESULTS:
{json.dumps(comparison, ensure_ascii=False)}

DIAGNOSTIC GAPS:
{json.dumps(gaps, ensure_ascii=False)}

RECOMMENDATIONS:
{json.dumps(recommendations, ensure_ascii=False)}
"""
    draft = _clean_json(_chat(client, [{"role": "system", "content": "Return valid JSON only."}, {"role": "user", "content": rewrite_prompt}], max_tokens=12000))
    update(100, "Analysis complete")

    return {
        "university": university,
        "subject": subject,
        "score": overall,
        "band": "HIGH WARNING" if overall < 50 else "IMPROVEMENT REQUIRED" if overall <= 80 else "FUTURE-READY",
        "structure": structure,
        "benchmark": {"dimension_scores": dims, "top_global_gaps": comparison.get("top_global_gaps", []), "first_gap_point": comparison.get("first_gap_point", ""), "benchmark_note": comparison.get("benchmark_note", "")},
        "gaps": gaps,
        "recommendations": recommendations,
        "draft": draft,
    }
