import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def _load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_available_roles():
    data = _load_json("roles.json")
    return [role["name"] for role in data.get("roles", [])]


def get_role_descriptions():
    data = _load_json("roles.json")
    return {
        role["name"]: role.get("description", "")
        for role in data.get("roles", [])
    }


def get_role_factions():
    data = _load_json("roles.json")
    return {
        role["name"]: role.get("faction", "Town")
        for role in data.get("roles", [])
    }


def load_role_templates():
    data = _load_json("role_templates.json")
    return (
        data.get("templates", {}),
        data.get("pending_templates", {})
    )
