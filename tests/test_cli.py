"""Tests for argument parsing."""

from argparse import ArgumentTypeError
from pathlib import Path

import pytest

from adder.cli import DEFAULT_WIDTH, PRINT_CONFIG, parse_args, width_percent


def test_defaults() -> None:
    args = parse_args([])
    assert args.width == DEFAULT_WIDTH == 75
    assert args.config is None


@pytest.mark.parametrize("value", ["0", "50", "100"])
def test_width_accepts_the_whole_range(value: str) -> None:
    assert width_percent(value) == int(value)


@pytest.mark.parametrize("value", ["-1", "101", "1000"])
def test_width_rejects_a_value_out_of_range(value: str) -> None:
    with pytest.raises(ArgumentTypeError, match="between 0 and 100"):
        width_percent(value)


@pytest.mark.parametrize("value", ["half", "50.5", ""])
def test_width_rejects_a_value_that_is_not_a_whole_number(value: str) -> None:
    with pytest.raises(ArgumentTypeError, match="whole number"):
        width_percent(value)


@pytest.mark.parametrize("flag", ["-w", "--width"])
def test_width_flag(flag: str) -> None:
    assert parse_args([flag, "40"]).width == 40


def test_a_bad_width_exits_with_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as info:
        parse_args(["-w", "200"])
    assert info.value.code == 2
    assert "between 0 and 100" in capsys.readouterr().err


def test_config_absent_is_none() -> None:
    assert parse_args([]).config is None


@pytest.mark.parametrize("flag", ["-c", "--config"])
def test_a_bare_config_flag_is_the_print_sentinel(flag: str) -> None:
    assert parse_args([flag]).config is PRINT_CONFIG


@pytest.mark.parametrize("flag", ["-c", "--config"])
def test_a_config_flag_with_a_path(flag: str) -> None:
    assert parse_args([flag, "/tmp/custom.conf"]).config == Path("/tmp/custom.conf")


def test_a_bare_config_flag_before_another_flag() -> None:
    args = parse_args(["-c", "-w", "40"])
    assert args.config is PRINT_CONFIG
    assert args.width == 40
