"""
Name: PDF Processor 
Purpose: Processes PDF content, Extracts text and layout
Input: Raw PDF content from Web Scraper in Input Layer
Output: Structured PDF data to Queue Manager in Processing Layer
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from typing import Any, Optional, TypeVar

DocumentType = TypeVar('DocumentType', str)


import abc
from abc import abstractmethod

@dataclass
class ScrapingResult:
    """
    Dataclass for scraping results.
    """
    job_id: UUID
    content: str|bytes
    content_type: DocumentType
    metadata: dict[str, Any]
    timestamp: datetime
    success: bool
    error: Optional[str] = None


# CREATE TABLE IF NOT EXISTS Documents (
#     document_id_bin BINARY(16) PRIMARY KEY,
#     source_id_bin BINARY(16) NOT NULL,
#     url VARCHAR(2200) NOT NULL,
#     current_version_id BINARY(16),
#     status ENUM('new', 'processing', 'complete', 'error') NOT NULL,
#     priority TINYINT NOT NULL DEFAULT 5 CHECK (priority BETWEEN 1 AND 5),
#     type VARCHAR(50) NOT NULL,
#     FOREIGN KEY (source_id) REFERENCES Sources(source_id),
#     FOREIGN KEY (current_version_id) REFERENCES Versions(version_id),
#     INDEX idx_status (status),
#     INDEX idx_priority (priority),
#     INDEX idx_type (type)
# ) 


class PdfProcessor(abc.ABCMeta):
    """
    Class for processing PDF content and extracting text and layout.
    """

    def __init__():
        pass

    @abstractmethod()
    def get_pdf_from_folder():
        pass






