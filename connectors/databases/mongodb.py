# connectors/databases/mongodb.py
"""
MongoDB connector — uses pymongo.
Schema inference via sampling documents (MongoDB is schema-less).
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
from collections import Counter

from connectors.base.base_connector import (
    BaseConnector, SourceMetadata, TableMeta, ColumnMeta
)

logger = logging.getLogger(__name__)

# Max documents to sample for schema inference per collection
SCHEMA_SAMPLE_SIZE = 200


def _infer_type(value: Any) -> str:
    """Map Python type to a descriptive type label."""
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "double"
    elif isinstance(value, str):
        return "string"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    elif isinstance(value, datetime):
        return "date"
    elif value is None:
        return "null"
    return type(value).__name__


def _infer_schema(docs: list) -> Dict[str, ColumnMeta]:
    """
    Infer schema from a sample of documents.
    Returns a dict of field_name -> ColumnMeta.
    Fields present in any document are included; null_count tracked for is_nullable.
    """
    field_types: Dict[str, Counter] = {}
    field_nulls: Dict[str, int] = {}
    total = len(docs)

    for doc in docs:
        for key, value in doc.items():
            if key == "_id":
                continue
            if key not in field_types:
                field_types[key] = Counter()
                field_nulls[key] = 0
            if value is None:
                field_nulls[key] += 1
            else:
                field_types[key][_infer_type(value)] += 1

    columns = {}
    for field, type_counter in field_types.items():
        dominant_type = type_counter.most_common(1)[0][0] if type_counter else "string"
        null_count = field_nulls.get(field, 0)
        columns[field] = ColumnMeta(
            name=field,
            data_type=dominant_type,
            is_nullable=(null_count > 0),
        )

    # Always include _id
    columns["_id"] = ColumnMeta(name="_id", data_type="ObjectId", is_nullable=False, is_primary_key=True)
    return columns


class MongoDBConnector(BaseConnector):
    """
    MongoDB connector.
    Required config keys: host, port, database, username, password
    Optional: auth_source (default 'admin')
    """

    def connect(self) -> bool:
        try:
            from pymongo import MongoClient

            auth_source = self.config.get("auth_source", "admin")
            username = self.config.get("username")
            password = self.config.get("password")

            if username and password:
                uri = (
                    f"mongodb://{username}:{password}@"
                    f"{self.config['host']}:{self.config.get('port', 27017)}/"
                    f"{self.config['database']}?authSource={auth_source}"
                )
            else:
                uri = f"mongodb://{self.config['host']}:{self.config.get('port', 27017)}/"

            self._client = MongoClient(uri, serverSelectionTimeoutMS=10000)
            self._db = self._client[self.config["database"]]
            return True
        except Exception as e:
            logger.error(f"[{self.source_id}] MongoDB connection failed: {e}")
            return False

    def disconnect(self) -> None:
        if hasattr(self, "_client") and self._client:
            self._client.close()

    def test_connection(self) -> tuple:
        try:
            info = self._client.server_info()
            version = info.get("version", "unknown")
            return True, f"Connected: MongoDB {version}"
        except Exception as e:
            return False, str(e)

    def get_metadata(self) -> SourceMetadata:
        tables = []
        try:
            collection_names = self._db.list_collection_names()

            for coll_name in collection_names[:50]:  # Limit to 50 collections
                coll = self._db[coll_name]

                # Sample documents for schema inference
                docs = list(coll.find({}, limit=SCHEMA_SAMPLE_SIZE))
                column_map = _infer_schema(docs) if docs else {
                    "_id": ColumnMeta(name="_id", data_type="ObjectId", is_nullable=False, is_primary_key=True)
                }

                # Approximate count from stats (no COUNT(*) scan)
                try:
                    stats = self._db.command("collStats", coll_name)
                    row_count = stats.get("count", 0)
                    size_bytes = stats.get("totalSize", 0)
                except Exception:
                    row_count = 0
                    size_bytes = 0

                tables.append(TableMeta(
                    name=coll_name,
                    schema=self.config["database"],
                    columns=list(column_map.values()),
                    row_count=row_count,
                    size_bytes=size_bytes,
                ))

        except Exception as e:
            logger.error(f"[{self.source_id}] MongoDB metadata failed: {e}")

        return SourceMetadata(
            source_id=self.source_id,
            source_type="mongodb",
            tables=tables,
            captured_at=datetime.utcnow(),
        )

    def sample_data(self, table: str, column: str, n: int = 100) -> List[str]:
        try:
            coll = self._db[table]
            docs = list(coll.find(
                {column: {"$exists": True, "$ne": None}},
                {column: 1, "_id": 0},
                limit=n
            ))
            return [str(doc.get(column, "")) for doc in docs if doc.get(column) is not None]
        except Exception as e:
            logger.warning(f"[{self.source_id}] MongoDB sampling failed: {e}")
            return []
