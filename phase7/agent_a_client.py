"""Agent A — A2A client. Formats a doc, sends to Agent B via real A2A protocol."""

from uuid import uuid4

import httpx
from a2a.client.client import Client, ClientConfig
from a2a.client.client_factory import create_client
from a2a.types.a2a_pb2 import Message, Part, Role, SendMessageRequest

_client: Client | None = None


async def get_client() -> Client:
    global _client
    if _client is None:
        config = ClientConfig(httpx_client=httpx.AsyncClient(timeout=120.0))
        _client = await create_client("http://localhost:9999", client_config=config)
    return _client


async def send_to_agent_b(formatted_doc: str, question: str) -> dict:
    """Send formatted doc + question to Agent B via A2A. Returns answer and b_tokens."""
    client = await get_client()
    message_text = f"{formatted_doc}\n\nQUESTION: {question}"

    request = SendMessageRequest(
        message=Message(
            message_id=str(uuid4()),
            role=Role.Value("ROLE_USER"),
            parts=[Part(text=message_text)],
        )
    )

    answer_text = ""
    async for response in client.send_message(request):
        if response.HasField("message"):
            for part in response.message.parts:
                if part.WhichOneof("content") == "text":
                    answer_text += part.text
        elif response.HasField("status_update"):
            su = response.status_update
            if su.HasField("status") and su.status.HasField("message"):
                for part in su.status.message.parts:
                    if part.WhichOneof("content") == "text":
                        answer_text += part.text

    # Parse metadata encoded by Agent B
    b_tokens = 0
    latency_ms = 0
    clean_answer = answer_text
    if "\n\n[META:" in answer_text:
        clean_answer, meta_str = answer_text.rsplit("\n\n[META:", 1)
        meta_str = meta_str.rstrip("]")
        for kv in meta_str.split(","):
            k, _, v = kv.partition("=")
            if k == "b_tokens":
                b_tokens = int(v)
            elif k == "latency_ms":
                latency_ms = int(v)

    return {"answer": clean_answer, "b_tokens": b_tokens, "latency_ms": latency_ms}
