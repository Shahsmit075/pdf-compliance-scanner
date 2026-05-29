# connectors/cloud/azure_adls.py
"""
Azure Data Lake Storage Gen2 connector.
Uses azure-storage-file-datalake SDK.
"""
import logging
from typing import List
from datetime import datetime

from connectors.base.base_connector import (
    BaseConnector, SourceMetadata, TableMeta, ColumnMeta
)

logger = logging.getLogger(__name__)


class ADLSConnector(BaseConnector):
    """
    Azure ADLS Gen2 connector.
    Required config keys: account_name, account_key, container
    Optional: directory_path (root prefix)
    """

    def connect(self) -> bool:
        try:
            from azure.storage.filedatalake import DataLakeServiceClient

            self._service = DataLakeServiceClient(
                account_url=f"https://{self.config['account_name']}.dfs.core.windows.net",
                credential=self.config["account_key"],
            )
            self._container = self.config["container"]
            self._fs = self._service.get_file_system_client(self._container)
            return True
        except Exception as e:
            logger.error(f"[{self.source_id}] ADLS connection failed: {e}")
            return False

    def disconnect(self) -> None:
        self._service = None

    def test_connection(self) -> tuple:
        try:
            props = self._fs.get_file_system_properties()
            return True, f"Connected: {self._container} (Azure ADLS Gen2)"
        except Exception as e:
            return False, str(e)

    def get_metadata(self) -> SourceMetadata:
        root_path = self.config.get("directory_path", "")
        tables = []

        try:
            # List top-level directories as tables
            paths = list(self._fs.get_paths(path=root_path, recursive=False))
            dirs = [p for p in paths if p.is_directory]

            if not dirs:
                # Flat container
                dirs = [None]  # Sentinel for root

            for dir_path in dirs[:50]:
                folder_name = (dir_path.name.split("/")[-1] if dir_path else "root")

                columns = [
                    ColumnMeta(name="name", data_type="string", is_nullable=False),
                    ColumnMeta(name="content_length", data_type="integer", is_nullable=False),
                    ColumnMeta(name="last_modified", data_type="timestamp", is_nullable=False),
                    ColumnMeta(name="hdi_isfolder", data_type="boolean", is_nullable=True),
                    ColumnMeta(name="group", data_type="string", is_nullable=True),
                    ColumnMeta(name="owner", data_type="string", is_nullable=True),
                ]

                # Count files in directory
                try:
                    sub_paths = list(self._fs.get_paths(
                        path=dir_path.name if dir_path else root_path,
                        recursive=True
                    ))
                    file_count = sum(1 for p in sub_paths if not p.is_directory)
                    total_size = sum(p.content_length or 0 for p in sub_paths if not p.is_directory)
                except Exception:
                    file_count = 0
                    total_size = 0

                tables.append(TableMeta(
                    name=folder_name,
                    schema=self._container,
                    columns=columns,
                    row_count=file_count,
                    size_bytes=total_size,
                ))

        except Exception as e:
            logger.error(f"[{self.source_id}] ADLS metadata failed: {e}")

        return SourceMetadata(
            source_id=self.source_id,
            source_type="azure_adls",
            tables=tables,
            captured_at=datetime.utcnow(),
        )

    def sample_data(self, table: str, column: str, n: int = 100) -> List[str]:
        root_path = self.config.get("directory_path", "")
        folder = f"{root_path}/{table}" if root_path else table
        samples = []

        try:
            paths = list(self._fs.get_paths(path=folder, recursive=True))
            for path in paths[:n]:
                if path.is_directory:
                    continue
                name = path.name
                if not any(name.endswith(ext) for ext in [".json", ".csv", ".txt", ".log"]):
                    continue
                try:
                    file_client = self._fs.get_file_client(name)
                    download = file_client.download_file(offset=0, length=2048)
                    content = download.readall().decode("utf-8", errors="replace")
                    samples.append(content[:500])
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"[{self.source_id}] ADLS sampling failed: {e}")

        return samples
