from typing import Literal, NotRequired, TypedDict, Any, Dict, List


class Location(TypedDict):
    start_line: int
    start_col: int
    end_line: int
    end_col: int


class LogicIssue(TypedDict):
    issue: str
    evidence: int
    location: NotRequired[Location]
    code_snippet: str
    relevant_concept: list[str]
    other_concept: list[str]
    fix_suggestion: str


class ImprovementNote(TypedDict):
    location: NotRequired[Location]
    code_snippet: str
    fix_suggestion: str
    issue: str


class ReviewItem(TypedDict):
    type: Literal["Warning", "Error"]
    location: NotRequired[Location]
    code_snippet: str
    fix_suggestion: str
    issue: str
    relevant_concept: list[str]


def create_logic_issue(
    issue: str = "",
    evidence: int = -1,
    code_snippet: str = "",
    location: Location = None,
) -> LogicIssue:
    """
    Helper function to create a LogicIssue with default empty lists for concepts.
    """
    return {
        "issue": issue,
        "evidence": evidence,
        "code_snippet": code_snippet,
        "location": location,
        "relevant_concept": [],
        "other_concept": [],
        "fix_suggestion": "",
    }


class SandBoxResult(TypedDict):
    id: int
    input: str
    expected: str
    actual: str


class ReviewState(TypedDict):
    code: str
    sandbox_results: List[SandBoxResult]
    assignment_requirements: str
    expected_concepts: List[str]
    logic_issues: Dict[int, LogicIssue]
    concept_issues: List[Dict[str, Any]]
    improvement_notes: List[ImprovementNote]
    overview: str
    review_items: List[ReviewItem]


def create_initial_state(
    code: str,
    sandbox_results: List[SandBoxResult],
    assignment_requirements: str,
    expected_concepts: List[str],
) -> ReviewState:
    """Helper function to create a properly initialized ReviewState"""
    return {
        "code": code,
        "sandbox_results": sandbox_results,
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
