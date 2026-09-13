import json
import re
import time
from typing import Callable, Optional

from groq import Groq

from benchmarks import BENCHMARKS
from scoring import calculate_overall_score, normalise_dimension_scores

MODEL_DEFAULT = "openai/gpt-oss-20b"
# The user's on-demand organization currently has an 8,000 TPM ceiling.
# Keep the whole five-stage workflow comfortably below it and retry briefly on 429s.
CALL_BUDGETS = [900, 900, 950, 1050]
MAX_SOURCE_CHARS = 9_000
MAX_OBJECTIVE_CHARS = 4_000
MAX_CONTEXT_CHARS = 4_500
RETRY_DELAYS = (2.0, 5.0, 10.0)


def _clean_json(text: str) -> dict:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    value = None
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            value = json.loads(text[start:end + 1])
        else:
            raise
    return value if isinstance(value, dict) else {"value": value}


def _compact(value, max_chars: int = MAX_CONTEXT_CHARS):
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if isinstance(v, list):
                out[k] = v[:6]
            else:
                out[k] = v
        value = out
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if len(text) <= max_chars:
        return value
    return {"truncated_context": text[:max_chars]}


def _trim(text: str, limit: int) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    head = int(limit * 0.70)
    tail = limit - head
    return text[:head] + "\n[...middle omitted... ]\n" + text[-tail:]


def _chat(client: Groq, messages: list[dict], *, max_tokens: int) -> str:
    last_err = None
    for delay in (0.0, *RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        try:
            response = client.chat.completions.create(
                model=MODEL_DEFAULT,
                messages=messages,
                temperature=0.1,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as exc:
            last_err = exc
            text = str(exc)
            if "429" not in text and "rate_limit_exceeded" not in text:
                raise
    raise last_err


def _local_extract(curriculum_text: str, objectives_text: str) -> dict:
    """Cheap deterministic stage: avoids spending a model call just to repeat the PDF text."""
    combined = _trim(curriculum_text, MAX_SOURCE_CHARS)
    objectives = _trim(objectives_text, MAX_OBJECTIVE_CHARS)
    lines = [re.sub(r"\s+", " ", x).strip() for x in combined.splitlines() if x.strip()]
    candidate_topics = []
    for line in lines:
        if 20 <= len(line) <= 180 and any(ch.isalpha() for ch in line):
            if any(token in line.lower() for token in ("course", "system", "distribution", "design", "analysis", "engineering", "power", "project", "lab", "technology")):
                candidate_topics.append(line)
    return {
        "source_excerpt": combined,
        "objectives_excerpt": objectives,
        "candidate_topics": candidate_topics[:20],
        "source_note": "Raw source is retained only in compact excerpts; downstream stages use structured summaries."
    }


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

    # Stage 1 (local, no API): reduce large PDF text before any model request.
    update(10, "Reading and structuring the submitted curriculum")
    source = _local_extract(curriculum_text, learning_objectives_text)

    # Stage 2: compact curriculum understanding.
    update(28, "Comparing the curriculum with modern global benchmarks")
    prompt2 = f"""
NayaNisab curriculum analyst. Subject: {subject}. University: {university}.
Use the supplied excerpts only. Extract concise facts for later analysis; do not recommend changes yet.
Return JSON with keys: program_summary, course_inventory (max 8 items), learning_outcomes (max 8), tools_and_technologies (max 8), assessment_signals (max 6), emerging_topics (max 6).

CURRICULUM EXCERPT:\n{source['source_excerpt']}
LEARNING OBJECTIVES EXCERPT:\n{source['objectives_excerpt']}
"""
    structure = _clean_json(_chat(client, [{"role":"system","content":"Return valid JSON only."},{"role":"user","content":prompt2}], max_tokens=CALL_BUDGETS[0]))
    structure_context = _compact(structure)

    # Stage 3: benchmark and score.
    update(46, "Finding the most important gaps and where they begin")
    benchmark_text = "\n".join(f"- {b['id']}: {b['name']} — {b['signals']}" for b in BENCHMARKS)
    prompt3 = f"""
NayaNisab benchmarking specialist for {subject}. Compare the structured curriculum with current global and industry-facing expectations. Do not claim any single vendor is mandatory.
Benchmark dimensions:\n{benchmark_text}
Structured curriculum:\n{json.dumps(structure_context, ensure_ascii=False, separators=(',',':'))}
Return JSON: dimension_scores (max 10 items with id,score,evidence,missing,priority), top_global_gaps (max 5 items), first_gap_point, benchmark_note.
"""
    comparison = _clean_json(_chat(client, [{"role":"system","content":"Return valid JSON only."},{"role":"user","content":prompt3}], max_tokens=CALL_BUDGETS[1]))
    dims = normalise_dimension_scores(comparison.get("dimension_scores", []))
    overall = calculate_overall_score(dims)
    comparison_context = _compact({"dimension_scores": dims, "top_global_gaps": comparison.get("top_global_gaps", []), "first_gap_point": comparison.get("first_gap_point", ""), "benchmark_note": comparison.get("benchmark_note", "")})

    # Stage 4: recommendations and change plan in one compact request.
    update(66, "Designing practical curriculum improvements")
    prompt4 = f"""
You are NayaNisab's academic modernisation specialist for {subject} at {university}.
Overall score: {overall}/100.
Create practical, realistic changes for a Pakistani university. Preserve strong foundations. Prioritise course-content updates, labs, projects, assessment, prerequisites, and electives.
Return JSON with: first_gap, critical_gaps (max 5), recommendations (max 6; priority Immediate|Mandatory|Optional), proposed_course_updates (max 6), teacher_message.
STRUCTURE:\n{json.dumps(structure_context, ensure_ascii=False, separators=(',',':'))}
BENCHMARK:\n{json.dumps(comparison_context, ensure_ascii=False, separators=(',',':'))}
"""
    plan = _clean_json(_chat(client, [{"role":"system","content":"Return valid JSON only."},{"role":"user","content":prompt4}], max_tokens=CALL_BUDGETS[2]))
    plan_context = _compact(plan)

    # Stage 5: concise 4-page-report payload.
    update(84, "Preparing the proposed modernised curriculum")
    prompt5 = f"""
You are NayaNisab's curriculum drafting specialist. Prepare a teacher-reviewable modernised curriculum proposal for {university}'s {subject}. It is a proposal, not an officially approved curriculum.
Return JSON with: executive_summary, principles (max 5), revised_curriculum (max 8 items with course_or_area,status,updated_scope,key_topics,practical_work,assessment), change_log (max 6 items with change,old_state,new_state,reason), teacher_review_points (max 5), disclaimer.
SCORE: {overall}/100\nSTRUCTURE:\n{json.dumps(structure_context, ensure_ascii=False, separators=(',',':'))}\nPLAN:\n{json.dumps(plan_context, ensure_ascii=False, separators=(',',':'))}
"""
    draft = _clean_json(_chat(client, [{"role":"system","content":"Return valid JSON only."},{"role":"user","content":prompt5}], max_tokens=CALL_BUDGETS[3]))
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
        "gaps": {
            "first_gap": plan.get("first_gap", comparison.get("first_gap_point", "")),
            "critical_gaps": plan.get("critical_gaps", []),
            "teacher_message": plan.get("teacher_message", ""),
        },
        "recommendations": {
            "recommendations": plan.get("recommendations", []),
            "proposed_course_updates": plan.get("proposed_course_updates", []),
        },
        "draft": draft,
    }
