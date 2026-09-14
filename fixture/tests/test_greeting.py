"""Tests for the fixture greeting project, run by the fixture's absolute pytest check."""
from greeting import greet


def test_greet_returns_a_friendly_message() -> None:
    assert greet("Ada") == "Hello, Ada!"


def test_greet_rejects_a_blank_name() -> None:
    try:
        greet("   ")
    except ValueError as error:
        assert "non-empty" in str(error)
    else:
        raise AssertionError("greet('   ') should have raised ValueError")
