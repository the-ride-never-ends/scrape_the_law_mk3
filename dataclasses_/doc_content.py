

from typing import Any


from dataclasses_.mysql_insert import SqlInsert
from dataclasses import dataclass



from dataclasses_.utils.html_to_text import html_to_text


@dataclass
class DocContent(SqlInsert):
    """
    CREATE TABLE IF NOT EXISTS doc_content (
        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        gnis MEDIUMINT UNSIGNED NOT NULL,
        document_hash CHAR(64) NOT NULL COMMENT 'References doc_metadata.document_hash',
        url_hash CHAR(64) NOT NULL COMMENT 'References urls.url_hash',
        query_hash CHAR(64) NOT NULL,
        doc_metadata_title_hash CHAR(64) NOT NULL,
        pg_title VARCHAR(255) NOT NULL,
        pg_num SMALLINT UNSIGNED NOT NULL,
        pg_content LONGTEXT NOT NULL,
        data_was_cleaned BOOLEAN NOT NULL DEFAULT FALSE,
        local_file_path VARCHAR(255),
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT fk_doc_metadata_content
            FOREIGN KEY (document_hash) 
            REFERENCES doc_metadata(document_hash)
            ON DELETE CASCADE,
        CONSTRAINT fk_urls_content
            FOREIGN KEY (url_hash) 
            REFERENCES urls(url_hash)
            ON DELETE CASCADE,
            
        INDEX idx_gnis (gnis),
        INDEX idx_url_hash (url_hash),
        INDEX idx_document_hash (document_hash),
        INDEX idx_doc_metadata_title_hash (doc_metadata_title_hash),
        INDEX idx_query_hash (query_hash),
        INDEX idx_created_at (created_at),
        INDEX idx_pg_title (pg_title),
        INDEX idx_local_file_path (local_file_path),
        UNIQUE INDEX unique_page (document_hash, pg_num)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    _url_hash: str # CHAR(64) NOT NULL
    _query_hash: str # CHAR(64) NOT NULL
    _document_hash: str # CHAR(64) NOT NULL
    _doc_metadata_title_hash: str
    _document_date: str  # Datetime string
    _pg_title: str # VARCHAR(255) NOT NULL
    _pg_num: int # SMALLINT UNSIGNED NOT NULL,
    _pg_content: str # LONGTEXT NOT NULL,
    _data_was_cleaned: bool # BOOLEAN NOT NULL DEFAULT FALSE,
    _local_file_path: str # VARCHAR(255),


    def __post_init__(self):
        self._url_hash: str = None
        self._query_hash: str = None
        self._document_hash: str = None
        self._doc_metadata_title_hash: str = None
        self._document_date: str = None
        self._pg_title: str = None
        self._pg_num: str  = None
        self._pg_content: bool = None
        self._data_was_cleaned: str = None
        self._local_file_path: str = None


    @property
    def query_hash(self) -> str:
        return self._query_hash

    @query_hash.setter
    def query_hash(self, value: tuple[Any,...]):
        self._query_hash = self._create_sha256_hash(*value)

    @property
    def document_hash(self) -> str:
        return self._document_hash

    @document_hash.setter
    def document_hash(self, *value: tuple[Any,...]):
        self._document_hash = self._create_sha256_hash(*value)

    @property
    def doc_metadata_title_hash(self) -> str:
        return self._doc_metadata_title_hash

    @doc_metadata_title_hash.setter
    def doc_metadata_title_hash(self, *value: tuple[Any,...]):
        self._doc_metadata_title_hash = self._create_sha256_hash(*value)

    @property
    def document_date(self) -> str:
        return self._document_date

    @document_date.setter
    def document_date(self, *value: str):
        self._document_date = value

    @property
    def pg_title(self) -> str:
        return self._pg_title

    @pg_title.setter
    def pg_title(self, value: str):
        self._pg_title = value

    @property
    def pg_num(self) -> int:
        return self._pg_num

    @pg_num.setter
    def pg_num(self, value: int):
        self._pg_num = value

    @property
    def pg_content(self) -> str:
        return self._pg_content

    @pg_content.setter
    def pg_content(self, value: str):
        self._pg_content = html_to_text(value)

    @property
    def data_was_cleaned(self) -> bool:
        return self._data_was_cleaned

    @data_was_cleaned.setter
    def data_was_cleaned(self, value: bool):
        self._data_was_cleaned = value

    @property
    def local_file_path(self) -> str:
        return self._local_file_path

    @local_file_path.setter
    def local_file_path(self, value: str):
        self._local_file_path = value

