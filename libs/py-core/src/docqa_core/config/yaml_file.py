"""Read the optional YAML config file and expand ``${ENV}`` references in it.

Pure functions (the environment is passed in), so they are easy to test. ``settings.py`` plugs
them into pydantic-settings.

Interpolation, in string values only:

- ``${NAME}``: the value of ``NAME``; a missing variable is an error.
- ``${NAME:-default}``: the value of ``NAME``, or ``default`` when it is unset or empty.
- ``$${NAME}``: a literal ``${NAME}``.

Inside YAML flow collections (``{...}``, ``[...]``) quote values that contain references,
because ``{`` would otherwise start a nested mapping: ``{url: "${URL}"}``.
"""

import re
from collections.abc import Mapping
from pathlib import Path

import yaml

from docqa_core.domain.errors import ConfigError

_REFERENCE = re.compile(r"\$(\$?)\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def load_yaml_config(path: Path, environ: Mapping[str, str]) -> dict[str, object]:
    """Load ``path`` as a mapping and expand ``${ENV}`` references in its strings.

    Raises:
        ConfigError: If the file is missing, is not valid YAML, is not a mapping at the top,
            or references an environment variable that is not set and has no default.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"config file {path} could not be read: {exc.strerror}") from exc
    try:
        data: object = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"config file {path} is not valid YAML: {_yaml_problem(exc)}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"config file {path} must contain a mapping at the top level")
    source = str(path)
    return {str(key): interpolate(item, environ, source=source) for key, item in data.items()}


def interpolate(value: object, environ: Mapping[str, str], *, source: str) -> object:
    """Return ``value`` with ``${ENV}`` references expanded in every nested string.

    Raises:
        ConfigError: If a referenced variable is unset and has no default.
    """
    if isinstance(value, str):
        return _expand(value, environ, source)
    if isinstance(value, dict):
        return {key: interpolate(item, environ, source=source) for key, item in value.items()}
    if isinstance(value, list):
        return [interpolate(item, environ, source=source) for item in value]
    return value


def _expand(text: str, environ: Mapping[str, str], source: str) -> str:
    def replace(match: re.Match[str]) -> str:
        escaped, name, default = match.groups()
        if escaped:
            return match.group(0)[1:]
        found = environ.get(name)
        if found is not None and (found or default is None):
            return found
        if default is not None:
            return default
        raise ConfigError(
            f"{source}: environment variable {name} is not set; "
            f"set it, or give a default with ${{{name}:-value}}"
        )

    return _REFERENCE.sub(replace, text)


def _yaml_problem(exc: yaml.YAMLError) -> str:
    mark = getattr(exc, "problem_mark", None)
    problem = getattr(exc, "problem", None) or "parse error"
    if mark is None:
        return str(problem)
    return f"{problem} at line {mark.line + 1}, column {mark.column + 1}"
