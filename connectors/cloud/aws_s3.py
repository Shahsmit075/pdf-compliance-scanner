# connectors/cloud/aws_s3.py
"""
AWS S3 connector — scans object metadata and samples file content.

Metadata approach: List objects with metadata (size, last-modified, content-type).
Data approach: Download only the first 2KB of files for sampling.

Authentication (priority order):
  1. Explicit access_key + secret_key in config
  2. IAM role (EC2/ECS/Lambda)
  3. AWS_PROFILE env variable
  4. Default credentials chain
"""
import logging
from datetime import datetime
from typing import List

from connectors.base.base_connector import (
    BaseConnector, SourceMetadata, TableMeta, ColumnMeta
)

logger = logging.getLogger(__name__)


class S3Connector(BaseConnector):
    """
    S3 connector. Each 'table' maps to an S3 prefix/folder.
    """

    def connect(self) -> bool:
        try:
            import boto3

            session_kwargs = {}
            if self.config.get("access_key"):
                session_kwargs["aws_access_key_id"] = self.config["access_key"]
                session_kwargs["aws_secret_access_key"] = self.config["secret_key"]
            if self.config.get("region"):
                session_kwargs["region_name"] = self.config["region"]
            if self.config.get("profile"):
                session_kwargs["profile_name"] = self.config["profile"]

            session = boto3.Session(**session_kwargs)
            self._s3 = session.client("s3")
            self._bucket = self.config["bucket"]
            return True
        except Exception as e:
            logger.error(f"[{self.source_id}] S3 connection failed: {e}")
            return False

    def disconnect(self) -> None:
        self._s3 = None

    def test_connection(self) -> tuple:
        try:
            self._s3.head_bucket(Bucket=self._bucket)
            return True, f"Connected to bucket: s3://{self._bucket}"
        except Exception as e:
            return False, str(e)

    def get_metadata(self) -> SourceMetadata:
        prefix = self.config.get("prefix", "")
        paginator = self._s3.get_paginator("list_objects_v2")
        tables = []

        try:
            # Get top-level prefixes (treat as tables)
            response = self._s3.list_objects_v2(
                Bucket=self._bucket,
                Prefix=prefix,
                Delimiter="/"
            )
            prefixes = [p["Prefix"] for p in response.get("CommonPrefixes", [])]

            if not prefixes:
                prefixes = [prefix or ""]

            for folder_prefix in prefixes[:50]:
                folder_name = folder_prefix.rstrip("/").split("/")[-1] if folder_prefix else "root"
                objects = []

                for page in paginator.paginate(Bucket=self._bucket, Prefix=folder_prefix):
                    objects.extend(page.get("Contents", []))

                if not objects:
                    continue

                columns = [
                    ColumnMeta(name="key", data_type="string", is_nullable=False),
                    ColumnMeta(name="size_bytes", data_type="integer", is_nullable=False),
                    ColumnMeta(name="content_type", data_type="string", is_nullable=True),
                    ColumnMeta(name="last_modified", data_type="timestamp", is_nullable=False),
                    ColumnMeta(name="etag", data_type="string", is_nullable=False),
                    ColumnMeta(name="storage_class", data_type="string", is_nullable=True),
                ]

                total_size = sum(o.get("Size", 0) for o in objects)
                last_mod = max(o["LastModified"] for o in objects) if objects else None

                tables.append(TableMeta(
                    name=folder_name,
                    schema=self._bucket,
                    columns=columns,
                    row_count=len(objects),
                    size_bytes=total_size,
                    last_modified=last_mod,
                ))

        except Exception as e:
            logger.error(f"[{self.source_id}] S3 metadata failed: {e}")

        return SourceMetadata(
            source_id=self.source_id,
            source_type="s3",
            tables=tables,
            captured_at=datetime.utcnow(),
        )

    def sample_data(self, table: str, column: str, n: int = 100) -> List[str]:
        prefix = self.config.get("prefix", "")
        folder_prefix = f"{prefix}{table}/" if prefix else f"{table}/"
        paginator = self._s3.get_paginator("list_objects_v2")
        samples = []

        for page in paginator.paginate(Bucket=self._bucket, Prefix=folder_prefix):
            for obj in page.get("Contents", []):
                if len(samples) >= n:
                    break
                key = obj["Key"]
                if not any(key.endswith(ext) for ext in [".json", ".csv", ".txt", ".log", ".ndjson"]):
                    continue
                try:
                    response = self._s3.get_object(
                        Bucket=self._bucket, Key=key,
                        Range="bytes=0-2047"
                    )
                    content = response["Body"].read().decode("utf-8", errors="replace")
                    samples.append(content[:500])
                except Exception:
                    continue

        return samples
