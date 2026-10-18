from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

# Layer 1: hardcoded defaults from the assignment.
DEFAULTS: dict[str, Any] = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# The assignment's simulated OS environment values. Real environment variables
# supplied by the host take precedence over these fallbacks.
ASSIGNED_OS_FALLBACKS = {
    "APP_PORT": "8011",
    "APP_WORKERS": "3",
    "APP_DEBUG": "true",
    "APP_LOG_LEVEL": "warning",
    "APP_API_KEY": "3qikgerqv1",
}

ALIASES = {
    "app_port": "port",
    "app_workers": "workers",
    "num_workers": "workers",
    "app_debug": "debug",
    "app_log_level": "log_level",
    "app_api_key": "api_key",
}


def coerce(key: str, value: Any) -> Any:
    """Apply the assignment's type conversion rules."""
    text = str(value)
    if key in {"port", "workers"}:
        return int(text)
    if key == "debug":
        return text.strip().lower() in {"true", "1", "yes", "on"}
    return text


def canonical_key(key: str) -> str:
    lowered = key.strip().lower()
    return ALIASES.get(lowered, lowered)


def load_config(cli_sets: list[str] | None = None) -> dict[str, Any]:
    config: dict[str, Any] = dict(DEFAULTS)

    # Layer 2: environment-specific YAML file.
    yaml_path = BASE_DIR / "config.development.yaml"
    if yaml_path.exists():
        loaded = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        if isinstance(loaded, dict):
            for key, value in loaded.items():
                k = canonical_key(str(key))
                if k in config:
                    config[k] = coerce(k, value)

    # Layer 3: .env values. NUM_WORKERS is an alias for workers.
    env_file_values = dotenv_values(BASE_DIR / ".env")
    for source_key, value in env_file_values.items():
        if value is None:
            continue
        key = canonical_key(source_key)
        if key in config:
            config[key] = coerce(key, value)

    # Layer 4: actual host OS environment variables (with assignment-specific
    # fallback values so the app still works if host variables were not entered).
    os_layer = dict(ASSIGNED_OS_FALLBACKS)
    os_layer.update(os.environ)
    for source_key, value in os_layer.items():
        if not source_key.startswith("APP_") or value is None:
            continue
        key = canonical_key(source_key)
        if key in config:
            config[key] = coerce(key, value)

    # Highest precedence: repeated ?set=key=value query parameters.
    for item in cli_sets or []:
        key_text, separator, value_text = item.partition("=")
        if not separator:
            continue
        key = canonical_key(key_text)
        if key in config:
            try:
                config[key] = coerce(key, value_text)
            except (TypeError, ValueError):
                # Ignore a malformed override instead of crashing the endpoint.
                continue

    # Never expose the actual key, including when a query override supplies it.
    config["api_key"] = "****"
    return config


app = FastAPI(title="TDS Config Precedence API", version="1.0.0")

# The assignment page needs browser cross-origin access. No credentials are used,
# so wildcard ACAO is valid and supports the exam page's origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/effective-config")
async def effective_config(request: Request) -> dict[str, Any]:
    return load_config(request.query_params.getlist("set"))


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "config-precedence-api", "endpoint": "GET /effective-config"}
