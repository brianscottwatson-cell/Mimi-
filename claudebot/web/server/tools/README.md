# MCP Tool Plugins

Drop JSON tool definitions in this directory to add new capabilities to Mimi.

## Example: Weather API tool

```json
{
    "name": "get_weather",
    "description": "Get current weather for a location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name or zip code"
            }
        },
        "required": ["location"]
    },
    "handler": {
        "type": "http",
        "url": "https://api.weatherapi.com/v1/current.json",
        "method": "GET",
        "headers": {
            "key": "${WEATHER_API_KEY}"
        }
    }
}
```

## Handler Types

- **http**: Makes HTTP requests. Supports `${ENV_VAR}` expansion in URLs and headers.
- Headers and URLs can reference environment variables with `${VAR_NAME}` syntax.
