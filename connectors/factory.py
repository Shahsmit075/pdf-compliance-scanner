# connectors/factory.py
"""
ConnectorFactory — creates the right connector from a source configuration.

Design: Factory + Registry pattern.
Adding a new connector = register it in the REGISTRY dict. Nothing else changes.
"""
import importlib
from typing import Type, Dict
from connectors.base.base_connector import BaseConnector


# Registry of all available connectors
# Keys: source_type values stored in data_sources.source_type
CONNECTOR_REGISTRY: Dict[str, str] = {
    "postgres":   "connectors.databases.postgres.PostgresConnector",
    "mysql":      "connectors.databases.mysql.MySQLConnector",
    "mongodb":    "connectors.databases.mongodb.MongoDBConnector",
    "sqlserver":  "connectors.databases.sqlserver.SQLServerConnector",
    "s3":         "connectors.cloud.aws_s3.S3Connector",
    "azure_adls": "connectors.cloud.azure_adls.ADLSConnector",
    "gcs":        "connectors.cloud.gcp_gcs.GCSConnector",
    "snowflake":  "connectors.warehouses.snowflake.SnowflakeConnector",
    "bigquery":   "connectors.warehouses.bigquery.BigQueryConnector",
    "databricks": "connectors.warehouses.databricks.DatabricksConnector",
}

# Human-friendly display metadata for each connector type
CONNECTOR_META: Dict[str, dict] = {
    "postgres":   {"label": "PostgreSQL",        "icon": "🐘", "category": "Database"},
    "mysql":      {"label": "MySQL",             "icon": "🐬", "category": "Database"},
    "mongodb":    {"label": "MongoDB",           "icon": "🍃", "category": "Database"},
    "sqlserver":  {"label": "SQL Server",        "icon": "🔷", "category": "Database"},
    "s3":         {"label": "AWS S3",            "icon": "🪣", "category": "Cloud Storage"},
    "azure_adls": {"label": "Azure ADLS Gen2",  "icon": "☁️", "category": "Cloud Storage"},
    "gcs":        {"label": "Google Cloud Storage", "icon": "🌐", "category": "Cloud Storage"},
    "snowflake":  {"label": "Snowflake",         "icon": "❄️", "category": "Data Warehouse"},
    "bigquery":   {"label": "BigQuery",          "icon": "🔍", "category": "Data Warehouse"},
    "databricks": {"label": "Databricks",        "icon": "🧱", "category": "Data Warehouse"},
}

# Required config fields per connector type (for UI form generation)
CONNECTOR_FIELDS: Dict[str, list] = {
    "postgres":   ["host", "port", "database", "username", "password", "schema"],
    "mysql":      ["host", "port", "database", "username", "password"],
    "mongodb":    ["host", "port", "database", "username", "password", "auth_source"],
    "sqlserver":  ["host", "port", "database", "username", "password"],
    "s3":         ["bucket", "region", "prefix", "access_key", "secret_key"],
    "azure_adls": ["account_name", "account_key", "container", "directory_path"],
    "gcs":        ["project_id", "bucket", "prefix", "credentials_json"],
    "snowflake":  ["account", "user", "password", "database", "schema", "warehouse", "role"],
    "bigquery":   ["project_id", "dataset", "credentials_json"],
    "databricks": ["host", "http_path", "access_token", "catalog", "schema"],
}

# Password/secret fields (redacted in UI)
SECRET_FIELDS = {"password", "secret_key", "access_key", "account_key", "access_token",
                 "credentials_json", "api_key"}


class ConnectorFactory:
    """
    Creates connector instances from config dict.
    Secrets are resolved through SecretManager before being passed to connectors.
    """

    @staticmethod
    def create(source_id: str, config: dict) -> BaseConnector:
        """
        Create and return the appropriate connector.

        Args:
            source_id: Unique source identifier from database
            config: Dict with 'type' and connection parameters

        Raises:
            ValueError: If source_type is not registered
            ImportError: If connector module is not installed
        """
        source_type = config.get("type", "").lower()

        if source_type not in CONNECTOR_REGISTRY:
            available = ", ".join(CONNECTOR_REGISTRY.keys())
            raise ValueError(
                f"Unknown source type '{source_type}'. Available: {available}"
            )

        module_path, class_name = CONNECTOR_REGISTRY[source_type].rsplit(".", 1)

        try:
            module = importlib.import_module(module_path)
            connector_class: Type[BaseConnector] = getattr(module, class_name)
        except ImportError as e:
            raise ImportError(
                f"Connector for '{source_type}' requires additional packages. "
                f"Install from requirements.txt\nOriginal error: {e}"
            )

        return connector_class(source_id=source_id, config=config)

    @staticmethod
    def list_supported() -> list:
        return list(CONNECTOR_REGISTRY.keys())

    @staticmethod
    def get_meta(source_type: str) -> dict:
        return CONNECTOR_META.get(source_type, {"label": source_type, "icon": "🔌", "category": "Unknown"})

    @staticmethod
    def get_fields(source_type: str) -> list:
        return CONNECTOR_FIELDS.get(source_type, [])
