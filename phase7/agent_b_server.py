"""Agent B — A2A server (v1.0.3 SDK). Receives formatted doc + question, returns answer."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uuid import uuid4

from starlette.applications import Starlette

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.server.request_handlers.default_request_handler_v2 import DefaultRequestHandlerV2
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types.a2a_pb2 import (
    AgentCard, AgentCapabilities, AgentInterface, AgentSkill,
    Message, Part, Role,
)
from phase4.agent_b import _call_claude, _SYSTEM, count_tokens, grade_answer


AGENT_CARD = AgentCard(
    name="ACF Research Agent",
    description="Answers questions from structured document context",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=False),
    supported_interfaces=[
        AgentInterface(url="http://localhost:9999", protocol_binding="JSONRPC", protocol_version="1.0")
    ],
    skills=[
        AgentSkill(
            id="qa",
            name="Question Answering",
            description="Answer questions from provided context",
            input_modes=["text"],
            output_modes=["text"],
        )
    ],
    default_input_modes=["text"],
    default_output_modes=["text"],
)


class AgentBExecutor(AgentExecutor):
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass  # cancellation not needed for this benchmark

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        raw_text = context.get_user_input()
        if "\n\nQUESTION: " in raw_text:
            doc_context, question = raw_text.split("\n\nQUESTION: ", 1)
        else:
            doc_context = raw_text
            question = ""

        b_tokens = count_tokens(_SYSTEM + f"CONTEXT:\n{doc_context}\n\nQUESTION: {question}")
        answer, latency_ms = _call_claude(question, doc_context, "claude-haiku")

        # Encode b_tokens and latency in the reply text for orchestrator to parse
        metadata_str = f"b_tokens={b_tokens},latency_ms={latency_ms}"
        answer_with_meta = f"{answer}\n\n[META:{metadata_str}]"

        # Immediate-response mode: enqueue a single Message (no Task event needed)
        reply = Message(
            message_id=str(uuid4()),
            role=Role.Value("ROLE_AGENT"),
            parts=[Part(text=answer_with_meta)],
        )
        await event_queue.enqueue_event(reply)


_handler = DefaultRequestHandlerV2(
    agent_executor=AgentBExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=AGENT_CARD,
)

app = Starlette(
    routes=(
        create_agent_card_routes(AGENT_CARD)
        + create_jsonrpc_routes(_handler, rpc_url="/")
    )
)
