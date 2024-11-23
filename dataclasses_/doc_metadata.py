

from dataclasses import dataclass
from typing import Any, AsyncIterable, Iterable, Container


from dataclasses_.mysql_insert import SqlInsert


@dataclass
class DocMetadata(SqlInsert):
    """
    ```sql
    CREATE TABLE IF NOT EXISTS doc_metadata (
        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        url_hash CHAR(64) NOT NULL COMMENT 'References urls.url_hash',
        document_hash CHAR(64) NOT NULL COMMENT 'Composite hash of URL + GNIS + document_date',
        query_hash CHAR(64) NOT NULL,
        doc_metadata_title_hash CHAR(64) NOT NULL,
        gnis MEDIUMINT UNSIGNED NOT NULL,
        doc_type VARCHAR(16) NOT NULL,
        doc_title VARCHAR(255), COMMENT '255 is just below the maximum length of a filename in NTFS.',
        document_date DATE NOT NULL COMMENT 'The date this document version is from',
        doc_creation_date DATETIME,
        saved_in_database BOOLEAN DEFAULT FALSE,
        other_metadata JSON,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_document_date (document_date),
        INDEX idx_doc_creation_date (doc_creation_date),
        INDEX idx_url_hash (url_hash),
        INDEX idx_document_hash (document_hash),
        INDEX idx_created_at (created_at),
        INDEX idx_doc_type (doc_type),
        INDEX idx_gnis (gnis),
        UNIQUE INDEX unique_document_version (url_hash, document_date),
        UNIQUE INDEX unique_metadata_title (doc_metadata_title_hash, node_id),
        
        CONSTRAINT fk_urls
            FOREIGN KEY (url_hash) 
            REFERENCES urls(url_hash)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    ```
    """
    _gnis: int | Container[int] # MEDIUMINT UNSIGNED NOT NULL
    _query_hash: str | Container[str] # CHAR(64) NOT NULL
    _document_hash: str | Container[str] # CHAR(64) NOT NULL
    _doc_metadata_title_hash: str | Container[str] # CHAR(64) NOT NULL
    _doc_type: str | Container[str] # VARCHAR(16) NOT NULL,
    _doc_title: str | Container[str] # VARCHAR(255) NOT NULL
    _doc_creation_date: str | Container[str] #DATETIME NOT NULL
    _saved_in_database: bool | Container[bool] # BOOLEAN DEFAULT FALSE
    _other_metadata: dict | Container[dict] # JSON

    def __post_init__(self):
        self._gnis: int = None or self._gnis
        self._query_hash: str = None or self._query_hash
        self._document_hash: str = None or self._document_hash
        self._doc_metadata_title_hash: str = None or self._doc_metadata_title_hash
        self._doc_type: str = None or self._doc_type
        self._doc_title: str = None or self._doc_title
        self._doc_creation_date: str  = None or self._doc_creation_date
        self._saved_in_database: bool = None or self._saved_in_database
        self._other_metadata: dict = None or self._other_metadata

    @property
    def doc_type(self) -> str:
        """
        The type of document (e.g., 'pdf', 'html', 'jpeg')\n
        MySQL definition: VARCHAR(16) NOT NULL
        """
        return self._doc_type

    @doc_type.setter
    def doc_type(self, value: str):
        self._type_check_value(value, str)
        self._type_check_value_length(value, max_length=16)
        self._document_date = value

    @property
    def query_hash(self) -> str:
        """
        A 64-character hash of the query used to retrieve the document.\n
        Hash order: query_string, query_date, query_results
        MySQL Definition: CHAR(64) NOT NULL
        """
        return self._query_hash

    @query_hash.setter
    def query_hash(self, *value: Any):
        self._type_check_value(value, tuple)
        self._query_hash = self._create_sha256_hash(*value)

    @property
    def document_hash(self) -> str:
        """
        A 64-character hash of properties used to uniquely identify a document.\n
        Hash order: gnis, document_date,
        MySQL Definition: CHAR(64) NOT NULL
        """
        return self._document_hash

    @document_hash.setter
    def document_hash(self, *value: Any):
        self._type_check_value(value, tuple)
        self._document_hash = self._create_sha256_hash(*value)

    @property
    def doc_metadata_title_hash(self) -> str:
        """
        MySQL Definition: CHAR(64) NOT NULL
        """
        return self._doc_metadata_title_hash

    @doc_metadata_title_hash.setter
    def doc_metadata_title_hash(self, *value: Any):
        self._type_check_value(value, tuple)
        self._doc_metadata_title_hash = self._create_sha256_hash(*value)

    @property
    def doc_type(self) -> str:
        """
        MySQL Definition: VARCHAR(16) NOT NULL
        """
        return self._doc_type

    @doc_type.setter
    def doc_type(self, value: str):
        self._type_check_value(value, str)
        self._type_check_value(value, str)
        self._document_date = value

    @property
    def doc_title(self) -> str:
        """
        VARCHAR(255) NOT NULL
        """
        return self._doc_title

    @doc_type.setter
    def doc_title(self, value: str):
        self._type_check_value(value, str)
        self._doc_title = value

    @property
    def doc_creation_date(self) -> str:
        return self._doc_creation_date

    @doc_type.setter
    def doc_creation_date(self, value: str):
        self._type_check_value(value, str)
        self._doc_creation_date = value

    @property
    def saved_in_database(self) -> bool:
        return self._saved_in_database

    @doc_type.setter
    def saved_in_database(self, value: bool):
        self._type_check_value(value, bool)
        self._saved_in_database = value

    @property
    def other_metadata(self) -> dict:
        return self._saved_in_database

    @doc_type.setter
    def other_metadata(self, value: dict):
        self._type_check_value(value, dict)
        self._saved_in_database = value

