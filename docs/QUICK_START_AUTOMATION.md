# Quick Start: Manus Automation Toolkit

Get started in 5 minutes!

## Prerequisites

- Python 3.8+
- Cloudflare account with at least one domain
- Cloudflare API token

## 1. Install Dependencies

```bash
cd ~/CLAUDE/manus-toolkit
pip install -r requirements.txt
```

## 2. Configure API Token

Create your Cloudflare API token at: https://dash.cloudflare.com/profile/api-tokens

Required permissions:
- Zone:DNS:Edit
- Zone:Zone:Read

```bash
# Copy the example config
cp config/.env.example config/.env

# Edit with your token
nano config/.env
```

Or set as environment variable:
```bash
export CLOUDFLARE_API_TOKEN="your_token_here"
```

## 3. Make Scripts Executable

```bash
chmod +x scripts/manus-dns
chmod +x scripts/claude-manus-helper.sh
```

## 4. Verify Setup

```bash
# List your Cloudflare domains
./scripts/manus-dns zones
```

## 5. Deploy Your First Project

```bash
# One-command deployment
./scripts/manus-dns deploy myproject app.yourdomain.com abc123.manus.space
```

This will:
1. Create a CNAME record pointing to your Manus deployment
2. Monitor DNS propagation
3. Verify site availability
4. Track the project in the local database

## Quick Reference

| Command | Description |
|---------|-------------|
| `manus-dns zones` | List all your domains |
| `manus-dns list` | List all DNS records |
| `manus-dns list example.com` | List records for one domain |
| `manus-dns deploy <name> <domain> <url>` | Deploy a Manus project |
| `manus-dns status <name>` | Check deployment status |
| `manus-dns projects` | List tracked projects |

## Interactive Mode

For guided workflows:
```bash
./scripts/claude-manus-helper.sh
```

## Need Help?

- Full documentation: `docs/MANUS_AUTOMATION_GUIDE.md`
- GitHub: https://github.com/pdubbbbbs
