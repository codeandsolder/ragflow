"""
Factory for creating Document instances.
"""

from factory import Sequence
from api.db.db_models import Document
from .base import BaseFactory


class DocumentFactory(BaseFactory):
    """Factory for creating Document instances."""

    class Meta:
        model = Document

    id = Sequence(lambda n: f"doc-{n:04d}")
    kb_id = Sequence(lambda n: f"kb-{n % 3:04d}")
    thumbnail = None
    parser_id = "naive"
    pipeline_id = None
    parser_config = {"pages": [[1, 1000000]], "table_context_size": 0, "image_context_size": 0}
    source_type = "local"
    type = "txt"
    created_by = Sequence(lambda n: f"user-{n:04d}")
    name = Sequence(lambda n: f"Document {n}.txt")
    location = Sequence(lambda n: f"/documents/doc-{n:04d}.txt")
    size = 0
    token_num = 0
    chunk_num = 0
    progress = 0.0
    progress_msg = ""
    process_begin_at = None
    process_duration = 0.0
    suffix = "txt"
    content_hash = ""
    run = "0"
    status = "1"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create a Document instance with factory-boy."""
        return super()._create(model_class, *args, **kwargs)