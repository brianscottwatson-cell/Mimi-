# Claudebot Deployment Guide

Choose your deployment method:

1. **Docker** (Local or any cloud)
2. **Railway.app** (Easiest, recommended)
3. **Render** (Alternative, also easy)
4. **Vercel** (Frontend only)

---

## Option 1: Docker (Local)

Run Claudebot with Docker & Docker Compose locally.

### Prerequisites

- Docker Desktop ([download](https://www.docker.com/products/docker-desktop))

### Setup

```bash
cd claudebot

# Build and run
docker-compose up --build

# On first run, initialize database
docker exec claudebot_app_1 npm run db:push
```

### Access

- Web: `http://localhost:3000`
- API: `http://localhost:3000/api`
- Database: `localhost:5432`

### Stop

```bash
docker-compose down
```

### Cleanup

```bash
docker-compose down -v  # Remove volumes too
```

---

## Option 2: Railway.app (Recommended)

Deploy with one click. Free tier available.

### 1. Create Railway Account

Visit [railway.app](https://railway.app) and sign up with GitHub.

### 2. Connect Repository

```bash
# From claudebot directory
git init
git add .
git commit -m "Initial commit"
```

Then in Railway dashboard:
- Click "New Project"
- Select "Deploy from GitHub"
- Connect your repo
- Select `claudebot` folder

### 3. Add PostgreSQL

In Railway dashboard:
- Click "Add Service"
- Select "PostgreSQL"
- Connect to project

### 4. Configure Environment

Railway auto-detects Node.js. Set environment variables:

```
ANTHROPIC_API_KEY = sk-ant-...
ELEVENLABS_API_KEY = ... (optional)
DATABASE_URL = (auto-set by Railway)
NODE_ENV = production
```

### 5. Deploy

- Push to GitHub
- Railway auto-deploys on commit
- View live URL in Railway dashboard

### Costs

- **Free tier**: 5 GB storage, 500 hours/month (enough for low usage)
- **Paid**: $5/month per service

---

## Option 3: Render

Similar to Railway, alternative platform.

### 1. Create Render Account

Visit [render.com](https://render.com) and sign up.

### 2. Create Web Service

- Click "New +"
- Select "Web Service"
- Connect GitHub repo
- Select `claudebot` folder

### 3. Configure

**Build Command:**
```
npm install && npm run build
```

**Start Command:**
```
node dist/server.js
```

**Environment:**
```
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
NODE_ENV=production
```

### 4. Add PostgreSQL

- In Render dashboard, create "PostgreSQL" service
- Copy `DATABASE_URL`
- Add to Web Service environment

### 5. Deploy

- Save and deploy
- Render builds and serves your app

### Costs

- **Free tier**: Limited (sleeps after 15 min inactivity)
- **Paid**: $7/month+ per service

---

## Option 4: Vercel (Frontend Only)

For hosting just the React frontend, with backend on separate service.

### 1. Create Frontend-Only Build

```bash
cd claudebot/client
npm install
npm run build
```

### 2. Deploy to Vercel

```bash
npm i -g vercel
vercel
```

### 3. Configure API Proxy

In `vercel.json`:
```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://your-api.railway.app/api/$1" }
  ]
}
```

### Costs

- **Free tier**: Perfect for static sites
- For this project, combine with Railway for backend

---

## Comparison

| Feature | Docker | Railway | Render | Vercel |
|---------|--------|---------|--------|--------|
| Ease | Medium | Easy | Easy | Easy |
| Cost | Free (self-hosted) | $0-5/mo | $7+/mo | Free frontend |
| Scaling | Manual | Auto | Auto | Auto |
| Database | Included | Included | Separate | Not applicable |
| CLI Support | Yes | Yes | Yes | No |
| Voice/Files | Yes | Yes | Yes | No (frontend) |

**Recommendation:** Start with **Railway.app** (easiest, free tier sufficient).

---

## Securing Your Deployment

### 1. Protect API Keys

**Never commit** `.env` files:

```bash
git add .gitignore  # Should have .env
git rm --cached .env  # If accidentally committed
```

Use platform's secret management:
- Railway: Environment variables UI
- Render: Environment variables UI
- Docker: Use `.env` file locally only

### 2. Database Security

- Change default PostgreSQL password
- Use strong credentials in production
- Enable SSL connections
- Restrict database access to app only

### 3. API Rate Limiting

Add to `server/index.ts`:

```typescript
import rateLimit from "express-rate-limit";

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100, // limit each IP to 100 requests per windowMs
});

app.use("/api/", limiter);
```

### 4. CORS Security

Update `server/index.ts`:

```typescript
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(",") || ["http://localhost:3000"],
  credentials: true,
}));
```

### 5. Enable HTTPS

All major platforms (Railway, Render) provide free SSL.

---

## Monitoring & Logs

### Railway

```bash
railway logs
railway logs --follow  # Watch in real-time
```

### Render

Dashboard → Logs tab

### Docker

```bash
docker-compose logs
docker-compose logs -f  # Follow
```

---

## Scaling Tips

### 1. Database Connection Pooling

Add to `.env`:

```
DATABASE_POOL_SIZE=10
```

### 2. Redis Cache (Optional)

Cache frequently accessed conversations:

```bash
# Add to docker-compose.yml
cache:
  image: redis:7-alpine
  ports:
    - "6379:6379"
```

### 3. Horizontal Scaling

- Railway: Increase replica count
- Render: Enable auto-scaling
- Docker: Use load balancer (nginx)

---

## Troubleshooting

### "Cannot connect to database"

```bash
# Check database URL format
postgresql://user:password@host:port/dbname

# Verify PostgreSQL is running
psql -c "SELECT version();"
```

### "Build fails on platform"

```bash
# Ensure build dependencies
npm ci --also=dev
npm run build
```

### "Port already in use"

```bash
# Find process using port 3000
lsof -i :3000
kill -9 <PID>
```

### "File uploads not working on Railway"

Railway uses ephemeral filesystem. Use cloud storage instead:

```typescript
// Consider: AWS S3, Cloudinary, or similar
```

---

## Next Steps

1. **Choose platform:** Railway recommended for beginners
2. **Set up repository:** Push to GitHub
3. **Deploy:** Follow platform-specific guide
4. **Test:** Visit deployed URL
5. **Monitor:** Check logs and performance
6. **Scale:** Add database pooling as needed

## Support

For issues:
- Railway docs: [railway.app/docs](https://railway.app/docs)
- Render docs: [render.com/docs](https://render.com/docs)
- Vercel docs: [vercel.com/docs](https://vercel.com/docs)
