import logging
from typing import Any, Dict
from google.genai import types


from app.utils.parse_json_response import safe_parse_json_response

logger = logging.getLogger(__name__)


class ReflectionAgent:
    """Performs a final sanity check, validates, and compiles feedback for CS1 students."""

    def __init__(self, client, model_name: str):
        self.client = client
        self.model_name = model_name

    def generate_prompt(self, state: Dict[str, Any]) -> str:
        return f"""
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
                "column": {{ "start": number, "end": number }},
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

    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug("Starting ReflectionAgent")
        logger.debug(f"Input state: {state}")

        new_state = dict(state)
        prompt = self.generate_prompt(state)

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
            candidate_count=1,
            max_output_tokens=2048,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )
            parsed = safe_parse_json_response(response.text)

            if parsed and parsed.get("final_report"):
                new_state["final_report"] = parsed.get("final_report")
            else:
                # Fallback: compile a simple final report from existing feedback
                new_state["final_report"] = {
                    "feedback": new_state.get("categorized_feedback", [])
                    or new_state.get("improvement_notes", [])
                    or [],
                    "meta": {"validated": True},
                }
        except Exception as e:
            logger.error(f"ReflectionAgent error: {e}")
            # Minimal final report on error
            new_state["final_report"] = {
                "feedback": [],
                "meta": {"validated": False, "error": str(e)},
            }

        logger.debug(f"ReflectionAgent output state: {new_state}")
        return new_state
