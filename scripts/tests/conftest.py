"""Shared fixtures for the fact-check test suite.

Adds the project root and ``scripts/`` to ``sys.path`` so the tests can import
``eu_funding_competition`` and the standalone ``independent_recompute`` module,
and exposes the dataset path (overridable via the ``SOLAR_PARQUET`` env var so
the mutation test can point the suite at a tampered temporary copy).
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

import pandas as pd
import pytest

TESTS_DIR = pathlib.Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
ROOT = SCRIPTS_DIR.parent

for _p in (str(TESTS_DIR), str(SCRIPTS_DIR), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

DEFAULT_PARQUET = ROOT / "data" / "solar_power_clean.parquet"
JSON_PATH = ROOT / "data" / "eu_funding_competition.json"


def parquet_path() -> pathlib.Path:
    """Path to the dataset under test (real, unless SOLAR_PARQUET overrides)."""
    return pathlib.Path(os.environ.get("SOLAR_PARQUET", str(DEFAULT_PARQUET)))


@pytest.fixture(scope="session")
def df() -> pd.DataFrame:
    return pd.read_parquet(parquet_path())


@pytest.fixture(scope="session")
def json_data() -> dict:
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))
