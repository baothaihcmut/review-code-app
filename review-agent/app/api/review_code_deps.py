import os
from fastapi import Depends
from app.agents.logic_agent import LogicAgent
from app.agents.concept_mapping_agent import ConceptMappingAgent
from app.agents.fix_hint_agent import FixHintAgent
from app.agents.improvement_agent import ImprovementAgent
from app.agents.overview_agent import OverviewAgent
from app.agents.reflection_agent import ReflectionAgent
from app.services.review_code_service import ReviewCodeService
from together import Together


def get_together_client() -> Together:
    api_key = os.environ.get("TOGETHER_API_KEY")
    if not api_key:
        raise ValueError("Environment variable TOGETHER_API_KEY is not set.")
    return Together(api_key=api_key)


def get_logic_agent(client=Depends(get_together_client)) -> LogicAgent:
    return LogicAgent(
        client=client, model_name="Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8"
    )  # replace with your model


def get_concept_mapping_agent(
    client=Depends(get_together_client),
) -> ConceptMappingAgent:
    return ConceptMappingAgent(
        client=client, model_name="Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8"
    )


def get_fix_hint_agent(client=Depends(get_together_client)) -> FixHintAgent:
    return FixHintAgent(
        client=client, model_name="Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8"
    )


def get_improvement_agent(client=Depends(get_together_client)) -> ImprovementAgent:
    return ImprovementAgent(
        client=client, model_name="Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8"
    )


def get_overview_agent(client=Depends(get_together_client)) -> OverviewAgent:
    return OverviewAgent(
        client=client, model_name="Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8"
    )


def get_reflection_agent(client=Depends(get_together_client)) -> ReflectionAgent:
    return ReflectionAgent(
        client=client, model_name="Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8"
    )


# -----------------------------
# Dependency for ReviewCodeService
# -----------------------------
def get_review_service(
    logic_agent: LogicAgent = Depends(get_logic_agent),
    concept_mapping_agent: ConceptMappingAgent = Depends(get_concept_mapping_agent),
    fix_hint_agent: FixHintAgent = Depends(get_fix_hint_agent),
    improvement_agent: ImprovementAgent = Depends(get_improvement_agent),
    overview_agent: OverviewAgent = Depends(get_overview_agent),
    reflection_agent: ReflectionAgent = Depends(get_reflection_agent),
) -> ReviewCodeService:
    return ReviewCodeService(
        logic_agent=logic_agent,
        concept_mapping_agent=concept_mapping_agent,
        fix_hint_agent=fix_hint_agent,
        improvement_agent=improvement_agent,
        overview_agent=overview_agent,
        reflection_agent=reflection_agent,
    )
