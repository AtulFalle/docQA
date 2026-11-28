"""Provider registries: pick an implementation by name, with parameters from config.

Each interface gets its own ``Registry`` instance (``llms``, ``embedders``, ...), so the same
name can mean different classes in different places. Providers register with a decorator:

.. code-block:: python

    llms: Registry[LLMProvider] = Registry("llm")


    @llms.register("fake")
    class FakeLLM: ...


    llm = llms.create("fake", latency_ms=5)

Registering the same name twice is a programming error and raises ``ProviderRegistrationError``
(a ``ValueError``; never an ``assert``, which ``python -O`` would remove). Asking for an unknown
name or passing parameters the provider does not accept is a configuration error and raises
``ConfigError`` with a readable message, so a service fails at startup instead of at first use.
"""

import difflib
import importlib
import inspect
import re
from collections.abc import Callable, Iterable, Mapping

from docqa_core.domain.errors import ConfigError

_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_PLAIN = (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)


class ProviderRegistrationError(ValueError):
    """A provider was registered with an invalid or duplicate name."""


class Registry[T]:
    """Named implementations of one interface."""

    def __init__(self, kind: str) -> None:
        """Create an empty registry for providers of ``kind`` (for example ``"llm"``)."""
        self.kind = kind
        self._providers: dict[str, type[T]] = {}

    def register(self, name: str) -> Callable[[type[T]], type[T]]:
        """Return a class decorator that registers the class under ``name``.

        Raises:
            ProviderRegistrationError: If the name is not ``snake_case`` or is already taken, or
                the class cannot be built from keyword arguments.
        """
        if not _NAME.fullmatch(name):
            raise ProviderRegistrationError(
                f"{self.kind} provider name {name!r} must be snake_case (a-z, 0-9, _)"
            )

        def decorator(cls: type[T]) -> type[T]:
            existing = self._providers.get(name)
            if existing is not None:
                raise ProviderRegistrationError(
                    f"{self.kind} provider {name!r} is already registered "
                    f"by {existing.__module__}.{existing.__qualname__}"
                )
            _check_keyword_constructible(self.kind, name, cls)
            self._providers[name] = cls
            return cls

        return decorator

    def names(self) -> tuple[str, ...]:
        """Return the registered names, sorted."""
        return tuple(sorted(self._providers))

    def __contains__(self, name: object) -> bool:
        """Whether a provider is registered under ``name``."""
        return name in self._providers

    def get(self, name: str) -> type[T]:
        """Return the class registered under ``name``.

        Raises:
            ConfigError: If no provider has that name. The message suggests close matches.
        """
        try:
            return self._providers[name]
        except KeyError:
            hint = _did_you_mean(name, self._providers)
            known = ", ".join(self.names()) or "none"
            raise ConfigError(
                f"unknown {self.kind} provider {name!r}{hint}; registered: {known}"
            ) from None

    def create(self, name: str, /, **params: object) -> T:
        """Instantiate the provider registered under ``name`` with ``params``.

        Raises:
            ConfigError: If the name is unknown, a parameter is not accepted, or a required
                parameter is missing.
        """
        cls = self.get(name)
        _check_params(f"{self.kind} provider {name!r}", cls, params)
        return cls(**params)


def import_plugins(modules: Iterable[str]) -> None:
    """Import provider modules by dotted name so their ``@register`` decorators run.

    The composition root calls this with the module list from config, so registration happens
    in one known place rather than as a side effect of some unrelated import.

    Raises:
        ConfigError: If a module cannot be imported.
    """
    for module in modules:
        try:
            importlib.import_module(module)
        except ImportError as exc:
            raise ConfigError(f"plugin module {module!r} could not be imported: {exc}") from exc


def _check_keyword_constructible(kind: str, name: str, cls: type[object]) -> None:
    """Config passes parameters by keyword, so no required parameter may be positional-only."""
    for param in inspect.signature(cls).parameters.values():
        if param.kind is inspect.Parameter.POSITIONAL_ONLY and param.default is param.empty:
            raise ProviderRegistrationError(
                f"{kind} provider {name!r} needs positional-only parameter {param.name!r}; "
                "providers must be constructible from keyword arguments"
            )


def _check_params(label: str, cls: type[object], params: Mapping[str, object]) -> None:
    accepted = _accepted_params(cls)
    if accepted is None:
        return
    names, required = accepted
    unknown = sorted(set(params) - names)
    if unknown:
        details = "; ".join(f"{key!r}{_did_you_mean(key, names)}" for key in unknown)
        allowed = ", ".join(sorted(names)) or "none"
        raise ConfigError(f"{label} got unknown parameter(s) {details}; accepted: {allowed}")
    missing = sorted(required - set(params))
    if missing:
        raise ConfigError(f"{label} is missing required parameter(s): {', '.join(missing)}")


def _accepted_params(cls: type[object]) -> tuple[set[str], set[str]] | None:
    """Return (accepted names, required names), or None when the class takes ``**kwargs``."""
    parameters = inspect.signature(cls).parameters.values()
    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in parameters):
        return None
    plain = [p for p in parameters if p.kind in _PLAIN]
    names = {p.name for p in plain}
    required = {p.name for p in plain if p.default is inspect.Parameter.empty}
    return names, required


def _did_you_mean(name: str, candidates: Iterable[str]) -> str:
    matches = difflib.get_close_matches(name, list(candidates), n=1)
    return f" (did you mean {matches[0]!r}?)" if matches else ""
