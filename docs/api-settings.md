# API Settings

Configure your OpenAI-compatible vision language model endpoint.

## Accessing Settings

1. Launch Photo Boss
2. Go to **File → Settings...** in the menu bar
3. Fill in the fields and click **Save**

## Configuration Fields

| Field | Description | Example |
|-------|-------------|---------|
| API Endpoint | URL of your OpenAI-compatible endpoint | `https://api.openai.com/v1/chat/completions` |
| Model Name | The model to use for analysis | `gpt-4o-mini`, `llama-3.2-vision` |
| API Key | Your API key for the service | `sk-...` |

## Supported Vision Models

Photo Boss works with any OpenAI-compatible endpoint that supports vision models:

### Public Services
- **OpenAI GPT-4o-mini** - Recommended, cost-effective
- **Anthropic Claude 3.5 Sonnet** (via compatible API)
- **Google Gemini 1.5 Flash**

### Local/On-Premise
- **Ollama** with vision models: `llava`, `baklava`, `llama-3.2-vision`
  - Endpoint: `http://localhost:11434/v1/chat/completions`
- **vLLM** with multimodal support
- **LM Studio** (local server mode)

## Analysis Prompt

Photos are sent to the vision model with this system prompt:

> You are a photo categorization assistant. Analyze the attached image and determine which category best fits: **memories**, **todo**, or **research**.
>
> - **memories**: Personal/family photos, important moments, events
> - **todo**: Photos containing tasks, instructions, recipes, lists, diagrams that need action
> - **research**: Reference materials, documents, articles for study

Return JSON:
```json
{
  "category": "memories|todo|research",
  "confidence": 0.95,
  "reasoning": "Brief explanation of your decision"
}
```

## Health Check

The API Settings dialog includes a **Test Connection** button that:
1. Sends a minimal test request to the endpoint
2. Validates API key validity
3. Confirms model name is accessible
4. Reports success or error in status bar

## Security Notes

- API keys are stored unencrypted in `~/Library/Preferences/photo-boss/config.json`
- Consider using environment variables for production use (TODO: feature)
- Keys are masked when displayed in the UI
