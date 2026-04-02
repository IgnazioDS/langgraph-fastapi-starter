#!/usr/bin/env python3
"""Revoke an API key by its UUID.

Usage:
    python scripts/revoke_api_key.py --id "3f2a1b4c-..."
    python scripts/revoke_api_key.py --id "3f2a1b4c-..." --yes
    make revoke-key ID="3f2a1b4c-..."
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main() -> int:
    parser = argparse.ArgumentParser(description="Revoke an API key by UUID")
    parser.add_argument("--id", required=True, help="UUID of the key to revoke")
    parser.add_argument(
        "--yes", action="store_true", help="Skip confirmation prompt"
    )
    args = parser.parse_args()

    if not args.yes:
        confirm = input(f"Revoke key {args.id}? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return 0

    try:
        from app.db.connection import close_pool, init_pool
        from app.services.api_key_service import ApiKeyService

        init_pool()
        service = ApiKeyService()
        revoked = service.revoke_key(args.id, tenant_id="default")
        close_pool()

        if revoked:
            print(f"Key {args.id} revoked.")
            return 0
        else:
            print(f"Key {args.id} not found or already revoked.", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
