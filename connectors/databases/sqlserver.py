# connectors/databases/sqlserver.py
"""
SQL Server connector — uses pyodbc.
"""
import logging
from typing import List
from datetime import datetime

from connectors.base.base_connector import (
    BaseConnector, SourceMetadata, TableMeta, ColumnMeta
)

logger = logging.getLogger(__name__)


class SQLServerConnector(BaseConnector):
    """
    SQL Server connector.
    Required config keys: host, port, database, username, password
    Optional: driver (default 'ODBC Driver 17 for SQL Server'), schema (default 'dbo')
    """

    def connect(self) -> bool:
        try:
            import pyodbc
            driver = self.config.get("driver", "ODBC Driver 17 for SQL Server")
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={self.config['host']},{self.config.get('port', 1433)};"
                f"DATABASE={self.config['database']};"
                f"UID={self.config['username']};"
                f"PWD={self.config['password']};"
                "Connection Timeout=10;"
            )
            self._conn = pyodbc.connect(conn_str)
            return True
        except Exception as e:
            logger.error(f"[{self.source_id}] SQL Server connection failed: {e}")
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
            cur.execute("SELECT @@VERSION")
            version = cur.fetchone()[0][:80]
            return True, f"Connected: {version}"
        except Exception as e:
            return False, str(e)

    def get_metadata(self) -> SourceMetadata:
        target_schema = self.config.get("schema", "dbo")
        tables = []

        try:
            cur = self._conn.cursor()

            cur.execute("""
                SELECT
                    t.TABLE_NAME,
                    t.TABLE_SCHEMA,
                    p.rows AS approx_rows
                FROM INFORMATION_SCHEMA.TABLES t
                LEFT JOIN sys.partitions p
                    ON p.object_id = OBJECT_ID(t.TABLE_SCHEMA + '.' + t.TABLE_NAME)
                    AND p.index_id IN (0, 1)
                WHERE t.TABLE_SCHEMA = ? AND t.TABLE_TYPE = 'BASE TABLE'
                ORDER BY t.TABLE_NAME
            """, target_schema)

            table_rows = cur.fetchall()

            for table_name, schema, approx_rows in table_rows:
                cur.execute("""
                    SELECT
                        c.COLUMN_NAME,
                        c.DATA_TYPE,
                        c.IS_NULLABLE,
                        c.CHARACTER_MAXIMUM_LENGTH,
                        CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END AS is_pk
                    FROM INFORMATION_SCHEMA.COLUMNS c
                    LEFT JOIN (
                        SELECT ku.COLUMN_NAME
                        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                            ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                        WHERE tc.TABLE_NAME = ? AND tc.TABLE_SCHEMA = ?
                          AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                    ) pk ON pk.COLUMN_NAME = c.COLUMN_NAME
                    WHERE c.TABLE_NAME = ? AND c.TABLE_SCHEMA = ?
                    ORDER BY c.ORDINAL_POSITION
                """, table_name, target_schema, table_name, target_schema)

                columns = [
                    ColumnMeta(
                        name=row[0],
                        data_type=row[1],
                        is_nullable=(row[2] == "YES"),
                        max_length=row[3],
                        is_primary_key=bool(row[4]),
                    )
                    for row in cur.fetchall()
                ]

                tables.append(TableMeta(
                    name=table_name,
                    schema=schema,
                    columns=columns,
                    row_count=int(approx_rows or 0),
                ))

        except Exception as e:
            logger.error(f"[{self.source_id}] SQL Server metadata failed: {e}")

        return SourceMetadata(
            source_id=self.source_id,
            source_type="sqlserver",
            tables=tables,
            captured_at=datetime.utcnow(),
        )

    def sample_data(self, table: str, column: str, n: int = 100) -> List[str]:
        schema = self.config.get("schema", "dbo")
        try:
            cur = self._conn.cursor()
            cur.execute(
                f"SELECT TOP {n} [{column}] FROM [{schema}].[{table}] "
                f"WHERE [{column}] IS NOT NULL ORDER BY NEWID()"
            )
            return [str(row[0]) for row in cur.fetchall()]
        except Exception as e:
            logger.warning(f"[{self.source_id}] SQL Server sampling failed: {e}")
            return []
