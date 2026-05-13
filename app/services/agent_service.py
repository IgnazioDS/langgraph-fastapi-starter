import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph

from app.db.connection import db_conn
from app.db.queries import (
    CREATE_SESSION,
    GET_SESSION,
    GET_SESSION_MESSAGES,
    INCREMENT_SESSION_MESSAGE_COUNT,
    INSERT_MESSAGE,
)
from app.graph.state import AgentState
from app.models.responses import MessageResponse, RunAgentResponse, SessionResponse, TokenUsage


class AgentService:
    def __init__(
        self,
        graph: CompiledStateGraph[AgentState, None, AgentState, AgentState],
    ) -> None:
        self._graph = graph

    async def run(
        self,
        session_id: str,
        tenant_id: str,
        message: str,
    ) -> RunAgentResponse:
        """Run the agent for a single turn.

        1. Upsert the session record
        2. Load full message history
        3. Invoke the graph (sync, via run_in_executor)
        4. Persist user + assistant messages
        5. Return structured response with token usage
        """
        # 1. Ensure session exists
        session_uuid = str(uuid.uuid4())
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    CREATE_SESSION,
                    {
                        "id": session_uuid,
                        "session_id": session_id,
                        "tenant_id": tenant_id,
                    },
                )

        # 2. Load message history
        history: list[BaseMessage] = []
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(GET_SESSION_MESSAGES, {"session_id": session_id})
                rows = cur.fetchall()

        for row in rows:
            _msg_id, _sid, role, content, _meta, _created = row
            if role == "user":
                history.append(HumanMessage(content=content))
            elif role in ("assistant", "tool"):
                history.append(AIMessage(content=content))

        # 3. Build initial state and invoke graph
        run_id = f"run_{datetime.now(tz=UTC).strftime('%Y%m%dT%H%M%S%f')}"
        initial_state: AgentState = {
            "messages": [*history, HumanMessage(content=message)],
            "session_id": session_id,
            "tenant_id": tenant_id,
            "context": [],
            "run_id": run_id,
            "input_tokens": 0,
            "output_tokens": 0,
        }

        loop = asyncio.get_event_loop()
        result = cast(
            AgentState,
            await loop.run_in_executor(None, lambda: self._graph.invoke(initial_state)),
        )

        # 4. Extract final assistant response
        final_response = ""
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                final_response = str(msg.content)
                break

        # 5. Persist messages
        user_msg_id = str(uuid.uuid4())
        asst_msg_id = str(uuid.uuid4())

        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    INSERT_MESSAGE,
                    {
                        "id": user_msg_id,
                        "session_id": session_id,
                        "role": "user",
                        "content": message,
                        "metadata": json.dumps({}),
                    },
                )
                cur.execute(
                    INSERT_MESSAGE,
                    {
                        "id": asst_msg_id,
                        "session_id": session_id,
                        "role": "assistant",
                        "content": final_response,
                        "metadata": json.dumps({"run_id": run_id}),
                    },
                )
                # Increment twice: once for user, once for assistant
                cur.execute(INCREMENT_SESSION_MESSAGE_COUNT, {"session_id": session_id})
                cur.execute(INCREMENT_SESSION_MESSAGE_COUNT, {"session_id": session_id})

        return RunAgentResponse(
            session_id=session_id,
            response=final_response,
            run_id=run_id,
            usage=TokenUsage(
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
            ),
        )

    async def get_session(
        self,
        session_id: str,
        tenant_id: str,
    ) -> SessionResponse | None:
        """Load a session and all its messages. Returns None if not found."""
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(GET_SESSION, {"session_id": session_id, "tenant_id": tenant_id})
                session_row = cur.fetchone()

        if session_row is None:
            return None

        _id, _session_id, _tenant_id, created_at, last_active_at, message_count = session_row

        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(GET_SESSION_MESSAGES, {"session_id": session_id})
                msg_rows = cur.fetchall()

        messages = [
            MessageResponse(role=role, content=content, created_at=created_at_msg)
            for _msg_id, _sid, role, content, _meta, created_at_msg in msg_rows
        ]

        return SessionResponse(
            session_id=session_id,
            message_count=message_count,
            created_at=created_at,
            last_active_at=last_active_at,
            messages=messages,
        )
