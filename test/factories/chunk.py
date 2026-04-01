"""
Chunk Factory for RAGFlow using factory-boy.

Note: In RAGFlow, chunks are primarily stored in the document store (Elasticsearch/Infinity),
not as a database model. The Chunk class here provides a simple model-like structure
for testing purposes that mimics the chunk data stored in the document store.
"""

import factory
from factory import Sequence, LazyAttribute
from faker import Faker

fake = Faker()


class Chunk:
    """Represents a chunk-like object for testing purposes.
    
    In RAGFlow, chunks are stored in the document store (ES/Infinity) with fields:
    - id: unique identifier
    - kb_id: knowledge base ID
    - doc_id: document ID  
    - text: chunk text content
    - chunk_index: position in document
    - parent_id: parent chunk for hierarchy
    - embedding/vector: vector representation
    - status: validity flag
    - created_by: creator user ID
    """

    def __init__(
        self,
        id: str,
        kb_id: str,
        doc_id: str,
        text: str,
        chunk_index: int,
        parent_id: str = None,
        embedding: list = None,
        vector: list = None,
        status: str = "1",
        created_by: str = None,
        **kwargs
    ):
        self.id = id
        self.kb_id = kb_id
        self.doc_id = doc_id
        self.text = text
        self.content = text
        self.chunk_index = chunk_index
        self.parent_id = parent_id
        self.embedding = embedding or vector or []
        self.vector = vector or embedding or []
        self.status = status
        self.created_by = created_by
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f"Chunk(id={self.id}, doc_id={self.doc_id}, chunk_index={self.chunk_index})"

    def to_dict(self):
        return {
            "id": self.id,
            "kb_id": self.kb_id,
            "doc_id": self.doc_id,
            "text": self.text,
            "content": self.text,
            "chunk_index": self.chunk_index,
            "parent_id": self.parent_id,
            "embedding": self.embedding,
            "vector": self.vector,
            "status": self.status,
            "created_by": self.created_by,
        }


class ChunkFactory(factory.Factory):
    """Factory for creating Chunk-like instances for testing."""

    class Meta:
        model = Chunk

    id = Sequence(lambda n: f"chunk-{n:04d}")
    kb_id = Sequence(lambda n: f"kb-{n % 3:04d}")
    doc_id = Sequence(lambda n: f"doc-{n % 5:04d}")
    text = LazyAttribute(lambda obj: fake.text(max_nb_chars=500))
    content = LazyAttribute(lambda obj: obj.text)
    chunk_index = Sequence(lambda n: n)
    parent_id = None
    embedding = LazyAttribute(lambda obj: [round(fake.random.uniform(-1.0, 1.0), 6) for _ in range(768)])
    vector = LazyAttribute(lambda obj: obj.embedding)
    status = "1"
    created_by = Sequence(lambda n: f"user-{n:04d}")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create a Chunk instance with factory-boy."""
        return model_class(*args, **kwargs)

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        """Build a Chunk instance without saving."""
        return model_class(*args, **kwargs)


class ChunkWithKeywordsFactory(ChunkFactory):
    """Factory for creating chunks with keywords and questions."""

    important_keywords = LazyAttribute(lambda obj: fake.words(nb=5, unique=True))
    questions = LazyAttribute(lambda obj: [fake.sentence() for _ in range(2)])
    docnm_kwd = LazyAttribute(lambda obj: fake.sentence(nb_words=3))


class LargeChunkFactory(ChunkFactory):
    """Factory for creating larger chunks for testing."""

    text = LazyAttribute(lambda obj: "\n\n".join([fake.paragraph(nb_sentences=10) for _ in range(5)]))


class SmallChunkFactory(ChunkFactory):
    """Factory for creating small chunks for testing."""

    text = LazyAttribute(lambda obj: fake.sentence(nb_words=20))


class RootChunkFactory(ChunkFactory):
    """Factory for creating root-level chunks (no parent)."""

    parent_id = None
    chunk_index = 0


class ChildChunkFactory(ChunkFactory):
    """Factory for creating child chunks under a parent."""

    parent_id = Sequence(lambda n: f"chunk-parent-{n:04d}")
    chunk_index = Sequence(lambda n: n + 1)


class ActiveChunkFactory(ChunkFactory):
    """Factory for creating active/valid chunks."""

    status = "1"


class InactiveChunkFactory(ChunkFactory):
    """Factory for creating inactive/invalid chunks."""

    status = "0"
