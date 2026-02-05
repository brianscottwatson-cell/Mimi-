# Deployment Troubleshooting Guide

## Database Issues

### "Cannot connect to database"

**Symptoms:**
- `Error: connect ECONNREFUSED 127.0.0.1:5432`
- `Connection error: no such host`

**Solutions:**

1. Check if PostgreSQL is running:
```bash
# macOS
brew services list | grep postgres

# Linux
sudo service postgresql status

# Docker
docker ps | grep postgres
```

2. Verify DATABASE_URL format:
```bash
# Correct format
postgresql://username:password@localhost:5432/claudebot

# For local testing
postgresql://postgres:password@localhost:5432/claudebot
```

3. Restart PostgreSQL:
```bash
# macOS
brew services restart postgresql@15

# Docker
docker-compose restart db
```

4. Check if database exists:
```bash
createdb claudebot  # If it doesn't exist
psql -l | grep claudebot
```

---

### "Database connection pool exhausted"

**Symptoms:**
- Application runs but API calls hang or timeout
- Works with few users, fails under load

**Solution:**

Add connection pooling to `server/db.ts`:

```typescript
const pool = new Pool({
  max: 20,  // Max connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

Or use PgBouncer (production):

```bash
# Install PgBouncer
brew install pgbouncer

# Configure /usr/local/etc/pgbouncer.ini
[databases]
claudebot = host=localhost port=5432 dbname=claudebot

# Start
pgbouncer -d /usr/local/etc/pgbouncer.ini
```

---

### "Migration failed: relation does not exist"

**Symptoms:**
- `Relation "conversations" does not exist`
- `Table schema.ts doesn't match database`

**Solution:**

1. Manually run migrations:
```bash
npm run db:push -- --force
```

2. Or reset database (⚠️ deletes all data):
```bash
dropdb claudebot
createdb claudebot
npm run db:push
```

3. Check migration history:
```bash
npm run db:studio
```

---

## API & Server Issues

### "Port 3000 already in use"

**Solution:**

```bash
# Find process using port 3000
lsof -i :3000

# Kill process
kill -9 <PID>

# Or use different port
PORT=3001 npm start
```

---

### "Build fails: module not found"

**Symptoms:**
- `Cannot find module '@anthropic-ai/sdk'`
- `Module 'react' not found`

**Solution:**

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check specific package
npm ls @anthropic-ai/sdk

# Install missing package
npm install @anthropic-ai/sdk
```

---

### "API endpoints return 404"

**Symptoms:**
- `POST /api/conversations` → 404 Not Found
- Web loads but API fails

**Solution:**

1. Check if server is running:
```bash
curl http://localhost:3000/api/health
```

2. Verify Express routes in `server/index.ts`:
```bash
# Should see routes defined
grep "app.post\|app.get" server/index.ts
```

3. Check if TypeScript compiled:
```bash
npm run build
# Should create dist/server.js
```

4. Start server with output:
```bash
npm start  # Should log "Server running on port 3000"
```

---

### "CORS error: blocked by cross-origin"

**Symptoms:**
- Frontend loads but API calls blocked
- Browser console: `Access to XMLHttpRequest blocked by CORS policy`

**Solution:**

In `server/index.ts`:

```typescript
const allowedOrigins = [
  "http://localhost:3000",
  "http://localhost:5173",  // Vite dev server
  "https://yourdomain.com"   // Production
];

app.use(cors({
  origin: allowedOrigins,
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE"],
}));
```

Then restart server.

---

## Frontend Issues

### "Vite dev server not loading changes"

**Symptoms:**
- Changes to React components don't appear
- HMR (Hot Module Reload) not working

**Solution:**

```bash
# Clear cache
rm -rf client/.vite

# Restart dev server
npm run dev

# Or restart with specific port
npm run dev -- --port 3000
```

---

### "Module resolution errors in browser"

**Symptoms:**
- Console errors about missing modules
- Components won't load

**Solution:**

```bash
# Check imports are correct
grep -r "from ['\"]" client/src | grep -v node_modules

# Rebuild frontend
cd client
npm run build

# Check output in dist/
ls -la client/dist/
```

---

## Docker Issues

### "Docker image build fails"

**Symptoms:**
- `FAILED [2/7] RUN npm ci --omit=dev`
- Build exits with error code

**Solution:**

```bash
# Clear Docker cache
docker system prune -a

# Build with no cache
docker build --no-cache -t claudebot .

# Check Dockerfile syntax
docker build --check
```

---

### "Container exits immediately"

**Symptoms:**
- `docker-compose up` shows container exiting
- `Exit code: 1` or similar

**Solution:**

```bash
# View container logs
docker-compose logs app

# Run container in foreground to see errors
docker-compose up --no-daemon app

# Check if port is conflicting
lsof -i :3000

# Inspect image
docker inspect claudebot
```

---

### "docker-compose: service not found"

**Symptoms:**
- `ERROR: Service 'db' not found`
- `compose unknown command`

**Solution:**

```bash
# Update Docker Desktop or Docker Engine
docker --version  # Should be 20.10+

# Use full docker-compose command if old version
docker-compose --version

# Or use newer syntax
docker compose up  # (note: no hyphen)
```

---

## Railway Deployment Issues

### "Build succeeds but app crashes immediately"

**Symptoms:**
- Railway build says "Success"
- App shows "Application crashed"

**Solution:**

1. Check logs in Railway dashboard:
   - Click project → View logs
   - Look for error messages

2. Verify start command:
   - Should be `node dist/server.js`
   - Or `npm start` if package.json is set up

3. Check environment variables:
   ```bash
   # All required vars must be set:
   - ANTHROPIC_API_KEY
   - DATABASE_URL
   ```

---

### "Database connection fails on Railway"

**Symptoms:**
- App connects locally but fails on Railway
- `Cannot connect to database` error in logs

**Solution:**

1. Railway auto-sets `DATABASE_URL` from PostgreSQL plugin
2. Verify it exists in Variables tab
3. Format should be: `postgresql://user:pass@host:5432/dbname`
4. Manually set if missing:
   ```
   DATABASE_URL=postgresql://postgres:...@containers-us-west-...
   ```

---

### "File uploads not working"

**Symptoms:**
- Upload works locally, fails on Railway
- File save error in production

**Solution:**

Railway uses ephemeral filesystem (files deleted on restart). Use cloud storage instead:

```typescript
// Install AWS S3 or similar
npm install aws-sdk

// Modify server/files.ts to use S3 instead of /tmp
```

Or use Railway's built-in file storage service.

---

## Render Deployment Issues

### "Deployment stuck at building"

**Symptoms:**
- Build runs for > 10 minutes
- No error message

**Solution:**

1. Check build logs in Render dashboard
2. Render may be installing optional dependencies
3. Add to `package.json`:
   ```json
   "engines": {
     "node": "18",
     "npm": "9"
   }
   ```

4. Use npm ci instead of npm install:
   ```
   npm ci --omit=dev
   ```

---

### "PostgreSQL service creation failed"

**Symptoms:**
- Cannot add PostgreSQL to Render project
- Error during setup

**Solution:**

1. Check Render account plan (requires paid plan for databases)
2. Use free tier but with external database:
   - Create database on Railway or Supabase
   - Copy `DATABASE_URL`
   - Set manually in Render environment

---

## Performance Issues

### "API responses are slow (>5s)"

**Symptoms:**
- Conversations load slowly
- `/api/conversations` takes > 5 seconds

**Solutions:**

1. Check database performance:
```bash
# Analyze queries
npm run db:studio
# Check slow query logs
```

2. Add indexes to frequently queried columns:
```typescript
// In shared/schema.ts
export const conversations = pgTable("conversations", {
  id: serial().primaryKey(),
  userId: text().notNull().unique(),  // Add .unique() for index
  createdAt: timestamp().defaultNow(),
});
```

3. Use pagination:
```typescript
// Limit results in server/storage.ts
db.select().from(conversations).limit(50).offset(0)
```

---

### "High CPU usage"

**Symptoms:**
- CPU constantly at 100%
- Application becomes unresponsive

**Solutions:**

1. Check for infinite loops in server code
2. Disable debug logging:
   ```bash
   NODE_DEBUG="" npm start
   ```

3. Monitor memory:
   ```bash
   # macOS
   top -p <PID>
   
   # Linux
   ps aux | grep node
   ```

---

## General Debugging

### Enable debug logging:

```bash
# Node debug
NODE_DEBUG=* npm start

# Specific module
DEBUG=express:* npm start
```

### Check environment variables are loaded:

```bash
# In server code
console.log("Database URL:", process.env.DATABASE_URL?.substring(0, 20) + "...");
console.log("API Key:", process.env.ANTHROPIC_API_KEY ? "✓ Set" : "✗ Missing");
```

### Verify all services are running:

```bash
# Local
ps aux | grep -E "node|postgres"

# Docker
docker ps

# Railway
railway status

# Render
(Check Render dashboard)
```

---

## Getting Help

If issue persists:

1. **Check logs:**
   - Local: Terminal output
   - Docker: `docker-compose logs`
   - Railway: Dashboard logs tab
   - Render: Dashboard logs tab

2. **Verify configuration:**
   - `.env` file exists and correct
   - DATABASE_URL format correct
   - All API keys present

3. **Try fresh deployment:**
   ```bash
   rm -rf dist node_modules
   npm install
   npm run build
   npm start
   ```

4. **Community support:**
   - Railway docs: [railway.app/docs](https://railway.app/docs)
   - Render docs: [render.com/docs](https://render.com/docs)
   - Anthropic API docs: [docs.anthropic.com](https://docs.anthropic.com)
   - Node.js docs: [nodejs.org/docs](https://nodejs.org/docs)

---

**Last Updated:** $(date)
