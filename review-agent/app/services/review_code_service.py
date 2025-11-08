import logging


from app.agents.concept_mapping_agent import ConceptMappingAgent
from app.agents.fix_hint_agent import FixHintAgent
from app.agents.improvement_agent import ImprovementAgent
from app.agents.logic_agent import LogicAgent
from app.agents.overview_agent import OverviewAgent
from app.agents.reflection_agent import ReflectionAgent
from app.models.review_state import ReviewState
from langgraph.graph import StateGraph
from typing import cast


logger = logging.getLogger(__name__)


class ReviewCodeService:
    def __init__(
        self,
        logic_agent: LogicAgent,
        concept_mapping_agent: ConceptMappingAgent,
        fix_hint_agent: FixHintAgent,
        improvement_agent: ImprovementAgent,
        overview_agent: OverviewAgent,
        reflection_agent: ReflectionAgent,
    ):
        self.logic_agent = logic_agent
        self.concept_mapping_agent = concept_mapping_agent
        self.fix_hint_agent = fix_hint_agent
        self.improvement_agent = improvement_agent
        self.overview_agent = overview_agent
        self.reflection_agent = reflection_agent

        # Build the workflow graph
        self.workflow = self.create_review_graph()

    def create_review_graph(self):
        workflow = StateGraph(ReviewState)

        # Add nodes for each agent
        workflow.add_node("logic", self.logic_agent.analyze)
        workflow.add_node("concept_map", self.concept_mapping_agent.analyze)
        workflow.add_node("fix_hint", self.fix_hint_agent.analyze)
        workflow.add_node("improve", self.improvement_agent.analyze)
        workflow.add_node("overview", self.overview_agent.analyze)

        workflow.set_entry_point("logic")

        # Conditional routing functions
        def route_after_logic(state: ReviewState) -> str:
            logger.debug("Determining route after logic agent")
            if state["logic_issues"] and len(state["logic_issues"]) > 0:
                logger.debug("Route: has_errors -> concept_map")
                return "concept_map"
            if state.get("needs_improvement"):
                logger.debug("Route: needs_improvement -> improve")
                return "improve"
            return "improve"

        def route_after_concept_map(state: ReviewState) -> str:
            return "fix_hint"

        # Add conditional edges
        workflow.add_conditional_edges(
            "logic",
            route_after_logic,
            {"concept_map": "concept_map", "improve": "improve"},
        )
        workflow.add_conditional_edges(
            "concept_map",
            route_after_concept_map,
            {"fix_hint": "fix_hint"},
        )
        workflow.add_conditional_edges(
            "fix_hint",
            lambda s: "improve",
            {"improve": "improve"},
        )
        workflow.add_conditional_edges(
            "improve",
            lambda s: "overview",
            {"overview": "overview"},
        )

        workflow.set_finish_point("overview")

        return workflow.compile()

    async def review_code(self, state: ReviewState) -> ReviewState:
        """Run the full review workflow on a student's submission state using TypedDict."""

        logger.debug("Starting review workflow")

        # Run the workflow
        final_state_dict = await self.workflow.ainvoke(state)

        logger.debug(f"Final state: {final_state_dict}")

        # Cast the returned dict to ReviewState TypedDict
        return cast(ReviewState, final_state_dict)
