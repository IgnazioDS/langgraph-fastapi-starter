# Build Your First Agent From This Starter

This walkthrough is the shortest credible path from clone to a customized agent API. It assumes you want to keep the infrastructure layer intact and only replace the example research assistant with your own behavior.

## 1. Clone and boot the starter

```bash
git clone https://github.com/IgnazioDS/langgraph-fastapi-starter.git
cd langgraph-fastapi-starter
cp .env.example .env

# Required for local boot
# - set OPENAI_API_KEY
# - set POSTGRES_PASSWORD

make up
make install
make migrate
make create-key NAME="local-dev" ROLE="admin"
make dev
```

At this point you have:

- FastAPI running on `http://localhost:8000`
- PostgreSQL + pgvector running in Docker
- Alembic-applied schema
- a real API key for protected routes

## 2. Replace the example agent contract

The starter keeps the graph surface area small on purpose. Most customizations happen in four files:

- `app/graph/state.py`
- `app/graph/nodes.py`
- `app/graph/tools.py`
- `app/graph/graph.py`

If you are building a support copilot, triage bot, internal assistant, or domain-specific retrieval agent, start here.

### `app/graph/state.py`

Add the fields your agent actually needs. The example state tracks:

- `messages`
- `session_id`
- `tenant_id`
- `context`
- `run_id`
- `input_tokens`
- `output_tokens`

For a support agent you might add fields like `customer_id`, `ticket_id`, or `intent`.

### `app/graph/tools.py`

Delete the tools you do not want and add your own. The shipped example includes:

- `web_search`
- `retrieve_documents`

For a real product you usually replace those with tools such as:

- `lookup_customer_profile`
- `fetch_recent_tickets`
- `query_internal_docs`
- `create_handoff_note`

Keep the `TOOLS` list current. That is what gets bound to the model.

### `app/graph/nodes.py`

The example graph has two core steps:

- `retrieve_context`: gather retrieval context before the model call
- `call_model`: invoke the LLM with tools bound

Typical edits:

- change how context is assembled
- inject a domain-specific system prompt
- enforce response structure
- add validation or routing logic before the model step

### `app/graph/graph.py`

The default flow is:

```text
retrieve -> agent -> tools? -> agent -> end
```

Keep that shape if your agent is still a standard tool-calling loop. Change it only when the product behavior genuinely needs more branches or stages.

## 3. Run a real request against your customized graph

Once you have edited the graph files, restart the dev server and send a request:

```bash
curl -X POST http://localhost:8000/v1/agent/run \
  -H "Authorization: Bearer <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-support-1",
    "message": "Summarize the last customer issue and suggest the next action.",
    "stream": false
  }'
```

What you should validate immediately:

- the route authenticates correctly
- the graph executes end-to-end
- your tool wiring is reachable
- the response shape still matches the API contract

## 4. Run the verification loop

Use the built-in quality gates before you trust the customization:

```bash
make lint
make typecheck
make test
```

If you changed graph behavior, pay special attention to:

- `tests/test_graph/`
- `tests/test_services/`
- `tests/test_routers/test_agents.py`

Add or update tests that reflect the new state shape, tool behavior, and expected agent responses.

## 5. What you usually do next

After the first successful run, most teams extend the starter in this order:

1. Replace the example tools with product-specific integrations.
2. Add a domain-specific system prompt and response contract.
3. Add one migration for your first real data table.
4. Add tests for the new graph path before adding more branches.
5. Decide whether you need streaming, multi-tenant auth, or background jobs.

If you can customize those four graph files, run a request, and pass the test suite, you are no longer evaluating the starter. You are building on top of it.
