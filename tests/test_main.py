"""Tests for the entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import adder
from src.config import DEFAULT_CONFIG_TEXT, Palette


@pytest.fixture(name="fake_app")
def fixture_fake_app(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Replace the app with a recorder, so main() never starts a terminal."""
    recorded: dict[str, Any] = {}

    class FakeApp:
        def __init__(self, width: int, palette: Palette) -> None:
            recorded["width"] = width
            recorded["palette"] = palette

        def run(self) -> None:
            recorded["ran"] = True

    monkeypatch.setattr(adder, "AdderApp", FakeApp)
    return recorded


def test_main_runs_the_app(fake_app: dict[str, Any]) -> None:
    assert adder.main([]) == 0
    assert fake_app == {"width": 75, "palette": Palette(), "ran": True}


def test_main_passes_the_width(fake_app: dict[str, Any]) -> None:
    assert adder.main(["-w", "40"]) == 0
    assert fake_app["width"] == 40


def test_main_loads_the_named_config(fake_app: dict[str, Any], tmp_path: Path) -> None:
    path = tmp_path / "custom.conf"
    path.write_text("[colors]\ntext = red\n", encoding="utf-8")
    assert adder.main(["-c", str(path)]) == 0
    assert fake_app["palette"].text == "red"


def test_a_bare_config_flag_prints_the_defaults(
    fake_app: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    assert adder.main(["-c"]) == 0
    assert capsys.readouterr().out == DEFAULT_CONFIG_TEXT
    assert "ran" not in fake_app


def test_a_missing_config_reports_the_error(
    fake_app: dict[str, Any], capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    assert adder.main(["-c", str(tmp_path / "absent.conf")]) == 2
    assert "config file not found" in capsys.readouterr().err
    assert "ran" not in fake_app


def test_a_bad_color_reports_the_error(
    fake_app: dict[str, Any], capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    path = tmp_path / "bad.conf"
    path.write_text("[colors]\ntext = nope\n", encoding="utf-8")
    assert adder.main(["-c", str(path)]) == 2
    assert "bad color for text" in capsys.readouterr().err
    assert "ran" not in fake_app


def test_no_config_file_uses_the_defaults(
    fake_app: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert adder.main([]) == 0
    assert fake_app["palette"] == Palette()
