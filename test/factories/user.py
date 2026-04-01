"""
User Factory for RAGFlow using factory-boy.
"""

import factory
import factory.fuzzy
from faker import Faker
from api.db.db_models import User

fake = Faker()


class UserFactory(factory.Factory):
    """Factory for creating User instances."""

    class Meta:
        model = User

    id = factory.Sequence(lambda n: f"user-{n:04d}")
    email = factory.LazyAttribute(lambda obj: fake.unique.email())
    nickname = factory.LazyAttribute(lambda obj: fake.name())
    password = factory.LazyAttribute(lambda obj: fake.password(length=12))
    avatar = factory.LazyAttribute(lambda obj: fake.image_url(width=200, height=200))
    language = "English"
    color_schema = "Bright"
    timezone = "UTC+8"
    is_active = "1"
    is_superuser = False
    tenant_id = factory.Sequence(lambda n: f"tenant-{n % 3}")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create a User instance with factory-boy."""
        return model_class.create(*args, **kwargs)


class AdminUserFactory(UserFactory):
    """Factory for creating admin User instances."""

    is_superuser = True


class ActiveUserFactory(UserFactory):
    """Factory for creating active User instances."""

    is_active = "1"


class InactiveUserFactory(UserFactory):
    """Factory for creating inactive User instances."""

    is_active = "0"


class EnglishUserFactory(UserFactory):
    """Factory for creating English language User instances."""

    language = "English"


class ChineseUserFactory(UserFactory):
    """Factory for creating Chinese language User instances."""

    language = "Chinese"


class BrightUserFactory(UserFactory):
    """Factory for creating Bright color schema User instances."""

    color_schema = "Bright"


class DarkUserFactory(UserFactory):
    """Factory for creating Dark color schema User instances."""

    color_schema = "Dark"