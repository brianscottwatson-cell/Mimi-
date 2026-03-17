# Quick Start Guide 🚀

Get your Multi-Agent AI System running in 5 minutes!

## Step 1: Install Dependencies

```bash
# Make sure you're in the project directory
cd anthropic-test

# Activate virtual environment (if not already active)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

## Step 2: Set Your API Key

Choose one of these methods:

### Option A: Create a .env file (Recommended)
```bash
cp .env.example .env
# Edit .env and add your key:
# ANTHROPIC_API_KEY=sk-ant-...
```

### Option B: Export in Terminal
```bash
export ANTHROPIC_API_KEY='sk-ant-api03-your-key-here'
```

### Option C: Add to your shell profile
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Get your API key from:** https://console.anthropic.com/

## Step 3: Choose Your Interface

### Terminal Interface (Computer)
```bash
python main.py terminal
```

Then just type your questions!

```
You: Research the latest AI trends for 2026
[research specialist]
Based on my research, here are the key AI trends...
```

### Web Interface (Phone/Browser)
```bash
python main.py web
```

Then open your browser to:
- **On your computer:** http://localhost:8000
- **On your phone:** http://[your-computer-ip]:8000

To find your computer's IP:
```bash
# Mac/Linux:
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows:
ipconfig | findstr IPv4
```

## Step 4: Start Using It!

Try these example prompts:

```
"Research the latest trends in AI for 2026"
"Create an SEO strategy for my e-commerce site"
"Help me plan a marketing campaign for a new app"
"Build a web application that displays weather data"
"Create a project plan for developing a mobile app"
"Analyze the best digital marketing channels for B2B SaaS"
```

## Terminal Commands

While in terminal mode:
- `help` - Show available commands
- `agents` - List all specialized agents
- `status` - Show system status
- `model` - Switch between Claude and Kimi
- `reset` - Clear conversation history
- `quit` - Exit

## Specialized Agents Available

1. **Research Agent** - Thorough research and analysis
2. **Marketing Agent** - Marketing strategies and campaigns
3. **SEO Agent** - Search engine optimization
4. **Digital Marketing Agent** - Multi-channel digital marketing
5. **Project Management Agent** - Project planning and management
6. **Web Development Agent** - Full-stack web development

The primary agent automatically routes your requests to the right specialist!

## Troubleshooting

### "No API keys found"
- Make sure you've set `ANTHROPIC_API_KEY` in your environment
- Check that you're using the correct format: `export ANTHROPIC_API_KEY='sk-ant-...'`
- Try running: `echo $ANTHROPIC_API_KEY` to verify it's set

### "Module not found"
- Make sure you've run: `pip install -r requirements.txt`
- Verify you're in the project directory
- Check that your virtual environment is activated

### "Port already in use"
- Change the port: `PORT=8080 python main.py web`
- Or kill the process using port 8000

### Can't connect from phone
- Make sure your phone and computer are on the same network
- Use your computer's local IP address (not localhost)
- Check your firewall settings

## Need Help?

- Read the full [README.md](README.md) for detailed documentation
- Run `python test_setup.py` to verify your setup
- Check the [API documentation](http://localhost:8000/docs) when running web mode

## Next Steps

Once you're comfortable:
1. Try switching models with the `model` command
2. Deploy to Railway or Heroku for 24/7 access
3. Customize agent prompts in `agents/specialized_agents.py`
4. Add more tools in `agents/tools.py`

Happy building! 🎉
