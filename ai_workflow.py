import json
import re
import time
from typing import Callable, Optional

from groq import Groq

from benchmarks import BENCHMARKS
from scoring import calculate_overall_score, normalise_dimension_scores

MODEL = "openai/gpt-oss-20b"
# Keep the combined request footprint below the user's 8K TPM on-demand ceiling.
MAX_SOURCE_CHARS = 3_500
MAX_OBJECTIVE_CHARS = 1_800
MAX_CONTEXT_CHARS = 3_000
RETRY_DELAYS = (2.0, 5.0)


def _clean_json(text: str) -> dict:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            value = json.loads(text[start:end + 1])
        else:
            raise
    return value if isinstance(value, dict) else {"value": value}


def _trim(text: str, limit: int) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    head = int(limit * 0.68)
    tail = limit - head
    return text[:head] + "\n[...middle omitted...]\n" + text[-tail:]


def _compact(value, max_chars: int = MAX_CONTEXT_CHARS):
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if len(text) <= max_chars:
        return value
    return {"truncated_context": text[:max_chars]}


def _chat(client: Groq, messages: list[dict], *, max_tokens: int, schema: dict) -> str:
    last_err = None
    for delay in (0.0, *RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.0,
                reasoning_effort="low",
                max_completion_tokens=max_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema["name"],
                        "strict": True,
                        "schema": schema["schema"],
                    },
                },
            )
            return response.choices[0].message.content
        except Exception as exc:
            last_err = exc
            text = str(exc)
            if "429" not in text and "rate_limit_exceeded" not in text:
                raise
    raise last_err


SCHEMA_STRUCTURE = {
    "name": "curriculum_structure",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "program_summary": {"type": "string"},
            "course_inventory": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
            "learning_outcomes": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
            "tools_and_technologies": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
            "assessment_signals": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
        },
        "required": ["program_summary", "course_inventory", "learning_outcomes", "tools_and_technologies", "assessment_signals"],
    },
}

SCHEMA_BENCHMARK = {
    "name": "curriculum_benchmark",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "dimension_scores": {
                "type": "array", "maxItems": 8,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "id": {"type": "string"},
                        "score": {"type": "integer", "minimum": 0, "maximum": 100},
                        "evidence": {"type": "string"},
                        "missing": {"type": "string"},
                        "priority": {"type": "string", "enum": ["Immediate", "Mandatory", "Optional"]},
                    },
                    "required": ["id", "score", "evidence", "missing", "priority"],
                },
            },
            "top_global_gaps": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
            "first_gap_point": {"type": "string"},
            "benchmark_note": {"type": "string"},
        },
        "required": ["dimension_scores", "top_global_gaps", "first_gap_point", "benchmark_note"],
    },
}

SCHEMA_PLAN = {
    "name": "modernisation_plan",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "first_gap": {"type": "string"},
            "critical_gaps": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
            "recommendations": {
                "type": "array", "maxItems": 5,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "title": {"type": "string"},
                        "priority": {"type": "string", "enum": ["Immediate", "Mandatory", "Optional"]},
                        "action": {"type": "string"},
                    },
                    "required": ["title", "priority", "action"],
                },
            },
            "proposed_course_updates": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
            "teacher_message": {"type": "string"},
        },
        "required": ["first_gap", "critical_gaps", "recommendations", "proposed_course_updates", "teacher_message"],
    },
}

SCHEMA_DRAFT = {
    "name": "curriculum_draft",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "executive_summary": {"type": "string"},
            "principles": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
            "revised_curriculum": {
                "type": "array", "maxItems": 6,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "course_or_area": {"type": "string"},
                        "status": {"type": "string"},
                        "updated_scope": {"type": "string"},
                        "key_topics": {"type": "string"},
                        "practical_work": {"type": "string"},
                        "assessment": {"type": "string"},
                    },
                    "required": ["course_or_area", "status", "updated_scope", "key_topics", "practical_work", "assessment"],
                },
            },
            "change_log": {
                "type": "array", "maxItems": 5,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "change": {"type": "string"},
                        "old_state": {"type": "string"},
                        "new_state": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["change", "old_state", "new_state", "reason"],
                },
            },
            "teacher_review_points": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
            "disclaimer": {"type": "string"},
        },
        "required": ["executive_summary", "principles", "revised_curriculum", "change_log", "teacher_review_points", "disclaimer"],
    },
}


def _local_extract(curriculum_text: str, objectives_text: str) -> dict:
    curriculum = _trim(curriculum_text, MAX_SOURCE_CHARS)
    objectives = _trim(objectives_text, MAX_OBJECTIVE_CHARS)
    return {
        "source_excerpt": curriculum,
        "objectives_excerpt": objectives,
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

    def update(p: int, msg: str):
        if progress:
            progress(p, msg)

    source = _local_extract(curriculum_text, learning_objectives_text)

    update(15, "Reading and structuring the submitted curriculum")
    structure_prompt = f"""
Analyse the submitted curriculum for the subject '{subject}' at '{university}'. Use only the supplied text. Be concise.
Return only the required structured fields. Do not invent courses, tools, outcomes or assessments.

CURRICULUM:\n{source['source_excerpt']}

LEARNING OBJECTIVES:\n{source['objectives_excerpt']}
"""
    structure = _clean_json(_chat(
        client,
        [{"role": "system", "content": "Extract factual curriculum information."}, {"role": "user", "content": structure_prompt}],
        max_tokens=500,
        schema=SCHEMA_STRUCTURE,
    ))

    update(40, "Comparing the curriculum with modern global benchmarks")
    benchmark_text = "\n".join(f"{b['id']}: {b['name']} - {b['signals']}" for b in BENCHMARKS[:8])
    benchmark_prompt = f"""
Benchmark this {subject} curriculum against current global and industry-facing expectations. Do not claim a single vendor is mandatory. Score each listed dimension 0-100 using evidence from the structured curriculum; be concise.

DIMENSIONS:\n{benchmark_text}

STRUCTURED CURRICULUM:\n{json.dumps(_compact(structure), ensure_ascii=False)}
"""
    comparison = _clean_json(_chat(
        client,
        [{"role": "system", "content": "Return a compact benchmark assessment."}, {"role": "user", "content": benchmark_prompt}],
        max_tokens=650,
        schema=SCHEMA_BENCHMARK,
    ))
    dims = normalise_dimension_scores(comparison.get("dimension_scores", []))
    overall = calculate_overall_score(dims)

    update(65, "Identifying the most important gaps and practical improvements")
    plan_prompt = f"""
Create a concise modernisation plan for {university}'s {subject}. Preserve valid foundations. Focus on the most important missing content, tools, practical work and assessment changes. Use Immediate, Mandatory and Optional priorities.

SCORE: {overall}/100
BENCHMARK:\n{json.dumps(_compact(comparison), ensure_ascii=False)}
STRUCTURE:\n{json.dumps(_compact(structure), ensure_ascii=False)}
"""
    plan = _clean_json(_chat(
        client,
        [{"role": "system", "content": "Design practical curriculum improvements."}, {"role": "user", "content": plan_prompt}],
        max_tokens=750,
        schema=SCHEMA_PLAN,
    ))

    update(88, "Preparing the proposed modernised curriculum")
    draft_prompt = f"""
Prepare a concise teacher-reviewable modernised curriculum proposal for {university}'s {subject}. This is a proposal, not an approved curriculum. Keep entries short enough for a 4-page report. Prefer high-value changes over detail.

SCORE: {overall}/100
PLAN:\n{json.dumps(_compact(plan), ensure_ascii=False)}
BENCHMARK:\n{json.dumps(_compact(comparison), ensure_ascii=False)}
"""
    draft = _clean_json(_chat(
        client,
        [{"role": "system", "content": "Draft a concise modern curriculum proposal."}, {"role": "user", "content": draft_prompt}],
        max_tokens=800,
        schema=SCHEMA_DRAFT,
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
