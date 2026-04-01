"""
Factory for creating Knowledgebase instances.
"""

from factory import Sequence, LazyAttribute
from api.db.db_models import Knowledgebase
from .base import BaseFactory


class KnowledgebaseFactory(BaseFactory):
    """Factory for creating Knowledgebase instances."""

    class Meta:
        model = Knowledgebase

    id = Sequence(lambda n: f"kb-{n:04d}")
    tenant_id = Sequence(lambda n: f"tenant-{n % 3:04d}")
    name = Sequence(lambda n: f"Knowledgebase {n}")
    language = "English"
    description = "Test knowledgebase description"
    embd_id = "embedding-model-1"
    tenant_embd_id = 1
    permission = "me"
    created_by = Sequence(lambda n: f"user-{n:04d}")
    doc_num = 0
    token_num = 0
    chunk_num = 0
    similarity_threshold = 0.2
    vector_similarity_weight = 0.3
    hybrid_weight = None
    parser_id = "naive"
    pipeline_id = None
    parser_config = {"pages": [[1, 1000000]], "table_context_size": 0, "image_context_size": 0}
    pagerank = 0
    graphrag_task_id = None
    graphrag_task_finish_at = None
    raptor_task_id = None
    raptor_task_finish_at = None
    mindmap_task_id = None
    mindmap_task_finish_at = None
    status = "1"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create a Knowledgebase instance with factory-boy."""
        return super()._create(model_class, *args, **kwargs)
