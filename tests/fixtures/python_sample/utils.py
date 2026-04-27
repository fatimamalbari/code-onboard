"""Utility functions."""

import json
from models import User


def helper_function(name: str) -> str:
    return f"Processed: {name}"


def load_config(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


async def fetch_data(url: str) -> dict:
    return {"url": url, "data": []}
