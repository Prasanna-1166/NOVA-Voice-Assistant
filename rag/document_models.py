import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional


@dataclass
class Document:
    filename: str
    source_path: str
    file_type: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DocumentChunk:
    document_id: str
    chunk_index: int
    text: str
    source_filename: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    similarity_score: float