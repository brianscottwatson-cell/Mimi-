import anthropic

client = anthropic.Anthropic()

try:
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[{"role": "user", "content": "hi"}]
    )
    print(response.content[0].text)
except Exception as e:
    print("Error:", str(e))