"""
BaseFactory for RAGFlow using factory-boy.
"""

import factory
import factory.fuzzy
from faker import Faker
from factory.alchemy import SQLAlchemyModelFactory
from api.db.db_models import BaseModel
from api.db.db_services import get_db_session

fake = Faker()


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory class for all RAGFlow factories."""

    class Meta:
        abstract = True
        sqlalchemy_session = get_db_session()
        sqlalchemy_session_persistence = 'flush'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create a model instance with factory-boy."""
        session = cls._meta.sqlalchemy_session
        instance = model_class(*args, **kwargs)
        session.add(instance)
        session.flush()
        return instance

    @classmethod
    def create_batch(cls, size, **kwargs):
        """Create a batch of model instances."""
        return super().create_batch(size, **kwargs)

    @classmethod
    def build_batch(cls, size, **kwargs):
        """Build a batch of model instances without saving."""
        return super().build_batch(size, **kwargs)

    @classmethod
    def generate_batch(cls, size, **kwargs):
        """Generate a batch of model instances without saving."""
        return super().generate_batch(size, **kwargs)

    @classmethod
    def create(cls, **kwargs):
        """Create a model instance and save it to the database."""
        return super().create(**kwargs)

    @classmethod
    def build(cls, **kwargs):
        """Build a model instance without saving."""
        return super().build(**kwargs)

    @classmethod
    def generate(cls, **kwargs):
        """Generate a model instance without saving."""
        return super().generate(**kwargs)

    @classmethod
    def stub(cls, **kwargs):
        """Create a stub instance without saving."""
        return super().stub(**kwargs)

    @classmethod
    def stub_batch(cls, size, **kwargs):
        """Create a batch of stub instances."""
        return super().stub_batch(size, **kwargs)