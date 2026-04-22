# API Client & Settings

What the client sends, where settings live, and the bugs to fix before
shipping.

## Config schema

File: `~/Library/Preferences/photo-bomb/config.json`. Defaults from
`core/config.py::Config.defaults`:

```json
{
  "api_endpoint": "",
  "api_key": "",
  "model_name": "",
  "categories": ["memories", "todo", "research"],
  "batch_size": 100,
  "last_library_path": ""
}
```

- `api_endpoint` is the **base URL only** (e.g. `https://api.openai.com/v1`).
  The client appends `/models` and `/chat/completions`. Storing
  `https://api.openai.com/v1/chat/completions` produces 404s.
- `api_key` is plaintext. No keychain integration.
- `categories` and `batch_size` are read from defaults but no UI mutates
  them yet.

Access pattern (always):

```python
from photo_bomb.core.config import get_config
cfg = get_config()
cfg.api_endpoint                    # property accessor
cfg.update({"model_name": "gpt-4o-mini"})  # writes to disk immediately
```

## Health check (`VisionAPIClient.check_connection`)

```
GET  {endpoint}/models                  Authorization: Bearer {key}
  -> 200: returns "Connected. Available models: m1, m2, m3, m4, m5"
  -> non-200: falls through to:
POST {endpoint}/chat/completions        Authorization: Bearer {key}
       body: {"model": model or "default", "messages": []}
  -> 200: "Connection successful"
```

5-second timeout each. Returns `(success: bool, message: str)`.

Note: an empty `messages` array will be rejected by most real providers
(OpenAI requires at least one message), so this can false-negative against
strict endpoints.

## Photo analysis (`VisionAPIClient.analyze_photo`)

Sent to `POST {endpoint}/chat/completions` with `Content-Type:
application/json` and bearer auth. Body shape (abridged):

```json
{
  "model": "<model_name>",
  "messages": [
    {"role": "system", "content": "You are a photo analysis assistant. ..."},
    {"role": "user", "content": [
      {"type": "text", "text": "Classify this photo into one of these categories: ..."},
      {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<...>"}}
    ]}
  ],
  "max_tokens": 300,
  "temperature": 0.3
}
```

Expected response: a JSON object inside `choices[0].message.content` with
keys `category`, `confidence`, `tags`, `description`. If the content isn't
valid JSON, the client returns `[{"raw_response": "<content>"}]`.

30-second timeout. Errors emit `error_occurred(str)` and return `[]`.

## Known bugs in `analyze_photo`

1. **Image is not actually base64-encoded.** The current code does
   `photo_data.decode('latin1')` and shoves the raw bytes into the data
   URL. Real OpenAI-compatible endpoints will 400 this. Fix:

   ```python
   import base64
   b64 = base64.b64encode(photo_data).decode("ascii")
   ... f"data:image/jpeg;base64,{b64}" ...
   ```

2. **`Content-Type` is hard-coded to `image/jpeg`** even for PNG/HEIC
   inputs. Sniff or pass through MIME from the caller.

3. **`api_key` empty + `Authorization: Bearer ` (empty)** is sent verbatim
   when not configured; some providers 401, some 403. Either short-circuit
   in the client or guard at the call site (`MainWindow._on_analyze_clicked`
   already does the latter for the engine, but not for `check_connection`).

## Settings dialog wiring (open work)

`ui/api_settings_dialog.py` exposes `load_settings(config)` and
`save_to_config(config)` but `MainWindow.show_api_settings` calls neither -
see the two `# TODO` comments. Result: changes in the dialog are lost on
close. Wire-up is one-line each:

```python
dialog.load_settings(get_config().config)            # before exec()
if dialog.exec() == dialog.DialogCode.Accepted:
    dialog.save_to_config(get_config())              # after accept
```

## Compatible endpoints

Anything that speaks OpenAI's `/chat/completions` with image content parts:
OpenAI, OpenRouter, vLLM, LM Studio, Ollama (`/v1` shim, vision models like
`llava`, `llama3.2-vision`), most local-LLM gateways. Endpoints that don't
support image content parts will silently work for `check_connection` but
fail at analysis time.
