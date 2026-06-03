# connectors/warehouses/snowflake.py
"""
Snowflake connector — uses snowflake-connector-python.
Uses INFORMATION_SCHEMA for metadata extraction (no data reads).
"""
import logging
from typing import List
from datetime import datetime

from connectors.base.base_connector import (
    BaseConnector, SourceMetadata, TableMeta, ColumnMeta
)

logger = logging.getLogger(__name__)


class SnowflakeConnector(BaseConnector):
    """
    Snowflake connector.
    Required config keys: account, user, password, database, schema, warehouse
    Optional: role
    """

    def connect(self) -> bool:
        try:
            import snowflake.connector

            conn_kwargs = {
                "account": self.config["account"],
                "user": self.config["user"],
                "password": self.config["password"],
                "database": self.config["database"],
                "schema": self.config.get("schema", "PUBLIC"),
                "warehouse": self.config["warehouse"],
            }
            if self.config.get("role"):
                conn_kwargs["role"] = self.config["role"]

            self._conn = snowflake.connector.connect(**conn_kwargs)
            return True
        except Exception as e:
            logger.error(f"[{self.source_id}] Snowflake connection failed: {e}")
            return False

    def disconnect(self) -> None:
        if hasattr(self, "_conn") and self._conn:
            try:
                self._conn.close()
            except Exception:
                pass

    def test_connection(self) -> tuple:
        try:
            cur = self._conn.cursor()
            cur.execute("SELECT CURRENT_VERSION()")
            version = cur.fetchone()[0]
            return True, f"Connected: Snowflake {version}"
        except Exception as e:
            return False, str(e)

    def get_metadata(self) -> SourceMetadata:
        database = self.config["database"]
        schema = self.config.get("schema", "PUBLIC")
        tables = []

        try:
            cur = self._conn.cursor()

            cur.execute(f"""
                SELECT
                    TABLE_NAME,
                    TABLE_SCHEMA,
                    ROW_COUNT,
                    BYTES
                FROM {database}.INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """, (schema,))

            table_rows = cur.fetchall()

            for table_name, tbl_schema, row_count, size_bytes in table_rows:
                cur.execute(f"""
                    SELECT
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE,
                        CHARACTER_MAXIMUM_LENGTH
                    FROM {database}.INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (schema, table_name))

                columns = [
                    ColumnMeta(
                        name=row[0],
                        data_type=row[1],
                        is_nullable=(row[2] == "YES"),
                        max_length=row[3],
                    )
                    for row in cur.fetchall()
                ]

                tables.append(TableMeta(
                    name=table_name,
                    schema=tbl_schema,
                    columns=columns,
                    row_count=int(row_count or 0),
                    size_bytes=int(size_bytes or 0),
                ))

        except Exception as e:
            logger.error(f"[{self.source_id}] Snowflake metadata failed: {e}")

        return SourceMetadata(
            source_id=self.source_id,
            source_type="snowflake",
            tables=tables,
            captured_at=datetime.utcnow(),
        )

    def sample_data(self, table: str, column: str, n: int = 100) -> List[str]:
        schema = self.config.get("schema", "PUBLIC")
        database = self.config["database"]
        try:
            cur = self._conn.cursor()
            cur.execute(
                f'SELECT "{column}" FROM "{database}"."{schema}"."{table}" '
                f'SAMPLE BERNOULLI (5) WHERE "{column}" IS NOT NULL LIMIT %s',
                (n,)
            )
            return [str(row[0]) for row in cur.fetchall()]
        except Exception as e:
            logger.warning(f"[{self.source_id}] Snowflake sampling failed: {e}")
            return []
