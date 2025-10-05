"""
Invoice file domain model.

Represents a downloaded invoice file with its content and metadata.
"""

import hashlib
from dataclasses import dataclass
from typing import Optional


@dataclass
class InvoiceFile:
    """Represents a downloaded invoice file with content and metadata."""
    
    content: bytes
    file_name: str
    content_type: str
    size: int
    hash_md5: str
    hash_sha256: str
    
    def __post_init__(self):
        """Validate the invoice file after initialization."""
        if len(self.content) == 0:
            raise ValueError("File content cannot be empty")
        
        if self.size != len(self.content):
            raise ValueError("File size must match content length")
        
        if not self.file_name.strip():
            raise ValueError("File name cannot be empty")
        
        if not self.content_type.strip():
            raise ValueError("Content type cannot be empty")
        
        # Verify hashes match content
        if self.hash_md5 != self._calculate_md5():
            raise ValueError("MD5 hash does not match content")
        
        if self.hash_sha256 != self._calculate_sha256():
            raise ValueError("SHA256 hash does not match content")
    
    def _calculate_md5(self) -> str:
        """Calculate MD5 hash of the content."""
        return hashlib.md5(self.content).hexdigest()
    
    def _calculate_sha256(self) -> str:
        """Calculate SHA256 hash of the content."""
        return hashlib.sha256(self.content).hexdigest()
    
    @classmethod
    def from_content(cls, content: bytes, file_name: str, content_type: str = "application/pdf") -> "InvoiceFile":
        """Create an InvoiceFile from raw content, calculating hashes automatically."""
        return cls(
            content=content,
            file_name=file_name,
            content_type=content_type,
            size=len(content),
            hash_md5=hashlib.md5(content).hexdigest(),
            hash_sha256=hashlib.sha256(content).hexdigest()
        )
