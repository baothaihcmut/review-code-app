import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any, Sequence, TypedDict
from typing_extensions import Required, NotRequired
from google import genai
from google.genai import types
import os
import logging
import operator
from langgraph.graph import StateGraph

# Configure logging for LangGraph
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("langgraph")

# --- Execution Instructions ---
# To run this service, ensure you have all dependencies installed:
# pip install fastapi uvicorn pydantic google-genai
# Then, run the API using uvicorn:
# uvicorn app:app --reload
# ------------------------------

# --- Configuration ---
# NOTE: API_KEY should be loaded from environment variables in a real application.
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCQEJejHqiSp-ZRZUai5dDvgKQUwLu-e20")
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"

# Initialize the Gemini Client outside the endpoint for efficiency
try:
    gemini_client = genai.Client(api_key=API_KEY)
except Exception as e:
    # If API key is missing, this will likely fail; better to handle at runtime or via environment variables
    print(f"Warning: Could not initialize Gemini client. API calls may fail. {e}")

# Initialize FastAPI application
app = FastAPI()


# -------------------------
# Shared state schema and constants
# -------------------------
class ReviewState(TypedDict):
    """
    TypedDict for managing review state with mutable list fields
    """

    # Required input fields
    code: Required[str]
    sandbox_result: Required[Dict[str, Any]]
    assignment_requirements: Required[str]
    expected_concepts: Required[List[str]]

    # Mutable state fields
    logic_issues: NotRequired[List[Dict[str, Any]]]
    concept_issues: NotRequired[List[Dict[str, Any]]]
    categorized_feedback: NotRequired[List[Dict[str, Any]]]
    improvement_notes: NotRequired[List[Dict[str, Any]]]
    advanced_suggestions: NotRequired[List[str]]
    static_issues: NotRequired[List[Dict[str, Any]]]
    final_report: NotRequired[Dict[str, Any]]
    # Runtime flags computed by agents
    has_errors: NotRequired[bool]
    needs_improvement: NotRequired[bool]
    # Overview text summary
    overview: NotRequired[str]
    # List of review items
    review_items: NotRequired[List[Dict[str, Any]]]


def create_initial_state(
    code: str,
    sandbox_result: Dict[str, Any],
    assignment_requirements: str,
    expected_concepts: List[str],
) -> ReviewState:
    """Helper function to create a properly initialized ReviewState"""
    return {
        "code": code,
        "sandbox_result": sandbox_result,
        "assignment_requirements": assignment_requirements,
        "expected_concepts": expected_concepts,
        "logic_issues": [],
        "concept_issues": [],
        "categorized_feedback": [],
        "improvement_notes": [],
        "advanced_suggestions": [],
        "final_report": {},
        "static_issues": [],
        # initialize runtime flags
        "has_errors": False,
        "needs_improvement": False,
        "overview": "",
        "review_items": [],
    }


def safe_parse_json_response(response: str) -> Dict[str, Any]:
    """Try to parse response into dict if it contains JSON-like text."""
    try:
        return json.loads(response)
    except Exception:
        return {"raw": str(response)}


def has_functional_errors(state: ReviewState) -> bool:
    sr = state.get("sandbox_result", {})
    if sr.get("passed_basic") is not None:
        return not bool(sr.get("passed_basic", False))
    if "cases" in sr:
        cases = sr["cases"]
        for c in cases:
            if str(c.get("output")).strip() != str(c.get("expected")).strip():
                return True
        return False
    if sr.get("errors"):
        return True
    return False


def quality_issues_present(state: ReviewState) -> bool:
    """Simple heuristic: if static analyzer reported warnings or code length / style hints."""
    static_issues = state.get("static_issues", [])
    if static_issues:
        return True
    code = state.get("code", "") or ""
    if len(code.splitlines()) > 300:
        return True
    if "/*" not in code and "//" not in code:
        return True
    return False


# ------------------------------

# ----------------------------------------------------------------------
# --- 1. Pydantic Models for Request (Input) ---
# ----------------------------------------------------------------------


class TestResult(BaseModel):
    name: str
    status: str
    input: str
    expect: str
    actual: str


class AssignmentContext(BaseModel):
    content: str
    language: str = Field(..., description="E.g., C, C++, Python")
    expected_concepts: List[str] = Field(
        default_factory=list,
        description="List of CS concepts expected to be demonstrated",
    )


class Submission(BaseModel):
    code: str


class ReviewRequest(BaseModel):
    """The complete input payload for the code review endpoint."""

    assignment: AssignmentContext
    student_submission: Submission
    test_results: List[TestResult]


# ----------------------------------------------------------------------
# --- 2. Agentic Models (Tool Input/Output) ---
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# --- 3. Review Response Models (Final Output) ---
# ----------------------------------------------------------------------


class LineContext(BaseModel):
    start: int
    end: int


class ColumnContext(BaseModel):
    start: int
    end: int


class ReviewItem(BaseModel):
    line: LineContext
    column: Optional[ColumnContext] = None
    code_snippet: str
    type: Literal["Error", "Warning"]
    issue: str = Field(
        ...,
        description="For a 'Warning', this must describe a case where it can lead to a bug.",
    )
    fix_suggestion: str


class ReviewResponse(BaseModel):
    """The structured output generated by the Gemini Model."""

    summary: str
    detail: str
    review_items: List[ReviewItem]


# ----------------------------------------------------------------------
# --- 4. Gemini API Configuration and Schema (Constants) ---
# ----------------------------------------------------------------------

SYSTEM_INSTRUCTION = (
    "You are an authoritative CS1 instructor and automated reviewer. Evaluate student submissions with precision, evidence, and conservative claims. "
    "Always ground findings in the provided inputs (the student's code and the sandbox/test snapshot). Do NOT invent test results, stack traces, or runtime behavior not present in the sandbox. "
    "Output format: When asked to produce a review, produce a single well-formed JSON object that follows the response schema exactly. Do not include markdown, commentary, or extraneous fields. "
    "Classification rules (use exactly these categories):\n"
    "- Error: A reproducible bug (failing test, runtime crash, incorrect algorithm) that causes incorrect behavior. Provide evidence (failing case or input-output pair) and a precise code location when possible.\n"
    "- Warning: A potential bug, risky practice, or style/quality issue that may lead to errors in edge cases (e.g., unchecked bounds, ambiguous naming, missing validation). Explain a concrete scenario where this could fail.\n"
    "- Correctness: A thing done well; still include a short suggestion for improvement (even if minor).\n"
    "Required fields for each review item: 'line' (start,end), optionally 'column' (start,end), 'code_snippet' (exact text), 'type' (Error|Warning|Correctness), 'issue' (concise description), 'fix_suggestion' (clear actionable suggestion).\n"
    "Safety and hallucination avoidance: If you cannot confirm an assertion from code or sandbox, mark it as 'possible' in the explanation and do not assert it as fact. Prefer asking for more information rather than fabricating evidence.\n"
    "Brevity and clarity: Keep suggestions actionable and short. When giving examples or code fragments, include only the minimal snippet and explicit line numbers.\n"
    "When generating downstream agent outputs (concept mappings, hints, improvements, overview), follow the designated JSON keys exactly and keep values simple types (strings, lists, objects)."
)

REVIEW_RESPONSE_SCHEMA_DICT = {
    "type": "OBJECT",
    "properties": {
        "summary": {
            "type": "STRING",
            "description": "A high-level summary of the code's flaws.",
        },
        "detail": {
            "type": "STRING",
            "description": "More detailed context on the main areas needing improvement.",
        },
        "review_items": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "line": {
                        "type": "OBJECT",
                        "properties": {
                            "start": {"type": "INTEGER"},
                            "end": {"type": "INTEGER"},
                        },
                    },
                    "column": {
                        "type": "OBJECT",
                        "properties": {
                            "start": {"type": "INTEGER"},
                            "end": {"type": "INTEGER"},
                        },
                    },
                    "code_snippet": {"type": "STRING"},
                    "type": {
                        "type": "STRING",
                        "enum": ["Error", "Warning", "Correctness"],
                    },
                    "issue": {
                        "type": "STRING",
                        "description": "What is wrong with this snippet. For a 'Warning', describe the case where it can lead to a bug.",
                    },
                    "fix_suggestion": {
                        "type": "STRING",
                        "description": "Specific advice on how to fix the issue.",
                    },
                },
                "required": ["line", "code_snippet", "type", "issue", "fix_suggestion"],
            },
        },
    },
    "required": ["summary", "detail", "review_items"],
}


# ----------------------------------------------------------------------
# --- 5. Agent Nodes ---
# ----------------------------------------------------------------------


def logic_agent(state: ReviewState) -> ReviewState:
    """Analyze sandbox outputs and produce logic_issues list."""
    logger.debug("Starting logic_agent")
    logger.debug(f"Input state: {state}")

    # Create a new state dict for modifications
    new_state = dict(state)

    prompt = f"""
You are an educational logic-analysis agent for C/C++ CS1. Your job is to determine whether the student's submission has logical/runtime errors (bugs) or is functionally correct but may still need stylistic/quality improvements.

Constraints:
- Use ONLY the provided sandbox_result and the code; do NOT invent test runs or outcomes.

Input CODE:
{state.get('code')}

SANDBOX RESULT:
{state.get('sandbox_result')}

Tasks (must produce JSON):
1) If there are failing test cases, runtime errors, or clear logic bugs, return a list under the key "logic_issues": [ ... ] where each item contains at least: {{"issue": "short summary", "evidence": "failing case or stack trace", "location": {{"line": n, "col": m}} (optional) }}.
2) If no reproducible logic errors are present, return an empty list for "logic_issues".
3) Additionally, provide an optional short boolean hint field "possible_quality_issues" if you notice code smells or style problems that suggest the submission may need improvement (e.g., missing comments, long function, inconsistent naming). Example: {{"possible_quality_issues": true}}.

Return a single valid JSON string containing at least the key "logic_issues" and optionally "possible_quality_issues".
"""
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.3,
        candidate_count=1,
        max_output_tokens=2048,
    )

    try:
        response = gemini_client.models.generate_content(
            model=MODEL_NAME, contents=prompt, config=config
        )
        parsed = safe_parse_json_response(response.text)
        # Accept both keys from model: logic_issues or issues
        new_state["logic_issues"] = (
            parsed.get("logic_issues") or parsed.get("issues") or []
        )
        # If model sets possible_quality_issues, respect it as a hint for needs_improvement
        if parsed.get("possible_quality_issues") is not None:
            new_state["needs_improvement"] = bool(parsed.get("possible_quality_issues"))
    except Exception as e:
        logger.error(f"Logic agent error: {e}")
        new_state["logic_issues"] = []

    # Compute runtime flags for routing
    try:
        # has_errors: true if sandbox indicates failing cases or the model returned logic issues
        new_state["has_errors"] = bool(
            new_state.get("logic_issues")
        ) or has_functional_errors(new_state)
        # needs_improvement: true if quality heuristics trigger (style/length/static warnings)
        new_state["needs_improvement"] = quality_issues_present(new_state)
    except Exception:
        # Fallback conservative defaults
        new_state.setdefault("has_errors", False)
        new_state.setdefault("needs_improvement", False)

    logger.debug(f"Logic agent output state: {new_state}")
    return new_state


def concept_mapping_agent(state: ReviewState) -> ReviewState:
    """Map logic issues to CS1 concepts."""
    logger.debug("Starting concept_mapping_agent")
    logger.debug(f"Input state: {state}")

    # Create new state dict for modifications
    new_state = dict(state)
    prompt = f"""
You are the concept-mapping agent. Your job: for each logic issue (if any), map it to one or more precise CS1 concepts (e.g., 'array bounds', 'pointer misuse', 'off-by-one', 'loop invariant', 'null deref', 'integer overflow').

Inputs you MUST use: the list under state['logic_issues'] and the assignment's expected_concepts: {state.get('expected_concepts', [])}

Output requirements (JSON only):
{{
    "concept_issues": [
        {{
            "issue_ref": <index or id referencing logic_issues>,
            "concept": "short concept name",
            "severity": "major" | "minor",
            "explanation": "1-2 sentence mapping that cites the logic issue evidence"
        }}
    ]
}}

Notes: Do NOT invent new failing cases. If a logic issue cannot be mapped confidently, set concept to "unknown" and provide a short explanation.
"""
    config = types.GenerateContentConfig(
        response_mime_type="application/json", temperature=0.3
    )

    try:
        response = gemini_client.models.generate_content(
            model=MODEL_NAME, contents=prompt, config=config
        )
        parsed = safe_parse_json_response(response.text)
        new_state["concept_issues"] = parsed.get("concept_issues") or []
    except Exception as e:
        logger.error(f"Concept mapping agent error: {e}")
        new_state["concept_issues"] = []

    logger.debug(f"Concept mapping agent output state: {new_state}")
    return new_state


def fix_hint_agent(state: ReviewState) -> ReviewState:
    """For each concept_issue produce a structured hint with exact location and fix suggestion."""
    logger.debug("Starting fix_hint_agent")
    logger.debug(f"Input state: {state}")

    # Create new state dict for modifications
    new_state = dict(state)

    prompt = f"""
You are a CS1 tutoring agent. For each concept issue, produce a detailed, structured hint that helps students fix the problem. Focus on the specific lines where each issue occurs.

CODE:
{state.get('code', '')}

Input context:
- Concept issues: {state.get('concept_issues')}
- Logic issues: {state.get('logic_issues')}
- Sandbox result: {state.get('sandbox_result')}

You must return a JSON object that EXACTLY follows this structure:
{{
    "categorized_feedback": [
        {{
            "line": {{ 
                "start": line_number,  # Where the issue begins
                "end": line_number     # Where the issue ends 
            }},
            "column": {{               # Optional
                "start": col_number,
                "end": col_number
            }},
            "code_snippet": "exact code from the specified lines",
            "type": "Error",          # Use "Error" for failing tests/runtime errors, "Warning" for risky code
            "issue": "Explain what's wrong AND how it could cause bugs",
            "fix_suggestion": "Clear steps to fix the problem (but don't give complete solution)"
        }}
    ]
}}

REQUIREMENTS:
1. For every issue, provide exact line numbers and code snippet
2. Set "type" to "Error" for failing tests/runtime errors or "Warning" for potential bugs
3. Each "issue" must explain both what's wrong AND its potential impact
4. "fix_suggestion" should guide the student without giving away the answer
5. Only report issues with clear evidence from sandbox_result, logic_issues, or concept_issues
"""
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.4,
        candidate_count=1,
        max_output_tokens=2048,
    )

    try:
        response = gemini_client.models.generate_content(
            model=MODEL_NAME, contents=prompt, config=config
        )
        parsed = safe_parse_json_response(response.text)
        new_state["categorized_feedback"] = parsed.get("categorized_feedback") or []
    except Exception as e:
        logger.error(f"Fix hint agent error: {e}")
        new_state["categorized_feedback"] = []

    logger.debug(f"Fix hint agent output state: {new_state}")
    return new_state


def improvement_agent(state: ReviewState) -> ReviewState:
    """Runs when no functional errors but quality issues exist."""
    logger.debug("Starting improvement_agent")
    logger.debug(f"Input state: {state}")

    # Create new state dict for modifications
    new_state = dict(state)

    prompt = f"""
You are a CS1 style and quality coach. Analyze the student's submission and identify style/quality issues that should be classified as WARNINGS. Use ONLY the provided code and sandbox snapshot.

CODE:
{state.get('code', '')}

Tasks (must return JSON):
1) Identify any style/quality issues such as:
   - Long functions
   - Poor variable/function naming
   - Missing or unclear comments
   - Potential edge cases (not failing but risky)
   - Code duplication
   - Poor modularity
   - Performance concerns

2) Return a JSON object with this exact structure:
{{
    "improvement_notes": [
        {{
            "line": {{ "start": line_number, "end": line_number }},
            "column": {{ "start": col_number, "end": col_number }},  # optional
            "code_snippet": "exact code from the specified lines",
            "type": "Warning",  # always "Warning" for improvement agent
            "issue": "Describe how this could lead to bugs/issues",
            "fix_suggestion": "Specific, actionable improvement suggestion"
        }}
    ],
    "is_warning": true  # Set to true if any issues found, false otherwise
}}

IMPORTANT: Each issue MUST explain how it could lead to actual bugs or problems."""
    config = types.GenerateContentConfig(
        response_mime_type="application/json", temperature=0.3
    )

    try:
        response = gemini_client.models.generate_content(
            model=MODEL_NAME, contents=prompt, config=config
        )
        parsed = safe_parse_json_response(response.text)
        new_state["improvement_notes"] = parsed.get("improvement_notes") or []
        # If the model explicitly marks is_warning, use it to set needs_improvement
        if parsed.get("is_warning") is not None:
            new_state["needs_improvement"] = bool(parsed.get("is_warning"))
        else:
            # otherwise infer from presence of improvement notes
            new_state["needs_improvement"] = bool(new_state.get("improvement_notes"))
    except Exception as e:
        logger.error(f"Improvement agent error: {e}")
        new_state["improvement_notes"] = []

    logger.debug(f"Improvement agent output state: {new_state}")
    return new_state


def advanced_concept_agent(state: ReviewState) -> ReviewState:
    """When code is correct and quality is acceptable: suggest advanced concepts."""
    logger.debug("Starting advanced_concept_agent")
    logger.debug(f"Input state: {state}")

    # Create new state dict for modifications
    new_state = dict(state)

    prompt = f"""
You are an educational advisor. Given the assignment and the student's code, suggest 1-3 advanced topics or exercises that are appropriate next steps. For each suggestion include a short title, why it is relevant, and an estimated difficulty level.

Context you MUST consider: assignment_requirements: {state.get('assignment_requirements', '')} and expected_concepts: {state.get('expected_concepts', [])}

Output (JSON only):
{{
    "advanced_suggestions": [
        {{
            "title": "Short title",
            "why": "Why this is a good next step (1-2 sentences)",
            "difficulty": "beginner|intermediate|advanced"
        }}
    ]
}}
"""
    config = types.GenerateContentConfig(
        response_mime_type="application/json", temperature=0.5
    )

    try:
        response = gemini_client.models.generate_content(
            model=MODEL_NAME, contents=prompt, config=config
        )
        parsed = safe_parse_json_response(response.text)
        new_state["advanced_suggestions"] = parsed.get("advanced_suggestions") or []
    except Exception as e:
        logger.error(f"Advanced concept agent error: {e}")
        new_state["advanced_suggestions"] = []

    logger.debug(f"Advanced concept agent output state: {new_state}")
    return new_state


def overview_agent(state: ReviewState) -> ReviewState:
    """Merge hints and improvement suggestions into a compact overview for the student/instructor."""
    logger.debug("Starting overview_agent")
    logger.debug(f"Input state: {state}")

    new_state = dict(state)

    # Build review items list from categorized_feedback and improvement_notes
    review_items = []

    # Convert categorized feedback to review items
    for item in new_state.get("categorized_feedback", []):
        if isinstance(item, dict):
            review_item = {
                "line": item.get("line", {"start": 1, "end": 1}),
                "column": item.get("column"),
                "code_snippet": item.get("code_snippet", ""),
                "type": item.get("type", "Error"),
                "issue": item.get("issue", ""),
                "fix_suggestion": item.get("fix_suggestion", ""),
            }
            review_items.append(review_item)

    # Convert improvement notes to review items
    for item in new_state.get("improvement_notes", []):
        if isinstance(item, dict):
            review_item = {
                "line": item.get("line", {"start": 1, "end": 1}),
                "column": item.get("column"),
                "code_snippet": item.get("code_snippet", ""),
                "type": "Warning",  # improvement notes are always warnings
                "issue": item.get("issue", ""),
                "fix_suggestion": item.get("fix_suggestion", ""),
            }
            review_items.append(review_item)

    # Create a short human-readable overview
    overview_lines = []
    if new_state.get("has_errors"):
        overview_lines.append(
            "Functional errors detected; see concept mapping and hints for fixes."
        )
    if new_state.get("needs_improvement"):
        overview_lines.append(
            "Code has style/quality warnings that should be addressed."
        )
    if not overview_lines:
        overview_lines.append(
            "Submission looks functionally correct and follows expected quality."
        )

    # Update state with new structure
    new_state["overview"] = " ".join(overview_lines)
    new_state["review_items"] = review_items

    logger.debug(f"Overview agent output state: {new_state}")
    return new_state


def reflection_agent(state: ReviewState) -> ReviewState:
    """Final sanity check and validation."""
    logger.debug("Starting reflection_agent")
    logger.debug(f"Input state: {state}")

    # Create new state dict for modifications
    new_state = dict(state)

    prompt = f"""
You are a CS1 (Introduction to Programming) professor reviewing the assembled feedback before it's presented to your first-year students. Your role is to ensure the feedback is:
1. Pedagogically sound and appropriate for CS1 level
2. Clear and understandable for beginners
3. Constructive and encouraging while being accurate
4. Focused on fundamental concepts they've learned

Review these components:
- Code and test results: {state.get('sandbox_result', {})}
- Identified issues: {state.get('logic_issues', [])}
- Concept mappings: {state.get('concept_issues', [])}
- Detailed feedback: {state.get('categorized_feedback', [])}
- Quality suggestions: {state.get('improvement_notes', [])}
- Advanced topics: {state.get('advanced_suggestions', [])}
- Summary overview: {state.get('overview', '')}
- Review items: {state.get('review_items', [])}

Your task (return as JSON):
{{
    "final_report": {{
        "feedback": [
            {{
                "line": {{ "start": number, "end": number }},
                "column": {{ "start": number, "end": number }},  # optional
                "code_snippet": "relevant code",
                "type": "Error|Warning",
                "issue": "Clear explanation using CS1 terminology",
                "fix_suggestion": "Step-by-step guidance appropriate for beginners",
                "educational_notes": {{
                    "concepts": ["list", "of", "relevant", "CS1", "concepts"],
                    "prerequisites": "What they need to know to understand this",
                    "learning_goal": "What they should learn from this feedback"
                }}
            }}
        ],
        "summary": {{
            "overview": "Overall assessment in encouraging, clear language",
            "key_concepts": ["main", "CS1", "concepts", "to", "focus", "on"],
            "next_steps": "Clear guidance on what to learn/review"
        }},
        "meta": {{
            "validated": true|false,
            "pedagogical_notes": "Any concerns about complexity or prerequisites",
            "difficulty_level": "beginner|intermediate|advanced"
        }}
    }}
}}

Educational Guidelines:
1. Use CS1 vocabulary consistently (e.g., "loop", "condition", "variable", etc.)
2. Break down complex issues into simpler concepts
3. Connect feedback to fundamental programming principles
4. Provide concrete, actionable steps for improvement
5. Include positive reinforcement when appropriate
6. Ensure fix suggestions don't give away complete solutions
7. Verify all feedback is based on evidence from code/tests

Remember: First-year CS students are still learning basic programming concepts. All feedback should be encouraging and educational, not just identifying problems.
    """
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.2,
        candidate_count=1,
        max_output_tokens=2048,
    )

    try:
        response = gemini_client.models.generate_content(
            model=MODEL_NAME, contents=prompt, config=config
        )
        parsed = safe_parse_json_response(response.text)
        if parsed and parsed.get("final_report"):
            new_state["final_report"] = parsed.get("final_report")
        else:
            # Create a default final report from existing state
            new_state["final_report"] = {
                "feedback": new_state.get("categorized_feedback", [])
                or new_state.get("improvement_notes", [])
                or [],
                "meta": {"validated": True},
            }
    except Exception as e:
        logger.error(f"Reflection agent error: {e}")
        # Create a minimal final report on error
        new_state["final_report"] = {
            "feedback": [],
            "meta": {"validated": False, "error": str(e)},
        }

    logger.debug(f"Reflection agent output state: {new_state}")
    return new_state


# -------------------------
# Initialize Review Graph
# -------------------------
def create_review_graph():
    workflow = StateGraph(ReviewState)

    # Add nodes for each agent
    workflow.add_node("logic", logic_agent)
    workflow.add_node("concept_map", concept_mapping_agent)
    workflow.add_node("fix_hint", fix_hint_agent)
    workflow.add_node("improve", improvement_agent)
    workflow.add_node("overview", overview_agent)
    workflow.add_node("advanced", advanced_concept_agent)
    workflow.add_node("reflection", reflection_agent)

    workflow.set_entry_point("logic")

    # Define conditional routing function
    def route_after_logic(state: ReviewState) -> str:
        logger.debug("Determining route after logic agent")
        # Prefer explicit flags set by logic_agent
        if state.get("has_errors"):
            logger.debug("Route: has_errors -> concept_map")
            return "concept_map"
        if state.get("needs_improvement"):
            logger.debug("Route: needs_improvement -> improve")
            return "improve"
        logger.debug("Route: no errors/warnings -> advanced")
        return "advanced"

    def route_after_concept_map(state: ReviewState) -> str:
        return "fix_hint"

    # Add sequential routing edges
    workflow.add_conditional_edges(
        "logic",
        route_after_logic,
        {
            "concept_map": "concept_map",
            "improve": "improve",
        },
    )

    # concept_map -> fix_hint -> overview -> reflection
    workflow.add_conditional_edges(
        "concept_map",
        route_after_concept_map,
        {"fix_hint": "fix_hint"},
    )
    workflow.add_conditional_edges(
        "fix_hint",
        lambda s: "overview",
        {"overview": "overview"},
    )

    # improve -> overview -> reflection
    workflow.add_conditional_edges(
        "improve",
        lambda s: "overview",
        {"overview": "overview"},
    )

    # overview -> reflection
    workflow.add_conditional_edges(
        "overview",
        lambda s: "reflection",
        {"reflection": "reflection"},
    )

    workflow.set_finish_point("reflection")

    return workflow.compile()


# Initialize the review graph
review_graph = create_review_graph()


# ----------------------------------------------------------------------
# --- 6. FastAPI Endpoint ---
# ----------------------------------------------------------------------


@app.post("/review_code", response_model=ReviewResponse)
async def review_code(request: ReviewRequest):
    """
    Endpoint that uses the LangGraph workflow with Gemini for code review.
    """
    try:
        # Create initial state using the helper function
        state_in = create_initial_state(
            code=request.student_submission.code,
            sandbox_result={
                "cases": [
                    {
                        "input": test.input,
                        "expected": test.expect,
                        "output": test.actual,
                        "status": test.status,
                    }
                    for test in request.test_results
                ]
            },
            assignment_requirements=request.assignment.content,
            expected_concepts=request.assignment.expected_concepts,
        )
        logger.debug(f"Creating initial state: {state_in}")

        # Run the review graph
        result_state = await review_graph.ainvoke(state_in)

        # Get the overview and review items from the result state
        overview = result_state.get("overview", "Code review completed")
        review_items = [
            ReviewItem(**item) for item in result_state.get("review_items", [])
        ]

        return ReviewResponse(
            summary=overview,
            detail="Review completed",
            review_items=review_items,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review process failed: {str(e)}")
