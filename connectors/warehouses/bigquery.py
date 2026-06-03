# connectors/warehouses/bigquery.py
"""
Google BigQuery connector — uses google-cloud-bigquery.
"""
import logging
import json
from typing import List
from datetime import datetime

from connectors.base.base_connector import (
    BaseConnector, SourceMetadata, TableMeta, ColumnMeta
)

logger = logging.getLogger(__name__)

# BigQuery → generic type mapping
BQ_TYPE_MAP = {
    "STRING": "string",
    "BYTES": "bytes",
    "INTEGER": "integer",
    "INT64": "integer",
    "FLOAT": "float",
    "FLOAT64": "float",
    "NUMERIC": "numeric",
    "BIGNUMERIC": "numeric",
    "BOOLEAN": "boolean",
    "BOOL": "boolean",
    "TIMESTAMP": "timestamp",
    "DATE": "date",
    "TIME": "time",
    "DATETIME": "datetime",
    "GEOGRAPHY": "geography",
    "RECORD": "object",
    "STRUCT": "object",
    "JSON": "json",
}


class BigQueryConnector(BaseConnector):
    """
    BigQuery connector.
    Required config keys: project_id, dataset
    Optional: credentials_json (service account JSON string)
    """

    def connect(self) -> bool:
        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account

            creds_json = self.config.get("credentials_json")
            if creds_json:
                if isinstance(creds_json, str):
                    creds_dict = json.loads(creds_json)
                else:
                    creds_dict = creds_json
                credentials = service_account.Credentials.from_service_account_info(creds_dict)
                self._client = bigquery.Client(
                    project=self.config["project_id"],
                    credentials=credentials,
                )
            else:
                self._client = bigquery.Client(project=self.config["project_id"])

            self._dataset = self.config["dataset"]
            return True
        except Exception as e:
            logger.error(f"[{self.source_id}] BigQuery connection failed: {e}")
            return False

    def disconnect(self) -> None:
        if hasattr(self, "_client"):
            self._client.close()

    def test_connection(self) -> tuple:
        try:
            from google.cloud.bigquery import DatasetReference
            dataset_ref = DatasetReference(self.config["project_id"], self._dataset)
            self._client.get_dataset(dataset_ref)
            return True, f"Connected: {self.config['project_id']}.{self._dataset}"
        except Exception as e:
            return False, str(e)

    def get_metadata(self) -> SourceMetadata:
        project_id = self.config["project_id"]
        dataset_id = self._dataset
        tables = []

        try:
            from google.cloud.bigquery import DatasetReference
            dataset_ref = DatasetReference(project_id, dataset_id)
            table_list = list(self._client.list_tables(dataset_ref))

            for table_item in table_list[:50]:
                table_ref = self._client.get_table(table_item.reference)

                columns = [
                    ColumnMeta(
                        name=field.name,
                        data_type=BQ_TYPE_MAP.get(field.field_type, field.field_type.lower()),
                        is_nullable=(field.mode != "REQUIRED"),
                        description=field.description,
                    )
                    for field in table_ref.schema
                ]

                tables.append(TableMeta(
                    name=table_item.table_id,
                    schema=dataset_id,
                    columns=columns,
                    row_count=table_ref.num_rows,
                    size_bytes=table_ref.num_bytes,
                    last_modified=table_ref.modified,
                ))

        except Exception as e:
            logger.error(f"[{self.source_id}] BigQuery metadata failed: {e}")

        return SourceMetadata(
            source_id=self.source_id,
            source_type="bigquery",
            tables=tables,
            captured_at=datetime.utcnow(),
        )

    def sample_data(self, table: str, column: str, n: int = 100) -> List[str]:
        project_id = self.config["project_id"]
        dataset_id = self._dataset
        try:
            query = (
                f"SELECT `{column}` FROM `{project_id}.{dataset_id}.{table}` "
                f"WHERE `{column}` IS NOT NULL LIMIT {n}"
            )
            results = self._client.query(query).result()
            return [str(row[0]) for row in results]
        except Exception as e:
            logger.warning(f"[{self.source_id}] BigQuery sampling failed: {e}")
            return []
