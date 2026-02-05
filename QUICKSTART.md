# Quick Start Guide

**Get Claudebot running in 5 minutes:**

## Option 1: Docker (Fastest)

```bash
cd claudebot
./deploy-docker.sh
```

Then open: `http://localhost:3000`

## Option 2: Railway (Cloud)

```bash
cd claudebot
git init && git add . && git commit -m "Initial"
./deploy-railway.sh
```

Then follow the prompts in Railway dashboard.

## Option 3: Manual Local

```bash
# Install dependencies
npm install

# Start PostgreSQL
psql -U postgres -c "CREATE DATABASE claudebot;"

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Build
npm run build

# Start
npm start
```

---

## Verify Installation

### Web App
- Open `http://localhost:3000`
- Should see chat interface with green text

### API Health Check
```bash
curl http://localhost:3000/api/health
# Should return: {"status":"ok","timestamp":"..."}
```

### CLI (if installed)
```bash
npm run cli
# Type: /help
```

---

## Common Issues

**"Cannot connect to database"**
- Check PostgreSQL is running: `psql --version`
- Verify DATABASE_URL in `.env`

**"404 on /api/conversations"**
- Run: `npm run db:push`
- Restart server: `npm start`

**"Module not found"**
- Clear node_modules: `rm -rf node_modules && npm install`
- Rebuild: `npm run build`

---

## Next

✅ [Local setup complete?] → Choose cloud platform in DEPLOYMENT.md
✅ [Deployed to cloud?] → Share URL and start using!
