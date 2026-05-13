# Contributing

This repository is meant to be forked, customized, and improved in the open.
Small, focused pull requests are easier to review and more likely to merge.

## Development Setup

1. Create a virtual environment.
2. Install dependencies with `pip install -e ".[dev]"`.
3. Copy `.env.example` to `.env`.
4. Start PostgreSQL with `make up`.
5. Run migrations with `make migrate`.

## Recommended Workflow

1. Create a branch from `main`.
2. Make one logical change at a time.
3. Run `make lint`, `make typecheck`, and `make test`.
4. Update docs or examples if behavior changed.
5. Open a pull request with a clear summary and verification notes.

## Pull Request Expectations

- Keep PRs narrow in scope.
- Describe the user-visible or maintainer-visible impact.
- Include the commands you ran locally.
- Call out follow-up work instead of mixing it into the same PR.

## Good First Contributions

- Documentation fixes and walkthrough improvements
- Additional tests around router, service, or graph behavior
- Production hardening and deployment guidance
- Example agent improvements that keep the starter generic

## Reporting Problems

Open an issue with:

- What you expected
- What actually happened
- Steps to reproduce
- Environment details that matter

Security-sensitive issues should follow [SECURITY.md](./SECURITY.md).
