# connectors/secrets/secret_manager.py
"""
Secret manager abstraction — resolves credentials from:
  1. Environment variables (default for local dev)
  2. .env file
  3. HashiCorp Vault (production)
  4. AWS Secrets Manager (AWS production)
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SecretManager:
    """Resolves secret references to actual values."""

    SUPPORTED_SCHEMES = ["env", "vault", "aws_sm", "plain"]

    @staticmethod
    def resolve(secret_ref: str) -> Optional[str]:
        """
        Resolve a secret reference to its actual value.

        Reference formats:
            env://MY_SECRET_KEY         → os.getenv("MY_SECRET_KEY")
            vault://secret/path:key     → Vault KV lookup
            aws_sm://my-secret-name     → AWS Secrets Manager
            plain://actual_value        → Plaintext (dev only)

        If secret_ref has no scheme prefix, treated as env:// by default.
        """
        if not secret_ref:
            return None

        if "://" not in secret_ref:
            return os.getenv(secret_ref)

        scheme, path = secret_ref.split("://", 1)

        if scheme == "env":
            value = os.getenv(path)
            if not value:
                logger.warning(f"Environment variable '{path}' not set")
            return value

        elif scheme == "plain":
            logger.warning("Using plaintext secret — only acceptable in development!")
            return path

        elif scheme == "vault":
            return SecretManager._resolve_vault(path)

        elif scheme == "aws_sm":
            return SecretManager._resolve_aws_sm(path)

        else:
            raise ValueError(f"Unknown secret scheme: {scheme}. "
                             f"Supported: {SecretManager.SUPPORTED_SCHEMES}")

    @staticmethod
    def _resolve_vault(path: str) -> Optional[str]:
        """Resolve from HashiCorp Vault."""
        try:
            import hvac
            vault_url = os.getenv("VAULT_ADDR", "http://localhost:8200")
            vault_token = os.getenv("VAULT_TOKEN")
            client = hvac.Client(url=vault_url, token=vault_token)
            secret_path, key = path.rsplit(":", 1) if ":" in path else (path, "value")
            response = client.secrets.kv.read_secret_version(path=secret_path)
            return response["data"]["data"].get(key)
        except Exception as e:
            logger.error(f"Vault resolution failed for {path}: {e}")
            return None

    @staticmethod
    def _resolve_aws_sm(secret_name: str) -> Optional[str]:
        """Resolve from AWS Secrets Manager."""
        try:
            import boto3
            import json as json_lib
            client = boto3.client("secretsmanager")
            response = client.get_secret_value(SecretId=secret_name)
            secret = response.get("SecretString", "{}")
            parsed = json_lib.loads(secret)
            return parsed.get("value", secret)
        except Exception as e:
            logger.error(f"AWS SM resolution failed for {secret_name}: {e}")
            return None

    @staticmethod
    def resolve_config(config: dict) -> dict:
        """
        Resolve all secret references in a config dict.
        Keys ending in '_ref' are resolved and stored without the '_ref' suffix.
        """
        resolved = dict(config)
        to_delete = []
        for key, value in list(config.items()):
            if key.endswith("_ref") and isinstance(value, str):
                real_key = key[:-4]
                resolved[real_key] = SecretManager.resolve(value)
                to_delete.append(key)
        for key in to_delete:
            del resolved[key]
        return resolved
