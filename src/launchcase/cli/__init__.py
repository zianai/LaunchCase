import argparse
import importlib.metadata
import json


def main():
    parser = argparse.ArgumentParser(prog="launchcase")
    parser.add_argument("command", choices=["doctor"])
    parser.parse_args()
    print(json.dumps({"status": "ok", "paid_enabled": False, "external_actions": False,
                      "versions": {p: importlib.metadata.version(p) for p in
                                   ["launchcase", "fastapi", "pydantic", "sqlalchemy", "langgraph", "openai-agents"]}}))
