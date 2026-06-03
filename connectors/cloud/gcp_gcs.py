# connectors/cloud/gcp_gcs.py
"""
Google Cloud Storage connector.
Uses google-cloud-storage SDK.
"""
import logging
import json
from typing import List
from datetime import datetime

from connectors.base.base_connector import (
    BaseConnector, SourceMetadata, TableMeta, ColumnMeta
)

logger = logging.getLogger(__name__)


class GCSConnector(BaseConnector):
    """
    Google Cloud Storage connector.
    Required config keys: project_id, bucket
    Optional: prefix, credentials_json (service account JSON string)
    """

    def connect(self) -> bool:
        try:
            from google.cloud import storage
            from google.oauth2 import service_account

            creds_json = self.config.get("credentials_json")
            if creds_json:
                if isinstance(creds_json, str):
                    creds_dict = json.loads(creds_json)
                else:
                    creds_dict = creds_json
                credentials = service_account.Credentials.from_service_account_info(creds_dict)
                self._client = storage.Client(
                    project=self.config["project_id"],
                    credentials=credentials,
                )
            else:
                # Use Application Default Credentials
                self._client = storage.Client(project=self.config["project_id"])

            self._bucket = self._client.bucket(self.config["bucket"])
            return True
        except Exception as e:
            logger.error(f"[{self.source_id}] GCS connection failed: {e}")
            return False

    def disconnect(self) -> None:
        self._client = None

    def test_connection(self) -> tuple:
        try:
            if self._bucket.exists():
                return True, f"Connected to: gs://{self.config['bucket']}"
            return False, f"Bucket {self.config['bucket']} not found"
        except Exception as e:
            return False, str(e)

    def get_metadata(self) -> SourceMetadata:
        prefix = self.config.get("prefix", "")
        tables = []

        try:
            # Get top-level prefixes (virtual directories)
            iterator = self._client.list_blobs(
                self._bucket,
                prefix=prefix,
                delimiter="/"
            )
            # Exhaust iterator to populate prefixes
            list(iterator)
            prefixes = list(iterator.prefixes) if hasattr(iterator, "prefixes") else []

            if not prefixes:
                prefixes = [prefix or ""]

            for folder_prefix in prefixes[:50]:
                folder_name = folder_prefix.rstrip("/").split("/")[-1] if folder_prefix else "root"

                blobs = list(self._client.list_blobs(self._bucket, prefix=folder_prefix))
                if not blobs:
                    continue

                columns = [
                    ColumnMeta(name="name", data_type="string", is_nullable=False),
                    ColumnMeta(name="size", data_type="integer", is_nullable=False),
                    ColumnMeta(name="content_type", data_type="string", is_nullable=True),
                    ColumnMeta(name="updated", data_type="timestamp", is_nullable=False),
                    ColumnMeta(name="storage_class", data_type="string", is_nullable=True),
                    ColumnMeta(name="md5_hash", data_type="string", is_nullable=True),
                ]

                total_size = sum(b.size or 0 for b in blobs)
                last_mod = max((b.updated for b in blobs if b.updated), default=None)

                tables.append(TableMeta(
                    name=folder_name,
                    schema=self.config["bucket"],
                    columns=columns,
                    row_count=len(blobs),
                    size_bytes=total_size,
                    last_modified=last_mod,
                ))

        except Exception as e:
            logger.error(f"[{self.source_id}] GCS metadata failed: {e}")

        return SourceMetadata(
            source_id=self.source_id,
            source_type="gcs",
            tables=tables,
            captured_at=datetime.utcnow(),
        )

    def sample_data(self, table: str, column: str, n: int = 100) -> List[str]:
        prefix = self.config.get("prefix", "")
        folder = f"{prefix}{table}/" if prefix else f"{table}/"
        samples = []

        try:
            blobs = list(self._client.list_blobs(self._bucket, prefix=folder))
            for blob in blobs[:n]:
                name = blob.name
                if not any(name.endswith(ext) for ext in [".json", ".csv", ".txt", ".log"]):
                    continue
                try:
                    content = blob.download_as_bytes(start=0, end=2047).decode("utf-8", errors="replace")
                    samples.append(content[:500])
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"[{self.source_id}] GCS sampling failed: {e}")

        return samples
