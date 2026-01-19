#!/bin/bash

# Gitea Mirror Setup Script for manus-toolkit
# Creates repository on local Proxmox Gitea and sets up push mirror

set -e

GITEA_URL="http://192.168.188.93:3000"
GITEA_API_URL="$GITEA_URL/api/v1"
REPO_NAME="manus-toolkit"
REPO_DESCRIPTION="Manus DNS Automation Toolkit - Deploy projects with custom domains via Cloudflare DNS"

echo "🔗 Gitea Mirror Setup for manus-toolkit"
echo "========================================"
echo ""
echo "🎯 Target: $GITEA_URL"
echo "📦 Repository: $REPO_NAME"
echo ""

# Check for token
if [ -z "$GITEA_TOKEN" ]; then
  echo "❌ GITEA_TOKEN required!"
  echo ""
  echo "Generate a token at: $GITEA_URL/user/settings/applications"
  echo ""
  echo "Then run:"
  echo "  GITEA_TOKEN=your_token ./scripts/setup-gitea-mirror.sh"
  echo ""
  echo "Or export it:"
  echo "  export GITEA_TOKEN=your_token"
  echo "  ./scripts/setup-gitea-mirror.sh"
  exit 1
fi

# Verify token and get username
echo "🔍 Verifying Gitea token..."
GITEA_USER_INFO=$(curl -s -H "Authorization: token $GITEA_TOKEN" "$GITEA_API_URL/user")

if echo "$GITEA_USER_INFO" | grep -q '"login"'; then
  GITEA_USER=$(echo "$GITEA_USER_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin)['login'])" 2>/dev/null)
  echo "✅ Authenticated as: $GITEA_USER"
else
  echo "❌ Invalid token or API error!"
  echo "Response: $GITEA_USER_INFO"
  exit 1
fi

echo ""

# Check if repo exists
echo "📦 Checking if repository exists..."
REPO_EXISTS=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $GITEA_TOKEN" "$GITEA_API_URL/repos/$GITEA_USER/$REPO_NAME")

if [ "$REPO_EXISTS" = "200" ]; then
  echo "⚠️  Repository '$REPO_NAME' already exists on Gitea"
else
  echo "📦 Creating repository '$REPO_NAME' on Gitea..."

  CREATE_RESPONSE=$(curl -s -H "Authorization: token $GITEA_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"$REPO_NAME\",
      \"description\": \"$REPO_DESCRIPTION\",
      \"private\": false,
      \"auto_init\": false
    }" \
    "$GITEA_API_URL/user/repos")

  if echo "$CREATE_RESPONSE" | grep -q '"id"'; then
    echo "✅ Repository created on Gitea!"
  else
    echo "❌ Failed to create repository!"
    echo "Response: $CREATE_RESPONSE"
    exit 1
  fi
fi

# Configure git remote
echo ""
echo "🔗 Configuring Gitea remote..."

GITEA_REMOTE_URL="$GITEA_URL/$GITEA_USER/$REPO_NAME.git"

if git remote get-url gitea >/dev/null 2>&1; then
  git remote set-url gitea "$GITEA_REMOTE_URL"
  echo "✅ Updated existing gitea remote"
else
  git remote add gitea "$GITEA_REMOTE_URL"
  echo "✅ Added gitea remote"
fi

# Push to Gitea
echo ""
echo "📤 Pushing to Gitea..."
if git push gitea main; then
  echo ""
  echo "🎉 SUCCESS!"
  echo "========================================"
  echo ""
  echo "Repository mirrored to Gitea!"
  echo ""
  echo "📍 GitHub:  https://github.com/pdubbbbbs/$REPO_NAME"
  echo "📍 Gitea:   $GITEA_URL/$GITEA_USER/$REPO_NAME"
  echo ""
  echo "💡 Push to both remotes:"
  echo "   git push origin main && git push gitea main"
  echo ""
  echo "Or create an alias:"
  echo "   git config alias.pushall '!git push origin main && git push gitea main'"
  echo "   git pushall"
else
  echo "❌ Push failed. Try manually:"
  echo "   git push gitea main"
fi
