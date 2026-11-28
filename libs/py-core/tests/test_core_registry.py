"""Provider registry and plugin import."""

import sys
import textwrap
from pathlib import Path
from typing import Protocol

import pytest

from docqa_core.domain import ConfigError
from docqa_core.registry import ProviderRegistrationError, Registry, import_plugins


class Greeter(Protocol):
    def greet(self) -> str: ...


def make_registry() -> Registry[Greeter]:
    registry: Registry[Greeter] = Registry("greeter")

    @registry.register("plain")
    class Plain:
        def greet(self) -> str:
            return "hello"

    @registry.register("polite")
    class Polite:
        def __init__(self, name: str, *, punctuation: str = "!") -> None:
            self.name = name
            self.punctuation = punctuation

        def greet(self) -> str:
            return f"hello {self.name}{self.punctuation}"

    return registry


def test_registry_creates_a_provider_by_name():
    assert make_registry().create("plain").greet() == "hello"


def test_registry_passes_parameters_by_keyword():
    greeter = make_registry().create("polite", name="Asha", punctuation=".")

    assert greeter.greet() == "hello Asha."


def test_registry_lists_names_sorted_and_supports_membership():
    registry = make_registry()

    assert registry.names() == ("plain", "polite")
    assert "plain" in registry
    assert "missing" not in registry


def test_registry_rejects_a_duplicate_name_with_value_error():
    registry = make_registry()

    with pytest.raises(ProviderRegistrationError, match="already registered") as info:
        registry.register("plain")(object)
    assert isinstance(info.value, ValueError)


@pytest.mark.parametrize("name", ["Plain", "with-dash", "1st", "", "white space"])
def test_registry_rejects_names_that_are_not_snake_case(name):
    with pytest.raises(ProviderRegistrationError, match="snake_case"):
        Registry[object]("greeter").register(name)


def test_registry_rejects_a_class_with_required_positional_only_parameters():
    class Positional:
        def __init__(self, value: int, /) -> None:
            self.value = value

    with pytest.raises(ProviderRegistrationError, match="positional-only"):
        Registry[object]("greeter").register("positional")(Positional)


def test_unknown_name_suggests_a_close_match():
    with pytest.raises(
        ConfigError, match=r"unknown greeter provider 'polit' \(did you mean 'polite'\?\)"
    ):
        make_registry().create("polit")


def test_unknown_name_lists_registered_names():
    with pytest.raises(ConfigError, match="registered: plain, polite"):
        make_registry().get("other")


def test_empty_registry_says_none_are_registered():
    with pytest.raises(ConfigError, match="registered: none"):
        Registry[object]("greeter").get("plain")


def test_unknown_parameter_is_a_config_error_with_a_suggestion():
    with pytest.raises(ConfigError, match=r"'punctuaton' \(did you mean 'punctuation'\?\)"):
        make_registry().create("polite", name="Asha", punctuaton="!")


def test_unknown_parameter_lists_accepted_parameters():
    with pytest.raises(ConfigError, match="accepted: name, punctuation"):
        make_registry().create("polite", name="Asha", colour="red")


def test_missing_required_parameter_is_a_config_error():
    with pytest.raises(ConfigError, match="missing required parameter\\(s\\): name"):
        make_registry().create("polite")


def test_provider_with_var_keyword_accepts_any_parameter():
    registry: Registry[object] = Registry("greeter")

    @registry.register("open")
    class Open:
        def __init__(self, **options: object) -> None:
            self.options = options

    created = registry.create("open", anything=1)

    assert isinstance(created, Open)
    assert created.options == {"anything": 1}


def test_registries_are_independent_per_interface():
    llms: Registry[object] = Registry("llm")
    embedders: Registry[object] = Registry("embedder")

    @llms.register("local")
    class LocalLLM: ...

    @embedders.register("local")
    class LocalEmbedder: ...

    assert llms.get("local") is LocalLLM
    assert embedders.get("local") is LocalEmbedder


def test_import_plugins_runs_registration_in_the_named_module(tmp_path: Path, monkeypatch):
    plugin = tmp_path / "docqa_test_plugin.py"
    plugin.write_text(
        textwrap.dedent(
            """
            from docqa_core.registry import Registry

            REGISTRY: Registry[object] = Registry("plugin")


            @REGISTRY.register("from_plugin")
            class FromPlugin: ...
            """
        )
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delitem(sys.modules, "docqa_test_plugin", raising=False)

    import_plugins(["docqa_test_plugin"])

    assert "from_plugin" in sys.modules["docqa_test_plugin"].REGISTRY


def test_import_plugins_reports_a_missing_module_as_config_error():
    with pytest.raises(ConfigError, match="plugin module 'docqa_no_such_plugin' could not"):
        import_plugins(["docqa_no_such_plugin"])
