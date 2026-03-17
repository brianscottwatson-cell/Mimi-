#!/bin/bash
# Deployment validation script
# Run this before deploying to check everything is ready

echo "🔍 Claudebot Deployment Validator"
echo "===================================="
echo ""

PASS=0
FAIL=0

# Check Node.js
if command -v node &> /dev/null; then
  NODE_VERSION=$(node -v)
  echo "✅ Node.js installed: $NODE_VERSION"
  ((PASS++))
else
  echo "❌ Node.js not installed"
  ((FAIL++))
fi

# Check npm
if command -v npm &> /dev/null; then
  NPM_VERSION=$(npm -v)
  echo "✅ npm installed: $NPM_VERSION"
  ((PASS++))
else
  echo "❌ npm not installed"
  ((FAIL++))
fi

# Check if .env exists
if [ -f .env ]; then
  echo "✅ .env file exists"
  ((PASS++))
else
  echo "⚠️  .env file missing (will need on deployment)"
  ((FAIL++))
fi

# Check if ANTHROPIC_API_KEY is set
if [ -f .env ] && grep -q "ANTHROPIC_API_KEY=" .env; then
  if grep "ANTHROPIC_API_KEY=sk-" .env > /dev/null; then
    echo "✅ ANTHROPIC_API_KEY configured"
    ((PASS++))
  else
    echo "❌ ANTHROPIC_API_KEY not set correctly (should start with sk-)"
    ((FAIL++))
  fi
else
  echo "⚠️  ANTHROPIC_API_KEY not found (will need on deployment)"
fi

# Check if package.json exists
if [ -f package.json ]; then
  echo "✅ package.json exists"
  ((PASS++))
else
  echo "❌ package.json not found"
  ((FAIL++))
fi

# Check if node_modules exists
if [ -d node_modules ]; then
  echo "✅ Dependencies installed (node_modules exists)"
  ((PASS++))
else
  echo "⚠️  Dependencies not installed (npm install needed)"
fi

# Check if dist exists
if [ -d dist ]; then
  echo "✅ Built for production (dist exists)"
  ((PASS++))
else
  echo "⚠️  Not built for production (npm run build needed)"
fi

# Check if Dockerfile exists
if [ -f Dockerfile ]; then
  echo "✅ Dockerfile exists"
  ((PASS++))
else
  echo "⚠️  Dockerfile not found"
fi

# Check if docker-compose.yml exists
if [ -f docker-compose.yml ]; then
  echo "✅ docker-compose.yml exists"
  ((PASS++))
else
  echo "⚠️  docker-compose.yml not found"
fi

# Check Docker
if command -v docker &> /dev/null; then
  DOCKER_VERSION=$(docker --version)
  echo "✅ Docker installed: $DOCKER_VERSION"
  ((PASS++))
else
  echo "⚠️  Docker not installed (needed for deployment)"
fi

# Check git
if command -v git &> /dev/null; then
  echo "✅ Git installed"
  ((PASS++))
else
  echo "⚠️  Git not installed"
fi

# Check if git repo exists
if [ -d .git ]; then
  echo "✅ Git repository initialized"
  ((PASS++))
else
  echo "⚠️  Not a git repository (git init needed)"
fi

# Check PostgreSQL connection
if command -v psql &> /dev/null; then
  if psql -U postgres -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
    ((PASS++))
  else
    echo "⚠️  PostgreSQL not responding"
  fi
else
  echo "⚠️  PostgreSQL client not installed (but database can be Docker)"
fi

# Summary
echo ""
echo "===================================="
echo "Summary: $PASS ✅  $FAIL ❌"
echo ""

if [ $FAIL -eq 0 ]; then
  echo "🎉 All checks passed! Ready to deploy."
  exit 0
else
  echo "⚠️  Fix the issues above before deploying."
  exit 1
fi
