# Contributing

Thanks for helping make this starter more useful to AI engineers.

By participating, you agree to follow the project's [Code of Conduct](./CODE_OF_CONDUCT.md).

The project is intentionally small and explicit. Contributions should strengthen the
reusable backend foundation without turning it into a platform or hiding important
decisions behind abstractions.

## Before you start

- Search existing [issues](https://github.com/IgnazioDS/langgraph-fastapi-starter/issues)
  and [discussions](https://github.com/IgnazioDS/langgraph-fastapi-starter/discussions).
- Open a discussion before starting a large feature, new infrastructure dependency, or
  public API change.
- Keep product-specific integrations optional and easy to remove.
- Never include credentials, customer data, or real API keys in examples, logs, or tests.

## Local setup

```bash
git clone https://github.com/IgnazioDS/langgraph-fastapi-starter.git
cd langgraph-fastapi-starter
cp .env.example .env

# Set OPENAI_API_KEY and POSTGRES_PASSWORD in .env
make install
make up
make migrate
```

Create a focused branch:

```bash
git switch -c fix/short-description
# or
git switch -c feat/short-description
```

## Quality checks

Run the same checks used by CI:

```bash
make lint
make typecheck
make test
```

When behavior changes, add or update the smallest relevant tests. Documentation-only
changes should still keep code samples, filenames, and public endpoints accurate.

## Pull requests

A strong pull request:

- solves one clearly described problem;
- explains the user or developer impact;
- keeps unrelated refactors out of the diff;
- includes tests for changed behavior;
- updates documentation and configuration examples when needed;
- calls out new dependencies, migrations, or compatibility risks.

Draft pull requests are welcome when early architectural feedback would prevent wasted
work.

## Scope guidance

Usually in scope:

- correctness and security fixes;
- focused FastAPI, LangGraph, PostgreSQL, or developer-experience improvements;
- better tests, examples, deployment guidance, and documentation;
- optional integrations with a small maintenance footprint.

Usually better as a discussion or separate project:

- a bundled frontend or admin dashboard;
- provider-specific product logic;
- mandatory observability, queueing, or cloud platforms;
- large abstractions that make the request path harder to follow.

## License

By submitting a contribution, you agree that it may be distributed under the
[MIT License](./LICENSE).
