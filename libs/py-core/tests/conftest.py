"""Shared fixtures for integration tests against a database migrated by Prisma."""

from collections.abc import Iterator

import pytest
from db_testing import TEST_URL, TenantFactory
from sqlalchemy import Engine, create_engine


@pytest.fixture
def engine() -> Iterator[Engine]:
    """Superuser engine for the migrated test database."""
    assert TEST_URL
    eng = create_engine(TEST_URL)
    yield eng
    eng.dispose()


@pytest.fixture
def tenants(engine: Engine) -> Iterator[TenantFactory]:
    """Factory for throwaway tenants, removed with everything they own."""
    factory = TenantFactory(engine)
    yield factory
    factory.cleanup()
