# Manus DNS Automation Toolkit

Complete automation toolkit for deploying Manus projects with custom domains via Cloudflare DNS.

## Features

- **One-Command Deployment** - Deploy with `manus-dns deploy myapp app.example.com target.manus.space`
- **Real-Time Monitoring** - Watch DNS propagation and site availability
- **Project Tracking** - Database of all deployments with status
- **Multi-Domain Support** - Works with all Cloudflare domains
- **Claude CLI Ready** - Interactive and natural language interfaces

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure your Cloudflare API token
cp config/.env.example config/.env
# Edit config/.env with your token

# Make scripts executable
chmod +x scripts/manus-dns scripts/claude-manus-helper.sh

# Deploy a project
./scripts/manus-dns deploy myproject app.yourdomain.com abc123.manus.space
```

## Three Levels of Automation

| Level | Tool | Use Case |
|-------|------|----------|
| 1 | `manus-dns-manager.py` | Direct Cloudflare API operations |
| 2 | `manus-deploy-auto.py` | Automated deployment with monitoring |
| 3 | `claude-manus-helper.sh` | Interactive menu-driven interface |

## Commands

```bash
# List your domains
./scripts/manus-dns zones

# List DNS records
./scripts/manus-dns list [domain]

# Deploy a Manus project
./scripts/manus-dns deploy <name> <custom_domain> <manus_url>

# Check deployment status
./scripts/manus-dns status <name>

# List all projects
./scripts/manus-dns projects

# Interactive mode
./scripts/claude-manus-helper.sh
```

## Requirements

- Python 3.8+
- Cloudflare account with API token
- Domains managed in Cloudflare

## Documentation

- [Quick Start Guide](docs/QUICK_START_AUTOMATION.md)
- [Complete Automation Guide](docs/MANUS_AUTOMATION_GUIDE.md)

## Directory Structure

```
manus-toolkit/
├── scripts/           # Automation scripts
├── config/            # Configuration files
├── db/                # SQLite database
├── docs/              # Documentation
└── requirements.txt   # Python dependencies
```

## Author

Philip S. Wright ([@pdubbbbbs](https://github.com/pdubbbbbs))
