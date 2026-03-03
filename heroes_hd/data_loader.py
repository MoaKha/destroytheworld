"""Data loading utilities for Heroes HD."""
import json
import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BASE_DIR, "data")

_cache: dict = {}


class DataLoader:
    """Loads and caches game data from JSON files."""

    @staticmethod
    def load_creatures() -> dict[str, dict]:
        """Returns flat dict: creature_id -> creature_data."""
        if "creatures" in _cache:
            return _cache["creatures"]
        path = os.path.join(_DATA_DIR, "creatures.json")
        with open(path, "r") as f:
            raw = json.load(f)
        flat: dict[str, dict] = {}
        for faction, creature_list in raw.items():
            for c in creature_list:
                flat[c["id"]] = c
        _cache["creatures"] = flat
        return flat

    @staticmethod
    def load_creatures_by_faction() -> dict[str, list[dict]]:
        """Returns dict: faction -> list of creature dicts."""
        if "creatures_by_faction" in _cache:
            return _cache["creatures_by_faction"]
        path = os.path.join(_DATA_DIR, "creatures.json")
        with open(path, "r") as f:
            data = json.load(f)
        _cache["creatures_by_faction"] = data
        return data

    @staticmethod
    def load_spells() -> dict[str, list[dict]]:
        """Returns dict: school -> list of spell dicts."""
        if "spells" in _cache:
            return _cache["spells"]
        path = os.path.join(_DATA_DIR, "spells.json")
        with open(path, "r") as f:
            data = json.load(f)
        _cache["spells"] = data
        return data

    @staticmethod
    def load_spells_flat() -> dict[str, dict]:
        """Returns flat dict: spell_id -> spell_data."""
        if "spells_flat" in _cache:
            return _cache["spells_flat"]
        spells_by_school = DataLoader.load_spells()
        flat: dict[str, dict] = {}
        for school, spell_list in spells_by_school.items():
            for s in spell_list:
                s["school"] = school
                flat[s["id"]] = s
        _cache["spells_flat"] = flat
        return flat

    @staticmethod
    def load_artifacts() -> dict[str, list[dict]]:
        """Returns dict: class -> list of artifact dicts."""
        if "artifacts" in _cache:
            return _cache["artifacts"]
        path = os.path.join(_DATA_DIR, "artifacts.json")
        with open(path, "r") as f:
            data = json.load(f)
        _cache["artifacts"] = data
        return data

    @staticmethod
    def load_artifacts_flat() -> dict[str, dict]:
        """Returns flat dict: artifact_id -> artifact_data."""
        if "artifacts_flat" in _cache:
            return _cache["artifacts_flat"]
        arts_by_class = DataLoader.load_artifacts()
        flat: dict[str, dict] = {}
        for cls, art_list in arts_by_class.items():
            for a in art_list:
                flat[a["id"]] = a
        _cache["artifacts_flat"] = flat
        return flat

    @staticmethod
    def clear_cache():
        _cache.clear()
