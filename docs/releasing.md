# Releasing

This repository is versioned manually on purpose. The goal is a simple release
path that keeps source, tags, and release notes in sync without introducing a
second layer of automation.

## Release Checklist

1. Run `make lint`, `make typecheck`, and `make test`.
2. Confirm `README.md` and docs match the current setup flow.
3. Bump the version in `pyproject.toml` and `app/main.py` if behavior changed.
4. Commit the release changes.
5. Create a tag such as `v0.2.0`.
6. Push the branch and tag to GitHub.

```bash
git tag v0.2.0
git push origin main --follow-tags
```

## What Happens On Tag Push

The `Release` GitHub Actions workflow:

- builds the source distribution and wheel
- creates a GitHub release for the tag
- attaches the built artifacts to the release

## Versioning Guidance

Use pragmatic semver:

- patch: docs fixes, small bug fixes, non-breaking maintenance
- minor: new starter capabilities or meaningful extension points
- major: breaking API or setup changes
