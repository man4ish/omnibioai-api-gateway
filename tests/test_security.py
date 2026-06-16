"""
Tests for app/core/security.py.

generate_trace_id() must return a valid UUID4 string and be globally unique.
"""
import uuid

from app.core.security import generate_trace_id


def test_generate_trace_id_is_valid_uuid():
    tid = generate_trace_id()
    uuid.UUID(tid)  # raises ValueError if not a valid UUID


def test_generate_trace_id_returns_string():
    assert isinstance(generate_trace_id(), str)


def test_generate_trace_id_is_unique():
    ids = {generate_trace_id() for _ in range(100)}
    assert len(ids) == 100
