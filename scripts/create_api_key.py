#!/usr/bin/env python3
"""Create a new API key and print it to stdout.

Usage:
    python scripts/create_api_key.py --name "local-dev" --role admin
    make create-key NAME="local-dev" ROLE="admin"
"""

import argparse
import os
import sys

# Ensure the project root is on sys.path when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new API key")
    parser.add_argument("--name", required=True, help="Human-readable name for the key")
    parser.add_argument(
        "--role",
        choices=["user", "admin"],
        default="user",
        help="Role for the key (default: user)",
    )
    parser.add_argument(
        "--tenant-id",
        default="default",
        help="Tenant identifier (default: default)",
    )
    args = parser.parse_args()

    try:
        from app.db.connection import close_pool, init_pool
        from app.services.api_key_service import ApiKeyService

        init_pool()
        service = ApiKeyService()
        plaintext, response = service.create_key(
            name=args.name,
            role=args.role,
            tenant_id=args.tenant_id,
        )
        close_pool()

        print()
        print("API Key Created")
        print("─" * 47)
        print(f"Name:      {response.name}")
        print(f"Role:      {response.role}")
        print(f"Tenant:    {response.tenant_id}")
        print(f"Key ID:    {response.id}")
        print(f"API Key:   {plaintext}")
        print()
        print("Store this key securely. It will not be shown again.")
        print()
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
