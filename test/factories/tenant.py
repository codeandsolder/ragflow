"""
Factory for creating Tenant instances.
"""

from factory import Sequence
from factory.fuzzy import FuzzyText
from api.db.db_models import Tenant
from .base import BaseFactory


class TenantFactory(BaseFactory):
    """Factory for creating Tenant instances."""

    class Meta:
        model = Tenant

    id = Sequence(lambda n: f"tenant-{n:04d}")
    name = FuzzyText(length=10, prefix="Tenant ")
    description = FuzzyText(length=50, prefix="Test tenant for ")
    status = "active"
    create_time = 0
    create_date = None
    update_time = 0
    update_date = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create a Tenant instance with factory-boy."""
        return super()._create(model_class, *args, **kwargs)