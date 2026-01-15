#!/usr/bin/env python3
import argparse
import getpass
import os
import secrets
import sys
from typing import Dict, Any

import yaml

try:
    import streamlit_authenticator as stauth
except Exception as exc:  # pragma: no cover - runtime dependency
    raise SystemExit(
        "streamlit-authenticator is required. Install dependencies and rerun."
    ) from exc


def build_config(
    username: str,
    name: str,
    email: str,
    password: str,
    cookie_name: str,
    cookie_key: str,
    expiry_days: int,
) -> Dict[str, Any]:
    hashed_password = stauth.Hasher([password]).generate()[0]
    return {
        "credentials": {
            "usernames": {
                username: {
                    "email": email,
                    "name": name,
                    "password": hashed_password,
                }
            }
        },
        "cookie": {
            "expiry_days": expiry_days,
            "key": cookie_key,
            "name": cookie_name,
        },
        "preauthorized": {"emails": []},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize config.local.yaml")
    parser.add_argument("--output", default="src/core/config/config.local.yaml")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--name", default="Admin User")
    parser.add_argument("--email", default="admin@example.com")
    parser.add_argument("--password")
    parser.add_argument("--cookie-name", default="dlc_webui_cookie")
    parser.add_argument("--cookie-key")
    parser.add_argument("--expiry-days", type=int, default=30)
    parser.add_argument("--force", action="store_true", help="Overwrite existing file")
    args = parser.parse_args()

    output_path = os.path.abspath(args.output)
    if os.path.exists(output_path) and not args.force:
        print(f"Config already exists: {output_path}")
        print("Use --force to overwrite.")
        return 1

    password = args.password
    if not password:
        password = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match.")
            return 1

    cookie_key = args.cookie_key or secrets.token_urlsafe(32)

    config = build_config(
        username=args.username,
        name=args.name,
        email=args.email,
        password=password,
        cookie_name=args.cookie_name,
        cookie_key=cookie_key,
        expiry_days=args.expiry_days,
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)

    try:
        os.chmod(output_path, 0o600)
    except OSError:
        pass

    print(f"Config written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
