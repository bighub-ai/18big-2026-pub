"""Central configuration of paths and course settings.

Uses pydantic-settings, so paths can be overridden via environment variables (ESHOP_*),
but the defaults work out-of-the-box after `git clone` + `uv sync`.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root = two levels above this file (src/eshop/config.py -> repo/)
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ESHOP_")

    data_dir: Path = REPO_ROOT / "data"
    seed: int = 18  # deterministic data generator (18BIG)
    n_customers: int = 2_000
    n_products: int = 300
    n_orders: int = 20_000

    @computed_field
    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @computed_field
    @property
    def bronze_dir(self) -> Path:
        return self.data_dir / "lake" / "bronze"

    @computed_field
    @property
    def silver_dir(self) -> Path:
        return self.data_dir / "lake" / "silver"

    @computed_field
    @property
    def gold_dir(self) -> Path:
        return self.data_dir / "lake" / "gold"

    @computed_field
    @property
    def quarantine_dir(self) -> Path:
        return self.data_dir / "quarantine"

    @computed_field
    @property
    def source_db(self) -> Path:
        """SQLite database acting as the 'operational system' (JDBC-like source)."""
        return self.raw_dir / "shop.sqlite"


settings = Settings()
