"""Tests for CLI argument parsing and configuration loading in main.py."""

import sys

from reflectsonar.main import parse_arguments


def test_parse_arguments_branch_default_none(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["reflectsonar", "-p", "my-project", "-t", "my-token"])
    args = parse_arguments()
    assert args.project == "my-project"
    assert args.token == "my-token"
    assert args.branch is None


def test_parse_arguments_branch_short_flag(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["reflectsonar", "-p", "my-project", "-t", "my-token", "-b", "develop"]
    )
    args = parse_arguments()
    assert args.branch == "develop"


def test_parse_arguments_branch_long_flag(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["reflectsonar", "-p", "my-project", "-t", "my-token", "--branch", "feature/my-feat"],
    )
    args = parse_arguments()
    assert args.branch == "feature/my-feat"


def test_parse_arguments_branch_from_config(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "project: config-proj\ntoken: config-token\nbranch: release/2.0\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(sys, "argv", ["reflectsonar", "-c", str(config_file)])
    args = parse_arguments()
    assert args.project == "config-proj"
    assert args.token == "config-token"
    assert args.branch == "release/2.0"


def test_parse_arguments_config_overrides_cli_branch(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "project: config-proj\ntoken: config-token\nbranch: config-branch\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "reflectsonar",
            "-c",
            str(config_file),
            "-p",
            "cli-proj",
            "-t",
            "cli-token",
            "-b",
            "cli-branch",
        ],
    )
    args = parse_arguments()
    assert args.project == "config-proj"
    assert args.token == "config-token"
    assert args.branch == "config-branch"
