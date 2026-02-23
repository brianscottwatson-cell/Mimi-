# Deployment Checklist

## Pre-Deployment

- [ ] All dependencies installed: `npm install`
- [ ] Environment variables configured: `.env` file created
- [ ] Database created: `createdb claudebot`
- [ ] Schema migrated: `npm run db:push`
- [ ] Local development tested: `npm run dev` works
- [ ] CLI tested: `npm run cli` works
- [ ] Code committed: `git add . && git commit -m "..."`

## Docker Deployment

- [ ] Docker Desktop installed
- [ ] Docker image builds: `docker build -t claudebot .`
- [ ] docker-compose runs: `docker-compose up --build`
- [ ] Database initializes: `docker exec <container> npm run db:push`
- [ ] Web accessible: `http://localhost:3000`
- [ ] Health check passes: `curl http://localhost:3000/api/health`
- [ ] Logs clean: `docker-compose logs` (no errors)

## Railway Deployment

- [ ] Railway account created
- [ ] GitHub repo connected
- [ ] PostgreSQL service added
- [ ] Environment variables set:
  - [ ] `ANTHROPIC_API_KEY`
  - [ ] `ELEVENLABS_API_KEY` (optional)
  - [ ] `DATABASE_URL` (auto-set)
  - [ ] `NODE_ENV=production`
- [ ] Build command configured: `npm run build`
- [ ] Start command configured: (auto-detected)
- [ ] First deployment succeeded
- [ ] Health check working: `curl https://your-app.railway.app/api/health`
- [ ] Web app loads at deployed URL
- [ ] Database initialized on Railway

## Render Deployment

- [ ] Render account created
- [ ] GitHub repo connected
- [ ] Web service created
- [ ] PostgreSQL service created
- [ ] Environment variables set:
  - [ ] `ANTHROPIC_API_KEY`
  - [ ] `ELEVENLABS_API_KEY` (optional)
  - [ ] `DATABASE_URL` (from PostgreSQL service)
  - [ ] `NODE_ENV=production`
- [ ] Build command: `npm install && npm run build`
- [ ] Start command: `node dist/server.js`
- [ ] First deployment succeeded
- [ ] Health check working: `curl https://your-app.render.onrender.com/api/health`

## Vercel Deployment (Frontend Only)

- [ ] Vercel account created
- [ ] Frontend deployed: `vercel --prod`
- [ ] Environment variables configured in Vercel UI
- [ ] API proxy configured: `vercel.json` set up
- [ ] Custom domain added (optional)

## Post-Deployment

- [ ] SSL/HTTPS working (automatic on Railway/Render)
- [ ] Database backups configured
- [ ] Monitoring enabled (platform-specific)
- [ ] Error tracking set up (optional: Sentry)
- [ ] Domain configured (custom domain)
- [ ] Email notifications enabled for alerts

## Testing

- [ ] Web app loads without errors
- [ ] Can create conversation
- [ ] Can send messages
- [ ] API responds to requests
- [ ] Database stores data
- [ ] File upload works (if filesystem available)
- [ ] Voice features work (if ElevenLabs key set)

## Performance

- [ ] Page loads in < 3 seconds
- [ ] API response time < 500ms
- [ ] Database queries optimized
- [ ] Frontend bundle size acceptable

## Security

- [ ] API keys not in version control
- [ ] HTTPS enabled
- [ ] Database credentials secure
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Input validation in place

## Monitoring & Alerts

- [ ] Logs accessible and clean
- [ ] Health checks passing
- [ ] Error alerts configured
- [ ] Uptime monitoring enabled
- [ ] Performance metrics tracked

---

**Deployment Date:** _____________

**Platform:** ☐ Docker ☐ Railway ☐ Render ☐ Vercel ☐ Other

**Deployed URL:** _________________________________

**Status:** ☐ Working ☐ Issues to fix

**Notes:**

_________________________________________________________________________

_________________________________________________________________________
