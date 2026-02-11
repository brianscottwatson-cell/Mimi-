import anthropic
client = anthropic.Anthropic()
try:
    resp = client.messages.create(
        model="claude-sonnet-4",
        max_tokens=100,
        messages=[{"role": "user", "content": "hi"}]
    )
    print(resp.content[0].text)
except Exception as e:
    print(e)