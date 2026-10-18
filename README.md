# TDS Config Precedence API

A FastAPI implementation for the config precedence assignment.

## Endpoint

`GET /effective-config?set=port=9000&set=debug=true`

Precedence, low to high: hardcoded defaults -> `config.development.yaml` -> `.env` -> host OS `APP_*` environment variables -> repeated `set=key=value` query parameters.

The `NUM_WORKERS` alias maps to `workers`. `port` and `workers` are integers; `debug` is a boolean; remaining values are strings. `api_key` is always masked as `****` in output.

## Deploy on Render

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Root directory: leave blank when these files are in the repository root.

The assigned OS values are included as code fallbacks. You can also add the following in Render's Environment settings to use real process environment variables:

- `APP_PORT=8011`
- `APP_WORKERS=3`
- `APP_DEBUG=true`
- `APP_LOG_LEVEL=warning`
- `APP_API_KEY=3qikgerqv1`

The API enables cross-origin GET and OPTIONS requests.
