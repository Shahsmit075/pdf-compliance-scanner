# connectors/warehouses/databricks.py
"""
Databricks connector — uses databricks-sql-connector.
Supports Unity Catalog (catalog.schema.table) and legacy Hive metastore.
"""
import logging
from typing import List
from datetime import datetime

from connectors.base.base_connector import (
    BaseConnector, SourceMetadata, TableMeta, ColumnMeta
)

logger = logging.getLogger(__name__)


class DatabricksConnector(BaseConnector):
    """
    Databricks connector.
    Required config keys: host, http_path, access_token
    Optional: catalog (default 'hive_metastore'), schema (default 'default')
    """

    def connect(self) -> bool:
        try:
            from databricks import sql as dbsql

            self._conn = dbsql.connect(
                server_hostname=self.config["host"],
                http_path=self.config["http_path"],
                access_token=self.config["access_token"],
            )
            self._catalog = self.config.get("catalog", "hive_metastore")
            self._schema = self.config.get("schema", "default")
            return True
        except Exception as e:
            logger.error(f"[{self.source_id}] Databricks connection failed: {e}")
            return False

    def disconnect(self) -> None:
        if hasattr(self, "_conn") and self._conn:
            try:
                self._conn.close()
            except Exception:
                pass

    def test_connection(self) -> tuple:
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT current_version()")
                version = cur.fetchone()[0]
            return True, f"Connected: Databricks Runtime {version}"
        except Exception as e:
            return False, str(e)

    def get_metadata(self) -> SourceMetadata:
        tables = []

        try:
            with self._conn.cursor() as cur:
                cur.execute(f"SHOW TABLES IN `{self._catalog}`.`{self._schema}`")
                table_rows = cur.fetchall()
                col_names = [desc[0] for desc in cur.description]

                name_idx = col_names.index("tableName") if "tableName" in col_names else 1

                for row in table_rows[:50]:
                    table_name = row[name_idx]
                    try:
                        cur.execute(f"DESCRIBE TABLE `{self._catalog}`.`{self._schema}`.`{table_name}`")
                        col_rows = cur.fetchall()

                        columns = []
                        for col_row in col_rows:
                            col_name = col_row[0]
                            col_type = col_row[1]
                            comment = col_row[2] if len(col_row) > 2 else None

                            if col_name.startswith("#"):  # Partition info header
                                break

                            columns.append(ColumnMeta(
                                name=col_name,
                                data_type=col_type,
                                is_nullable=True,  # Databricks doesn't enforce NOT NULL by default
                                description=comment,
                            ))

                        tables.append(TableMeta(
                            name=table_name,
                            schema=self._schema,
                            columns=columns,
                        ))
                    except Exception as e:
                        logger.warning(f"[{self.source_id}] Could not describe {table_name}: {e}")

        except Exception as e:
            logger.error(f"[{self.source_id}] Databricks metadata failed: {e}")

        return SourceMetadata(
            source_id=self.source_id,
            source_type="databricks",
            tables=tables,
            captured_at=datetime.utcnow(),
        )

    def sample_data(self, table: str, column: str, n: int = 100) -> List[str]:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    f"SELECT `{column}` FROM `{self._catalog}`.`{self._schema}`.`{table}` "
                    f"TABLESAMPLE ({min(10, 100)}  PERCENT) WHERE `{column}` IS NOT NULL LIMIT {n}"
                )
                return [str(row[0]) for row in cur.fetchall()]
        except Exception as e:
            logger.warning(f"[{self.source_id}] Databricks sampling failed: {e}")
            return []
