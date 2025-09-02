from __future__ import annotations

from pathlib import Path


def _parse_simple_yaml(path: Path) -> dict[str, str]:
    """Return key-value pairs from a simple YAML file."""
    data: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def test_simulation_config_defaults() -> None:
    config = _parse_simple_yaml(Path("config.yml"))
    assert config["weapon_a"] == "katana"
    assert config["weapon_b"] == "shuriken"
    assert int(config["seed"]) == 6666
    assert int(config["max_simulation_seconds"]) == 120
