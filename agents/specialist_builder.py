from typing import List

from gpc_agents.src.agents import Agent, FileSearchTool, ModelSettings, CodeInterpreterTool, WebSearchTool, HostedMCPTool
from openai.types.responses.file_search_tool_param import RankingOptions
from openai.types.responses.tool_param import CodeInterpreter, Mcp
from openai.types.responses.web_search_tool_param import UserLocation
import os

from .config import DEFAULT_MODEL
from .guardrails import enforce_citation_json, profanity_filter, pii_filter, length_guardrail
from .structures import AnswerWithCitations
from .citation_verifier import verify_citations

_VECTOR_STORE_ID = "vs_67f06532f1008191921744f7b0643ab6"


def create_specialist(
    *,
    name: str,
    instructions: str,
    domain: str,
    extra_tools: List = None,
) -> Agent:
    """Return a fully-featured specialist agent."""

    tools = [
        FileSearchTool(
            vector_store_ids=[_VECTOR_STORE_ID],
            max_num_results=5,
            include_search_results=True,
            ranking_options={"model": "hybrid"},
            filters={"chapter": {"eq": domain}},
        ),
    ]

    if extra_tools:
        tools.extend(extra_tools)

    # Append hosted tools
    # Code interpreter (simple container)
    tools.extend([
        CodeInterpreterTool(tool_config=CodeInterpreter()),
        WebSearchTool(user_location=UserLocation(country="US", region="LA"), search_context_size="high"),
    ])

    mcp_url = os.getenv("MCP_PERMIT_URL")
    if mcp_url:
        tools.append(
            HostedMCPTool(tool_config={"url": mcp_url, "name": "permit_service"})
        )

    return Agent(
        name=name,
        instructions=instructions,
        model=DEFAULT_MODEL,
        model_settings=ModelSettings(),
        tools=tools,
        input_guardrails=[profanity_filter, pii_filter, length_guardrail],
        output_guardrails=[enforce_citation_json, verify_citations],
        output_type=AnswerWithCitations,
    ) 