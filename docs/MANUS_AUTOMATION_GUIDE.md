# Manus Automation Guide

Complete reference documentation for the Manus DNS Automation Toolkit.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Level 1: Basic DNS Manager](#level-1-basic-dns-manager)
6. [Level 2: Automated Deployment](#level-2-automated-deployment)
7. [Level 3: Claude CLI Integration](#level-3-claude-cli-integration)
8. [Workflow Examples](#workflow-examples)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

---

## Overview

The Manus Automation Toolkit provides three levels of automation for managing DNS records and deploying Manus projects:

| Level | Tool | Purpose |
|-------|------|---------|
| 1 | `manus-dns-manager.py` | Direct Cloudflare API control |
| 2 | `manus-deploy-auto.py` | Automated deployment with monitoring |
| 3 | `claude-manus-helper.sh` | Interactive Claude CLI integration |

### Key Features

- **One-Command Deployment**: Deploy a Manus project with a single command
- **Real-Time Monitoring**: Watch DNS propagation and site availability
- **Project Tracking**: SQLite database for deployment history
- **Multi-Domain Support**: Works with all domains in your Cloudflare account
- **Claude CLI Ready**: Natural language command support

---

## Architecture

```
manus-toolkit/
├── scripts/
│   ├── manus-dns-manager.py    # Level 1: DNS API
│   ├── manus-deploy-auto.py    # Level 2: Deployment
│   ├── manus-dns               # Bash wrapper
│   └── claude-manus-helper.sh  # Level 3: Interactive CLI
├── config/
│   ├── .env                    # API tokens (gitignored)
│   ├── .env.example            # Template
│   └── claude-manus-config.json
├── db/
│   └── manus_projects.db       # SQLite database
├── docs/
│   ├── QUICK_START_AUTOMATION.md
│   └── MANUS_AUTOMATION_GUIDE.md
└── requirements.txt
```

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Cloudflare account with API access
- At least one domain managed in Cloudflare

### Setup Steps

```bash
# 1. Navigate to toolkit directory
cd ~/CLAUDE/manus-toolkit

# 2. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API token
cp config/.env.example config/.env
# Edit config/.env with your Cloudflare API token

# 5. Make scripts executable
chmod +x scripts/manus-dns
chmod +x scripts/claude-manus-helper.sh

# 6. Verify installation
./scripts/manus-dns zones
```

---

## Configuration

### Cloudflare API Token

1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token"
3. Use "Edit zone DNS" template or create custom with:
   - **Zone:DNS:Edit** - Modify DNS records
   - **Zone:Zone:Read** - List zones
4. Copy the token to `config/.env`

```env
CLOUDFLARE_API_TOKEN=your_token_here
```

### Alternative: Global API Key (Legacy)

```env
CLOUDFLARE_EMAIL=your@email.com
CLOUDFLARE_API_KEY=your_global_api_key
```

### Manus API Key (Optional)

For Manus AI MCP integration:

```env
MANUS_API_KEY=your_manus_api_key
```

---

## Level 1: Basic DNS Manager

The `manus-dns-manager.py` script provides direct Cloudflare API control.

### List All Zones

```bash
python3 scripts/manus-dns-manager.py zones
```

### List DNS Records

```bash
# All domains
python3 scripts/manus-dns-manager.py list

# Specific domain
python3 scripts/manus-dns-manager.py list --domain example.com
```

### Create a Record

```bash
python3 scripts/manus-dns-manager.py create \
  --domain example.com \
  --type CNAME \
  --name app \
  --content target.manus.space \
  --proxied
```

Supported record types:
- A, AAAA - IP addresses
- CNAME - Aliases
- TXT - Text records
- MX - Mail exchange
- NS - Nameservers

### Update a Record

```bash
python3 scripts/manus-dns-manager.py update \
  --domain example.com \
  --name app \
  --content new-target.manus.space
```

### Delete a Record

```bash
python3 scripts/manus-dns-manager.py delete \
  --domain example.com \
  --name app
```

---

## Level 2: Automated Deployment

The `manus-deploy-auto.py` script automates the full deployment workflow.

### Deploy a Project

```bash
python3 scripts/manus-deploy-auto.py deploy \
  myproject \
  app.example.com \
  abc123.manus.space
```

This performs:
1. Zone lookup for your domain
2. CNAME record creation
3. Project database entry
4. DNS propagation monitoring (up to 60 seconds)
5. Site availability check

### Check Project Status

```bash
python3 scripts/manus-deploy-auto.py status myproject
```

Shows:
- Custom domain and Manus URL
- Current DNS resolution status
- Site availability and HTTP status
- Creation and update timestamps

### List All Projects

```bash
python3 scripts/manus-deploy-auto.py list
```

### Remove a Project

```bash
python3 scripts/manus-deploy-auto.py remove myproject
```

This deletes the DNS record and removes from database.

### Monitor a Domain

```bash
python3 scripts/manus-deploy-auto.py monitor app.example.com
```

Real-time monitoring of DNS and HTTP availability for 2 minutes.

---

## Level 3: Claude CLI Integration

The `claude-manus-helper.sh` script provides an interactive, menu-driven interface.

### Interactive Mode

```bash
./scripts/claude-manus-helper.sh
```

Menu options:
1. Deploy a new Manus project
2. Check project status
3. List all projects
4. List DNS records
5. Create a DNS record
6. Update a DNS record
7. Delete a DNS record
8. List all domains
9. Monitor a domain
0. Configure API tokens

### Natural Language Commands

```bash
# Direct command execution
./scripts/claude-manus-helper.sh "deploy a new project"
./scripts/claude-manus-helper.sh "list my projects"
./scripts/claude-manus-helper.sh "check status"
./scripts/claude-manus-helper.sh "list dns records"
```

---

## Workflow Examples

### Example 1: Deploy a PiVPN Dashboard

```bash
# Using the bash wrapper
./scripts/manus-dns deploy pivpn pivpn.philipwright.me abc123.manus.space

# Check status
./scripts/manus-dns status pivpn

# View in browser
open https://pivpn.philipwright.me
```

### Example 2: Batch DNS Setup

```bash
# Create multiple records
./scripts/manus-dns create -d example.com -t CNAME -n app1 -c host1.manus.space --proxied
./scripts/manus-dns create -d example.com -t CNAME -n app2 -c host2.manus.space --proxied
./scripts/manus-dns create -d example.com -t CNAME -n api -c api.manus.space --proxied

# Verify
./scripts/manus-dns list example.com
```

### Example 3: Migrate DNS Records

```bash
# Export current records (manual)
./scripts/manus-dns list old-domain.com

# Recreate on new domain
./scripts/manus-dns create -d new-domain.com -t CNAME -n app -c target.manus.space
```

---

## Troubleshooting

### "Zone not found" Error

- Verify the domain is in your Cloudflare account
- Check API token has Zone:Zone:Read permission
- Use the root domain (example.com, not subdomain.example.com)

### "Record already exists" Error

- Use `update` instead of `create` for existing records
- Or delete first with `delete` command

### DNS Not Propagating

- DNS changes can take up to 24 hours (usually < 5 minutes)
- Check with: `dig app.example.com CNAME`
- Verify at: https://dnschecker.org

### HTTPS Not Working

- Cloudflare proxy must be enabled for SSL
- Wait for SSL certificate provisioning (up to 15 minutes)
- Check Cloudflare SSL settings

### API Token Errors

- Verify token is set: `echo $CLOUDFLARE_API_TOKEN`
- Check token permissions at Cloudflare dashboard
- Regenerate token if compromised

---

## API Reference

### manus-dns-manager.py

```
usage: manus-dns-manager.py [-h] {zones,list,create,update,delete} ...

Commands:
  zones   List all zones/domains
  list    List DNS records [--domain DOMAIN]
  create  Create record (--domain, --type, --name, --content, [--proxied])
  update  Update record (--domain, --name, --content, [--type])
  delete  Delete record (--domain, --name, [--type])
```

### manus-deploy-auto.py

```
usage: manus-deploy-auto.py [-h] {deploy,status,list,remove,monitor} ...

Commands:
  deploy   Deploy project (project_name, custom_domain, manus_url)
  status   Check status (project_name)
  list     List all projects
  remove   Remove project (project_name)
  monitor  Monitor domain (domain)
```

### manus-dns (bash wrapper)

```
usage: manus-dns <command> [options]

Commands:
  zones              List all domains
  list [domain]      List DNS records
  add                Interactive record creation
  create <options>   Create with CLI options
  update <options>   Update existing record
  delete <options>   Delete record
  deploy <args>      Full deployment
  status <name>      Check status
  projects           List projects
  remove <name>      Remove project
  monitor <domain>   Monitor domain
```

---

## Database Schema

The SQLite database (`db/manus_projects.db`) stores:

```sql
CREATE TABLE projects (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE,
  custom_domain TEXT,
  manus_url TEXT,
  record_id TEXT,
  zone_id TEXT,
  status TEXT,
  created_at TEXT,
  updated_at TEXT,
  dns_propagated INTEGER,
  site_live INTEGER
);
```

---

## Security Notes

- Never commit `.env` files to version control
- Use API tokens with minimal required permissions
- Rotate tokens if exposed
- The database contains zone IDs and record IDs (not secrets)

---

## Author

Philip S. Wright (pdubbbbbs)
- GitHub: https://github.com/pdubbbbbs
- Company: Always Under, Inc.
