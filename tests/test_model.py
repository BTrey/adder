"""Tests for the session model."""

from adder.model import Row, RowKind, Session


def test_row_defaults() -> None:
    row = Row(text="hello")
    assert row.kind is RowKind.TEXT
    assert row.color_key == "text"
    assert row.value is None
    assert row.error is None


def test_row_error_factory() -> None:
    row = Row.error_row("/ 0", "division by zero")
    assert row.kind is RowKind.ERROR
    assert row.color_key == "error"
    assert row.error == "division by zero"
    assert row.value is None


def test_session_starts_empty() -> None:
    session = Session()
    assert session.rows == []
    assert session.value == 0.0
    assert session.variables == {}


def test_session_add_appends_row() -> None:
    session = Session()
    row = Row(text="hello")
    session.add(row)
    assert session.rows == [row]


def test_session_add_with_value_updates_value() -> None:
    session = Session()
    session.add(Row(text="+ 5", kind=RowKind.OPERATION, value=5.0))
    assert session.value == 5.0


def test_session_add_without_value_keeps_value() -> None:
    session = Session()
    session.value = 7.0
    session.add(Row(text="hello"))
    assert session.value == 7.0


def test_session_variables_round_trip() -> None:
    session = Session()
    session.set_variable("var1", 5.0)
    assert session.get_variable("var1") == 5.0
    assert session.get_variable("nope") is None


def test_session_clear_resets_everything_but_variables() -> None:
    session = Session()
    session.add(Row(text="+ 5", value=5.0))
    session.set_variable("var1", 2.0)
    session.clear()
    assert session.rows == []
    assert session.value == 0.0
    assert session.variables == {"var1": 2.0}


def test_session_reset_clears_everything_including_variables() -> None:
    session = Session()
    session.add(Row(text="+ 5", value=5.0))
    session.set_variable("var1", 2.0)
    session.reset()
    assert session.rows == []
    assert session.value == 0.0
    assert session.variables == {}


def test_session_reset_matches_a_new_session() -> None:
    session = Session()
    session.add(Row(text="+ 5", value=5.0))
    session.set_variable("var1", 2.0)
    session.reset()
    assert session == Session()


def test_session_starts_with_no_effects() -> None:
    assert Session().effects == []


def test_take_effects_returns_and_empties_the_requests() -> None:
    session = Session()
    session.request_effect("help")
    session.request_effect("help")
    assert session.take_effects() == ["help", "help"]
    assert session.effects == []


def test_reset_drops_a_pending_effect() -> None:
    session = Session()
    session.request_effect("help")
    session.reset()
    assert session == Session()
