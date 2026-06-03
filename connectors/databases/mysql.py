# connectors/databases/mysql.py
"""
MySQL connector — uses pymysql.
Extracts schema metadata from information_schema.
"""
import logging
from typing import List
from datetime import datetime

from connectors.base.base_connector import (
    BaseConnector, SourceMetadata, TableMeta, ColumnMeta
)

logger = logging.getLogger(__name__)


class MySQLConnector(BaseConnector):
    """
    MySQL connector.
    Required config keys: host, port, database, username, password
    """

    def connect(self) -> bool:
        try:
            import pymysql
            self._conn = pymysql.connect(
                host=self.config["host"],
                port=int(self.config.get("port", 3306)),
                database=self.config["database"],
                user=self.config["username"],
                password=self.config["password"],
                connect_timeout=10,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
            return True
        except Exception as e:
            logger.error(f"[{self.source_id}] MySQL connection failed: {e}")
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
                cur.execute("SELECT VERSION()")
                row = cur.fetchone()
                version = row["VERSION()"] if row else "unknown"
            return True, f"Connected: MySQL {version}"
        except Exception as e:
            return False, str(e)

    def get_metadata(self) -> SourceMetadata:
        database = self.config["database"]
        tables = []

        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        TABLE_NAME,
                        TABLE_SCHEMA,
                        DATA_LENGTH + INDEX_LENGTH as size_bytes,
                        TABLE_ROWS as approx_rows
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """, (database,))
                table_rows = cur.fetchall()

                for row in table_rows:
                    table_name = row["TABLE_NAME"]

                    cur.execute("""
                        SELECT
                            COLUMN_NAME,
                            DATA_TYPE,
                            IS_NULLABLE,
                            CHARACTER_MAXIMUM_LENGTH,
                            COLUMN_KEY
                        FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                        ORDER BY ORDINAL_POSITION
                    """, (database, table_name))

                    columns = [
                        ColumnMeta(
                            name=c["COLUMN_NAME"],
                            data_type=c["DATA_TYPE"],
                            is_nullable=(c["IS_NULLABLE"] == "YES"),
                            max_length=c["CHARACTER_MAXIMUM_LENGTH"],
                            is_primary_key=(c["COLUMN_KEY"] == "PRI"),
                        )
                        for c in cur.fetchall()
                    ]

                    tables.append(TableMeta(
                        name=table_name,
                        schema=database,
                        columns=columns,
                        row_count=int(row["approx_rows"] or 0),
                        size_bytes=int(row["size_bytes"] or 0),
                    ))

            return SourceMetadata(
                source_id=self.source_id,
                source_type="mysql",
                tables=tables,
                captured_at=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"[{self.source_id}] MySQL metadata failed: {e}")
            return SourceMetadata(source_id=self.source_id, source_type="mysql", tables=[])

    def sample_data(self, table: str, column: str, n: int = 100) -> List[str]:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    f"SELECT `{column}` FROM `{table}` WHERE `{column}` IS NOT NULL ORDER BY RAND() LIMIT %s",
                    (n,)
                )
                return [str(row[column]) for row in cur.fetchall()]
        except Exception as e:
            logger.warning(f"[{self.source_id}] MySQL sampling failed: {e}")
            return []
