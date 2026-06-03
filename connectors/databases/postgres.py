# connectors/databases/postgres.py
"""
PostgreSQL connector — uses psycopg2 with connection pooling.
Extracts schema metadata from information_schema (no row reads).
"""
import logging
from typing import List
from datetime import datetime

from connectors.base.base_connector import (
    BaseConnector, SourceMetadata, TableMeta, ColumnMeta
)

logger = logging.getLogger(__name__)


class PostgresConnector(BaseConnector):
    """
    PostgreSQL connector.

    Required config keys:
        host, port, database, username, password
    Optional:
        schema (default 'public'), ssl_mode (default 'prefer')
    """

    def connect(self) -> bool:
        try:
            import psycopg2
            from psycopg2 import pool as pg_pool

            self._pool = pg_pool.SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                host=self.config["host"],
                port=self.config.get("port", 5432),
                database=self.config["database"],
                user=self.config["username"],
                password=self.config["password"],
                connect_timeout=10,
                sslmode=self.config.get("ssl_mode", "prefer"),
            )
            return True
        except Exception as e:
            logger.error(f"[{self.source_id}] PostgreSQL connection failed: {e}")
            return False

    def disconnect(self) -> None:
        if hasattr(self, "_pool") and self._pool:
            self._pool.closeall()

    def test_connection(self) -> tuple:
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
            self._pool.putconn(conn)
            return True, f"Connected: {version[:60]}"
        except Exception as e:
            return False, str(e)

    def _get_conn(self):
        return self._pool.getconn()

    def _release_conn(self, conn):
        self._pool.putconn(conn)

    def get_metadata(self) -> SourceMetadata:
        conn = self._get_conn()
        try:
            target_schema = self.config.get("schema", "public")
            tables = []

            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        t.table_name,
                        t.table_schema,
                        pg_total_relation_size(pgc.oid) as size_bytes,
                        GREATEST(pgc.reltuples::bigint, 0) as approx_row_count,
                        pg_postmaster_start_time()::text as version
                    FROM information_schema.tables t
                    JOIN pg_class pgc ON pgc.relname = t.table_name
                    JOIN pg_namespace pgn ON pgn.oid = pgc.relnamespace
                        AND pgn.nspname = t.table_schema
                    WHERE t.table_schema = %s
                      AND t.table_type = 'BASE TABLE'
                    ORDER BY t.table_name
                """, (target_schema,))

                table_rows = cur.fetchall()
                db_version = None

                for table_name, schema, size_bytes, approx_rows, ver in table_rows:
                    if db_version is None:
                        try:
                            cur.execute("SELECT version()")
                            db_version = cur.fetchone()[0][:80]
                        except Exception:
                            pass

                    cur.execute("""
                        SELECT
                            c.column_name,
                            c.data_type,
                            c.is_nullable,
                            c.character_maximum_length,
                            CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_pk
                        FROM information_schema.columns c
                        LEFT JOIN (
                            SELECT ku.column_name
                            FROM information_schema.table_constraints tc
                            JOIN information_schema.key_column_usage ku
                                ON tc.constraint_name = ku.constraint_name
                                AND tc.table_schema = ku.table_schema
                            WHERE tc.table_name = %s
                              AND tc.table_schema = %s
                              AND tc.constraint_type = 'PRIMARY KEY'
                        ) pk ON pk.column_name = c.column_name
                        WHERE c.table_name = %s AND c.table_schema = %s
                        ORDER BY c.ordinal_position
                    """, (table_name, target_schema, table_name, target_schema))

                    columns = [
                        ColumnMeta(
                            name=col_name,
                            data_type=data_type,
                            is_nullable=(is_nullable == "YES"),
                            max_length=max_len,
                            is_primary_key=bool(is_pk),
                        )
                        for col_name, data_type, is_nullable, max_len, is_pk
                        in cur.fetchall()
                    ]

                    tables.append(TableMeta(
                        name=table_name,
                        schema=schema,
                        columns=columns,
                        row_count=max(0, approx_rows or 0),
                        size_bytes=size_bytes,
                    ))

            return SourceMetadata(
                source_id=self.source_id,
                source_type="postgres",
                tables=tables,
                captured_at=datetime.utcnow(),
                database_version=db_version,
            )

        finally:
            self._release_conn(conn)

    def sample_data(self, table: str, column: str, n: int = 100) -> List[str]:
        conn = self._get_conn()
        schema = self.config.get("schema", "public")
        try:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT "{column}"::text
                    FROM "{schema}"."{table}" TABLESAMPLE BERNOULLI(10)
                    WHERE "{column}" IS NOT NULL
                    LIMIT %s
                """, (n,))
                rows = cur.fetchall()
                return [str(row[0]) for row in rows if row[0] is not None]
        except Exception as e:
            logger.warning(f"[{self.source_id}] Sampling failed for {table}.{column}: {e}")
            return []
        finally:
            self._release_conn(conn)

    def get_table_stats(self, table: str) -> dict:
        conn = self._get_conn()
        schema = self.config.get("schema", "public")
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT attname, null_frac, n_distinct, correlation
                    FROM pg_stats
                    WHERE schemaname = %s AND tablename = %s
                """, (schema, table))
                return {
                    row[0]: {
                        "null_frac": row[1],
                        "n_distinct": row[2],
                        "correlation": row[3]
                    }
                    for row in cur.fetchall()
                }
        except Exception:
            return {}
        finally:
            self._release_conn(conn)
