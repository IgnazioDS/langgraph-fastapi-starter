#!/usr/bin/env python3
"""Minimal health check. Used as Docker HEALTHCHECK command.

Exit 0 if the server responds with status="ok". Exit 1 otherwise.

Usage:
    python scripts/health_check.py
"""

import sys
import urllib.error
import urllib.request


def main() -> int:
    try:
        with urllib.request.urlopen("http://localhost:8000/health", timeout=5) as resp:
            import json
            body = json.loads(resp.read())
            if body.get("status") == "ok":
                return 0
            print(f"Unhealthy: {body}", file=sys.stderr)
            return 1
    except urllib.error.URLError as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Health check error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
