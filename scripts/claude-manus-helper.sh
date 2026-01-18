#!/usr/bin/env bash
#
# claude-manus-helper.sh - Level 3: Claude CLI Integration
#
# Interactive menu-driven interface for Manus DNS operations.
# Designed for use with Claude Code conversational workflows.
#
# Features:
#   - Interactive menu-driven interface
#   - Natural language deployment commands
#   - Guided workflows with prompts
#   - Batch operation support
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$TOOLKIT_DIR/config"
ENV_FILE="$CONFIG_DIR/.env"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

# Load environment
if [[ -f "$ENV_FILE" ]]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

show_banner() {
  clear
  echo -e "${CYAN}"
  echo "╔═══════════════════════════════════════════════════════════════╗"
  echo "║                                                               ║"
  echo "║   ███╗   ███╗ █████╗ ███╗   ██╗██╗   ██╗███████╗              ║"
  echo "║   ████╗ ████║██╔══██╗████╗  ██║██║   ██║██╔════╝              ║"
  echo "║   ██╔████╔██║███████║██╔██╗ ██║██║   ██║███████╗              ║"
  echo "║   ██║╚██╔╝██║██╔══██║██║╚██╗██║██║   ██║╚════██║              ║"
  echo "║   ██║ ╚═╝ ██║██║  ██║██║ ╚████║╚██████╔╝███████║              ║"
  echo "║   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝              ║"
  echo "║                                                               ║"
  echo "║           ${BOLD}Claude Code DNS Automation Toolkit${NC}${CYAN}                  ║"
  echo "║                                                               ║"
  echo "╚═══════════════════════════════════════════════════════════════╝"
  echo -e "${NC}"
}

show_menu() {
  echo -e "${BOLD}${YELLOW}What would you like to do?${NC}"
  echo ""
  echo -e "  ${GREEN}1)${NC} Deploy a new Manus project"
  echo -e "  ${GREEN}2)${NC} Check project status"
  echo -e "  ${GREEN}3)${NC} List all projects"
  echo -e "  ${GREEN}4)${NC} List DNS records"
  echo -e "  ${GREEN}5)${NC} Create a DNS record"
  echo -e "  ${GREEN}6)${NC} Update a DNS record"
  echo -e "  ${GREEN}7)${NC} Delete a DNS record"
  echo -e "  ${GREEN}8)${NC} List all domains (zones)"
  echo -e "  ${GREEN}9)${NC} Monitor a domain"
  echo -e "  ${GREEN}0)${NC} Configure API tokens"
  echo ""
  echo -e "  ${DIM}q) Quit${NC}"
  echo ""
}

check_config() {
  if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
    echo -e "${YELLOW}No Cloudflare API token configured.${NC}"
    echo -e "Run option ${GREEN}0${NC} to configure."
    return 1
  fi
  return 0
}

configure_tokens() {
  echo -e "${BOLD}${CYAN}API Configuration${NC}"
  echo ""

  # Current status
  if [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]]; then
    echo -e "Current Cloudflare token: ${GREEN}configured${NC} (${CLOUDFLARE_API_TOKEN:0:12}...)"
  else
    echo -e "Current Cloudflare token: ${RED}not set${NC}"
  fi

  if [[ -n "${MANUS_API_KEY:-}" ]]; then
    echo -e "Current Manus API key: ${GREEN}configured${NC}"
  else
    echo -e "Current Manus API key: ${DIM}not set${NC}"
  fi

  echo ""
  echo -e "${YELLOW}Enter new values (leave blank to keep current):${NC}"
  echo ""

  read -rp "Cloudflare API Token: " new_cf_token
  read -rp "Manus API Key (optional): " new_manus_key

  # Create config directory if needed
  mkdir -p "$CONFIG_DIR"

  # Write to .env file
  if [[ -n "$new_cf_token" || -n "$new_manus_key" ]]; then
    cat > "$ENV_FILE" << EOF
# Manus Toolkit Configuration
# Generated: $(date)

CLOUDFLARE_API_TOKEN=${new_cf_token:-${CLOUDFLARE_API_TOKEN:-}}
MANUS_API_KEY=${new_manus_key:-${MANUS_API_KEY:-}}
EOF

    echo ""
    echo -e "${GREEN}Configuration saved to $ENV_FILE${NC}"

    # Reload
    export $(grep -v '^#' "$ENV_FILE" | xargs 2>/dev/null) || true
  fi
}

deploy_wizard() {
  echo -e "${BOLD}${CYAN}Deploy New Manus Project${NC}"
  echo -e "${DIM}This will create DNS records and monitor deployment.${NC}"
  echo ""

  # Project name
  read -rp "Project name (e.g., my-app): " project_name
  if [[ -z "$project_name" ]]; then
    echo -e "${RED}Project name is required.${NC}"
    return
  fi

  # Custom domain
  echo ""
  echo -e "${DIM}Your custom domain should be a subdomain you control.${NC}"
  echo -e "${DIM}Example: app.yourdomain.com${NC}"
  read -rp "Custom domain: " custom_domain
  if [[ -z "$custom_domain" ]]; then
    echo -e "${RED}Custom domain is required.${NC}"
    return
  fi

  # Manus URL
  echo ""
  echo -e "${DIM}The Manus URL is the deployment URL from Manus (e.g., abc123.manus.space)${NC}"
  read -rp "Manus URL: " manus_url
  if [[ -z "$manus_url" ]]; then
    echo -e "${RED}Manus URL is required.${NC}"
    return
  fi

  # Confirm
  echo ""
  echo -e "${YELLOW}Ready to deploy:${NC}"
  echo -e "  Project: ${CYAN}$project_name${NC}"
  echo -e "  Domain:  ${GREEN}$custom_domain${NC}"
  echo -e "  Target:  ${BLUE}$manus_url${NC}"
  echo ""
  read -rp "Proceed? [Y/n]: " confirm

  if [[ ! "$confirm" =~ ^[Nn]$ ]]; then
    echo ""
    python3 "$SCRIPT_DIR/manus-deploy-auto.py" deploy "$project_name" "$custom_domain" "$manus_url"
  fi
}

status_wizard() {
  echo -e "${BOLD}${CYAN}Check Project Status${NC}"
  echo ""

  read -rp "Project name: " project_name
  if [[ -z "$project_name" ]]; then
    echo -e "${RED}Project name is required.${NC}"
    return
  fi

  echo ""
  python3 "$SCRIPT_DIR/manus-deploy-auto.py" status "$project_name"
}

list_projects() {
  echo -e "${BOLD}${CYAN}All Manus Projects${NC}"
  echo ""
  python3 "$SCRIPT_DIR/manus-deploy-auto.py" list
}

list_records() {
  echo -e "${BOLD}${CYAN}List DNS Records${NC}"
  echo ""

  read -rp "Domain (leave blank for all): " domain

  if [[ -n "$domain" ]]; then
    python3 "$SCRIPT_DIR/manus-dns-manager.py" list --domain "$domain"
  else
    python3 "$SCRIPT_DIR/manus-dns-manager.py" list
  fi
}

create_record() {
  echo -e "${BOLD}${CYAN}Create DNS Record${NC}"
  echo ""

  read -rp "Domain (e.g., example.com): " domain
  if [[ -z "$domain" ]]; then
    echo -e "${RED}Domain is required.${NC}"
    return
  fi

  echo ""
  echo "Record types: A, AAAA, CNAME, TXT, MX, NS"
  read -rp "Record type [CNAME]: " record_type
  record_type=${record_type:-CNAME}

  read -rp "Name (@ for root, or subdomain): " name
  if [[ -z "$name" ]]; then
    echo -e "${RED}Name is required.${NC}"
    return
  fi

  read -rp "Content/Value: " content
  if [[ -z "$content" ]]; then
    echo -e "${RED}Content is required.${NC}"
    return
  fi

  read -rp "Enable Cloudflare proxy? [y/N]: " proxied
  proxied_flag=""
  if [[ "$proxied" =~ ^[Yy]$ ]]; then
    proxied_flag="--proxied"
  fi

  echo ""
  python3 "$SCRIPT_DIR/manus-dns-manager.py" create --domain "$domain" --type "$record_type" --name "$name" --content "$content" $proxied_flag
}

update_record() {
  echo -e "${BOLD}${CYAN}Update DNS Record${NC}"
  echo ""

  read -rp "Domain: " domain
  read -rp "Record name to update: " name
  read -rp "New content/value: " content

  if [[ -z "$domain" || -z "$name" || -z "$content" ]]; then
    echo -e "${RED}All fields are required.${NC}"
    return
  fi

  echo ""
  python3 "$SCRIPT_DIR/manus-dns-manager.py" update --domain "$domain" --name "$name" --content "$content"
}

delete_record() {
  echo -e "${BOLD}${CYAN}Delete DNS Record${NC}"
  echo -e "${RED}Warning: This will permanently delete the record!${NC}"
  echo ""

  read -rp "Domain: " domain
  read -rp "Record name to delete: " name

  if [[ -z "$domain" || -z "$name" ]]; then
    echo -e "${RED}Domain and name are required.${NC}"
    return
  fi

  read -rp "Are you sure? [y/N]: " confirm
  if [[ "$confirm" =~ ^[Yy]$ ]]; then
    echo ""
    python3 "$SCRIPT_DIR/manus-dns-manager.py" delete --domain "$domain" --name "$name"
  fi
}

list_zones() {
  echo -e "${BOLD}${CYAN}All Cloudflare Domains${NC}"
  echo ""
  python3 "$SCRIPT_DIR/manus-dns-manager.py" zones
}

monitor_domain() {
  echo -e "${BOLD}${CYAN}Monitor Domain${NC}"
  echo ""

  read -rp "Domain to monitor: " domain
  if [[ -z "$domain" ]]; then
    echo -e "${RED}Domain is required.${NC}"
    return
  fi

  echo ""
  python3 "$SCRIPT_DIR/manus-deploy-auto.py" monitor "$domain"
}

wait_for_key() {
  echo ""
  echo -e "${DIM}Press any key to continue...${NC}"
  read -n 1 -s
}

# Natural language command handling
handle_natural_language() {
  local input="$1"
  input=$(echo "$input" | tr '[:upper:]' '[:lower:]')

  case "$input" in
    *"deploy"*|*"new project"*|*"create project"*)
      deploy_wizard
      ;;
    *"status"*|*"check"*)
      status_wizard
      ;;
    *"list project"*|*"show project"*|*"my project"*)
      list_projects
      ;;
    *"list record"*|*"show record"*|*"dns record"*)
      list_records
      ;;
    *"create record"*|*"add record"*|*"new record"*)
      create_record
      ;;
    *"update record"*|*"change record"*|*"modify record"*)
      update_record
      ;;
    *"delete record"*|*"remove record"*)
      delete_record
      ;;
    *"zone"*|*"domain"*|*"list domain"*)
      list_zones
      ;;
    *"monitor"*|*"watch"*)
      monitor_domain
      ;;
    *"config"*|*"setup"*|*"token"*)
      configure_tokens
      ;;
    *"help"*)
      show_menu
      ;;
    *"quit"*|*"exit"*|*"bye"*)
      echo -e "${GREEN}Goodbye!${NC}"
      exit 0
      ;;
    *)
      echo -e "${YELLOW}I didn't understand that. Try one of these:${NC}"
      echo "  - deploy, status, list projects"
      echo "  - list records, create record, update record, delete record"
      echo "  - list domains, monitor, config"
      ;;
  esac
}

# Main loop
main() {
  # Check for direct command
  if [[ $# -gt 0 ]]; then
    handle_natural_language "$*"
    exit 0
  fi

  # Interactive mode
  while true; do
    show_banner
    check_config || true
    show_menu

    read -rp "$(echo -e "${CYAN}>${NC} ")" choice

    case "$choice" in
      1) deploy_wizard ;;
      2) status_wizard ;;
      3) list_projects ;;
      4) list_records ;;
      5) create_record ;;
      6) update_record ;;
      7) delete_record ;;
      8) list_zones ;;
      9) monitor_domain ;;
      0) configure_tokens ;;
      q|Q) echo -e "${GREEN}Goodbye!${NC}"; exit 0 ;;
      *)
        # Try natural language
        handle_natural_language "$choice"
        ;;
    esac

    wait_for_key
  done
}

main "$@"
