"""YAML config file loading and ${ENV} interpolation."""

from pathlib import Path

import pytest

from docqa_core.config.yaml_file import interpolate, load_yaml_config
from docqa_core.domain import ConfigError


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "docqa.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_yaml_config_loads_nested_values(tmp_path):
    path = write(tmp_path, "env: dev\nproviders:\n  llm:\n    name: fake\n    params: {seed: 7}\n")

    assert load_yaml_config(path, {}) == {
        "env": "dev",
        "providers": {"llm": {"name": "fake", "params": {"seed": 7}}},
    }


def test_yaml_config_expands_environment_references(tmp_path):
    path = write(tmp_path, "database_url: postgresql://${DB_USER}@${DB_HOST}/docqa\n")

    data = load_yaml_config(path, {"DB_USER": "docqa", "DB_HOST": "db"})

    assert data == {"database_url": "postgresql://docqa@db/docqa"}


def test_yaml_config_expands_inside_lists(tmp_path):
    path = write(tmp_path, "plugins:\n  - ${PLUGIN}\n  - static.module\n")

    assert load_yaml_config(path, {"PLUGIN": "my.plugin"}) == {
        "plugins": ["my.plugin", "static.module"]
    }


def test_empty_yaml_file_is_an_empty_config(tmp_path):
    path = write(tmp_path, "")

    assert load_yaml_config(path, {}) == {}


def test_missing_yaml_file_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match="could not be read"):
        load_yaml_config(tmp_path / "absent.yaml", {})


def test_invalid_yaml_reports_the_line(tmp_path):
    path = write(tmp_path, "env: dev\nproviders: [unclosed\n")

    with pytest.raises(ConfigError, match=r"not valid YAML: .* at line \d+, column \d+"):
        load_yaml_config(path, {})


def test_yaml_that_is_not_a_mapping_is_rejected(tmp_path):
    path = write(tmp_path, "- just\n- a list\n")

    with pytest.raises(ConfigError, match="mapping at the top level"):
        load_yaml_config(path, {})


def test_unset_variable_without_default_names_the_variable_and_file(tmp_path):
    path = write(tmp_path, "redis_url: ${REDIS_URL}\n")

    with pytest.raises(
        ConfigError, match=r"docqa\.yaml: environment variable REDIS_URL is not set"
    ):
        load_yaml_config(path, {})


@pytest.mark.parametrize(
    ("environ", "expected"),
    [
        ({}, "fallback"),
        ({"NAME": ""}, "fallback"),
        ({"NAME": "set"}, "set"),
    ],
)
def test_default_applies_when_the_variable_is_unset_or_empty(environ, expected):
    assert interpolate("${NAME:-fallback}", environ, source="test") == expected


def test_set_but_empty_variable_without_default_expands_to_empty():
    assert interpolate("a${NAME}b", {"NAME": ""}, source="test") == "ab"


def test_empty_default_is_allowed():
    assert interpolate("[${NAME:-}]", {}, source="test") == "[]"


def test_double_dollar_keeps_a_literal_reference():
    assert interpolate("$${NAME} and ${NAME}", {"NAME": "x"}, source="test") == "${NAME} and x"


def test_reference_inside_a_quoted_flow_mapping_is_expanded(tmp_path):
    path = write(tmp_path, 'params: {latency_ms: "${LATENCY:-5}"}\n')

    assert load_yaml_config(path, {}) == {"params": {"latency_ms": "5"}}


def test_non_string_values_are_left_alone():
    value = {"count": 3, "ratio": 0.5, "on": True, "none": None}

    assert interpolate(value, {}, source="test") == value
