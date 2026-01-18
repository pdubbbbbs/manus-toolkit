#!/usr/bin/env python3
"""
Manus Deploy Auto - Level 2: Automated Deployment with Monitoring

Features:
- Automatic DNS configuration via Cloudflare
- Real-time DNS propagation monitoring
- Site availability verification
- Project database for tracking deployments
- Intelligent status reporting

Usage:
  manus-deploy-auto.py deploy <project_name> <your_domain> <manus_url>
  manus-deploy-auto.py status <project_name>
  manus-deploy-auto.py list
  manus-deploy-auto.py remove <project_name>
  manus-deploy-auto.py monitor <subdomain.domain.com>
"""

import os
import sys
import json
import time
import socket
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich import box
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / "config" / ".env"
if env_path.exists():
  load_dotenv(env_path)
else:
  load_dotenv()

console = Console()

# Cloudflare API configuration
CF_API_BASE = "https://api.cloudflare.com/client/v4"
CF_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")

# Database path
DB_PATH = Path(__file__).parent.parent / "db" / "manus_projects.db"


def get_headers() -> dict:
  """Get Cloudflare API headers."""
  return {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json"
  }


def init_database():
  """Initialize the SQLite database."""
  DB_PATH.parent.mkdir(parents=True, exist_ok=True)
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT UNIQUE NOT NULL,
      custom_domain TEXT NOT NULL,
      manus_url TEXT NOT NULL,
      record_id TEXT,
      zone_id TEXT,
      status TEXT DEFAULT 'pending',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      dns_propagated INTEGER DEFAULT 0,
      site_live INTEGER DEFAULT 0
    )
  """)
  conn.commit()
  conn.close()


def get_zone_id(domain: str) -> Optional[str]:
  """Get zone ID for a domain."""
  # Extract root domain
  parts = domain.split(".")
  if len(parts) >= 2:
    root_domain = ".".join(parts[-2:])
  else:
    root_domain = domain

  with httpx.Client(timeout=30) as client:
    resp = client.get(
      f"{CF_API_BASE}/zones",
      headers=get_headers(),
      params={"name": root_domain}
    )

    if resp.status_code == 200:
      data = resp.json()
      if data.get("result"):
        return data["result"][0]["id"]
    return None


def extract_manus_target(manus_url: str) -> str:
  """Extract the target hostname from a Manus URL."""
  # Handle various formats
  if manus_url.startswith("http"):
    parsed = urlparse(manus_url)
    return parsed.netloc
  return manus_url


def create_cname_record(zone_id: str, subdomain: str, target: str) -> Optional[str]:
  """Create a CNAME record and return the record ID."""
  payload = {
    "type": "CNAME",
    "name": subdomain,
    "content": target,
    "proxied": True,
    "ttl": 1  # Auto
  }

  with httpx.Client(timeout=30) as client:
    resp = client.post(
      f"{CF_API_BASE}/zones/{zone_id}/dns_records",
      headers=get_headers(),
      json=payload
    )

    if resp.status_code in [200, 201]:
      data = resp.json()
      if data.get("success"):
        return data["result"]["id"]

    # Check if record already exists
    if "already exists" in resp.text.lower():
      # Try to find and update existing record
      resp = client.get(
        f"{CF_API_BASE}/zones/{zone_id}/dns_records",
        headers=get_headers(),
        params={"name": subdomain, "type": "CNAME"}
      )
      if resp.status_code == 200:
        records = resp.json().get("result", [])
        if records:
          return records[0]["id"]

    return None


def check_dns_propagation(hostname: str, expected_target: str) -> bool:
  """Check if DNS has propagated by resolving the hostname."""
  try:
    # Try multiple DNS lookups
    result = socket.gethostbyname(hostname)
    return True  # If we get any result, DNS is working
  except socket.gaierror:
    return False


def check_site_availability(url: str) -> Tuple[bool, int]:
  """Check if a site is accessible and return status code."""
  try:
    with httpx.Client(timeout=10, follow_redirects=True) as client:
      resp = client.get(url)
      return resp.status_code < 400, resp.status_code
  except Exception:
    return False, 0


def deploy_project(project_name: str, custom_domain: str, manus_url: str):
  """Deploy a new Manus project with DNS configuration."""
  init_database()

  console.print(Panel(
    f"[bold cyan]Deploying Project: {project_name}[/bold cyan]\n\n"
    f"Custom Domain: [green]{custom_domain}[/green]\n"
    f"Manus URL: [blue]{manus_url}[/blue]",
    title="Manus Auto Deploy",
    border_style="cyan"
  ))

  # Parse domains
  parts = custom_domain.split(".")
  if len(parts) >= 3:
    subdomain = parts[0]
    root_domain = ".".join(parts[1:])
  else:
    subdomain = custom_domain.split(".")[0]
    root_domain = ".".join(parts[-2:]) if len(parts) >= 2 else custom_domain

  manus_target = extract_manus_target(manus_url)

  console.print(f"\n[dim]Root domain: {root_domain}[/dim]")
  console.print(f"[dim]Subdomain: {subdomain}[/dim]")
  console.print(f"[dim]Target: {manus_target}[/dim]\n")

  # Step 1: Get zone ID
  console.print("[yellow]Step 1:[/yellow] Finding Cloudflare zone...")
  zone_id = get_zone_id(root_domain)
  if not zone_id:
    console.print(f"[red]Error: Zone not found for {root_domain}[/red]")
    console.print("[dim]Make sure this domain is in your Cloudflare account.[/dim]")
    return False

  console.print(f"[green]Found zone ID: {zone_id[:12]}...[/green]")

  # Step 2: Create DNS record
  console.print("\n[yellow]Step 2:[/yellow] Creating CNAME record...")
  record_id = create_cname_record(zone_id, custom_domain, manus_target)
  if not record_id:
    console.print("[red]Error: Failed to create DNS record[/red]")
    return False

  console.print(f"[green]Created record ID: {record_id[:12]}...[/green]")

  # Step 3: Save to database
  console.print("\n[yellow]Step 3:[/yellow] Saving project to database...")
  now = datetime.now().isoformat()
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  try:
    cursor.execute("""
      INSERT OR REPLACE INTO projects
      (name, custom_domain, manus_url, record_id, zone_id, status, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, 'deployed', ?, ?)
    """, (project_name, custom_domain, manus_url, record_id, zone_id, now, now))
    conn.commit()
    console.print("[green]Project saved![/green]")
  except Exception as e:
    console.print(f"[red]Database error: {e}[/red]")
    conn.close()
    return False
  conn.close()

  # Step 4: Monitor DNS propagation
  console.print("\n[yellow]Step 4:[/yellow] Monitoring DNS propagation...")

  with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    console=console,
  ) as progress:
    dns_task = progress.add_task("[cyan]Waiting for DNS...", total=30)

    for i in range(30):
      if check_dns_propagation(custom_domain, manus_target):
        progress.update(dns_task, completed=30)
        console.print("[green]DNS propagated![/green]")

        # Update database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
          "UPDATE projects SET dns_propagated=1, updated_at=? WHERE name=?",
          (datetime.now().isoformat(), project_name)
        )
        conn.commit()
        conn.close()
        break

      progress.update(dns_task, advance=1)
      time.sleep(2)
    else:
      console.print("[yellow]DNS still propagating... This can take up to 24 hours.[/yellow]")

  # Step 5: Check site availability
  console.print("\n[yellow]Step 5:[/yellow] Checking site availability...")
  site_url = f"https://{custom_domain}"

  for attempt in range(5):
    is_live, status_code = check_site_availability(site_url)
    if is_live:
      console.print(f"[green]Site is LIVE! Status: {status_code}[/green]")

      # Update database
      conn = sqlite3.connect(DB_PATH)
      cursor = conn.cursor()
      cursor.execute(
        "UPDATE projects SET site_live=1, status='live', updated_at=? WHERE name=?",
        (datetime.now().isoformat(), project_name)
      )
      conn.commit()
      conn.close()
      break

    console.print(f"[dim]Attempt {attempt + 1}/5 - Waiting...[/dim]")
    time.sleep(5)
  else:
    console.print("[yellow]Site not responding yet. Check back later.[/yellow]")

  # Final summary
  console.print(Panel(
    f"[bold green]Deployment Complete![/bold green]\n\n"
    f"Project: [cyan]{project_name}[/cyan]\n"
    f"URL: [blue]https://{custom_domain}[/blue]\n"
    f"Manus: [dim]{manus_url}[/dim]\n\n"
    f"[dim]Run 'manus-deploy-auto status {project_name}' to check status[/dim]",
    title="Success",
    border_style="green"
  ))

  return True


def get_project_status(project_name: str):
  """Get detailed status for a project."""
  init_database()

  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM projects WHERE name=?", (project_name,))
  row = cursor.fetchone()
  conn.close()

  if not row:
    console.print(f"[red]Project not found: {project_name}[/red]")
    return

  (id_, name, custom_domain, manus_url, record_id, zone_id,
   status, created_at, updated_at, dns_propagated, site_live) = row

  # Check current status
  dns_ok = check_dns_propagation(custom_domain, "")
  site_ok, status_code = check_site_availability(f"https://{custom_domain}")

  status_color = "green" if site_ok else "yellow" if dns_ok else "red"

  console.print(Panel(
    f"[bold]Project: {name}[/bold]\n\n"
    f"Custom Domain: [cyan]{custom_domain}[/cyan]\n"
    f"Manus URL: [blue]{manus_url}[/blue]\n\n"
    f"DNS Status: [{'green' if dns_ok else 'red'}]{'Propagated' if dns_ok else 'Pending'}[/{'green' if dns_ok else 'red'}]\n"
    f"Site Status: [{'green' if site_ok else 'red'}]{'Live ({})'.format(status_code) if site_ok else 'Not Responding'}[/{'green' if site_ok else 'red'}]\n\n"
    f"[dim]Created: {created_at}[/dim]\n"
    f"[dim]Updated: {updated_at}[/dim]",
    title=f"Project Status [{status}]",
    border_style=status_color
  ))


def list_projects():
  """List all tracked projects."""
  init_database()

  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute("SELECT name, custom_domain, manus_url, status, dns_propagated, site_live FROM projects")
  rows = cursor.fetchall()
  conn.close()

  if not rows:
    console.print("[dim]No projects found. Deploy one with:[/dim]")
    console.print("[cyan]manus-deploy-auto deploy <name> <domain> <manus_url>[/cyan]")
    return

  table = Table(title="Manus Projects", box=box.ROUNDED)
  table.add_column("Name", style="cyan")
  table.add_column("Domain", style="blue")
  table.add_column("Status", style="green")
  table.add_column("DNS", style="magenta")
  table.add_column("Live", style="yellow")

  for name, domain, manus_url, status, dns, live in rows:
    dns_icon = "[green]OK[/green]" if dns else "[red]--[/red]"
    live_icon = "[green]YES[/green]" if live else "[red]NO[/red]"
    table.add_row(name, domain, status, dns_icon, live_icon)

  console.print(table)


def remove_project(project_name: str):
  """Remove a project and optionally its DNS record."""
  init_database()

  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute("SELECT record_id, zone_id, custom_domain FROM projects WHERE name=?", (project_name,))
  row = cursor.fetchone()

  if not row:
    console.print(f"[red]Project not found: {project_name}[/red]")
    conn.close()
    return

  record_id, zone_id, custom_domain = row

  # Delete DNS record
  if record_id and zone_id:
    console.print(f"[yellow]Deleting DNS record for {custom_domain}...[/yellow]")
    with httpx.Client(timeout=30) as client:
      resp = client.delete(
        f"{CF_API_BASE}/zones/{zone_id}/dns_records/{record_id}",
        headers=get_headers()
      )
      if resp.status_code == 200:
        console.print("[green]DNS record deleted.[/green]")
      else:
        console.print(f"[yellow]Warning: Could not delete DNS record: {resp.text}[/yellow]")

  # Remove from database
  cursor.execute("DELETE FROM projects WHERE name=?", (project_name,))
  conn.commit()
  conn.close()

  console.print(f"[green]Project '{project_name}' removed.[/green]")


def monitor_domain(domain: str):
  """Monitor DNS and availability for any domain."""
  console.print(Panel(
    f"[bold cyan]Monitoring: {domain}[/bold cyan]",
    border_style="cyan"
  ))

  # Parse domain for manus target hint
  manus_target = ""

  with Live(console=console, refresh_per_second=1) as live:
    for i in range(60):  # 2 minute monitoring
      dns_ok = check_dns_propagation(domain, manus_target)
      site_ok, status_code = check_site_availability(f"https://{domain}")

      status_table = Table(box=box.SIMPLE)
      status_table.add_column("Check", style="cyan")
      status_table.add_column("Status")
      status_table.add_column("Details", style="dim")

      dns_status = "[green]OK[/green]" if dns_ok else "[red]PENDING[/red]"
      site_status = f"[green]{status_code}[/green]" if site_ok else "[red]DOWN[/red]"

      status_table.add_row("DNS Resolution", dns_status, "Resolving hostname")
      status_table.add_row("Site Available", site_status, f"https://{domain}")
      status_table.add_row("Time", f"[dim]{i*2}s[/dim]", "Elapsed")

      live.update(Panel(status_table, title=f"Monitor: {domain}", border_style="blue"))

      if dns_ok and site_ok:
        console.print("\n[green]Domain is fully operational![/green]")
        break

      time.sleep(2)


def main():
  parser = argparse.ArgumentParser(
    description="Manus Deploy Auto - Automated Deployment with Monitoring",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  %(prog)s deploy pivpn pivpn.philipwright.me abc123.manus.space
  %(prog)s status pivpn
  %(prog)s list
  %(prog)s remove pivpn
  %(prog)s monitor app.example.com
    """
  )

  subparsers = parser.add_subparsers(dest="command", help="Commands")

  # deploy command
  deploy_parser = subparsers.add_parser("deploy", help="Deploy a new project")
  deploy_parser.add_argument("project_name", help="Project identifier")
  deploy_parser.add_argument("custom_domain", help="Your custom domain (e.g., app.example.com)")
  deploy_parser.add_argument("manus_url", help="Manus deployment URL")

  # status command
  status_parser = subparsers.add_parser("status", help="Get project status")
  status_parser.add_argument("project_name", help="Project identifier")

  # list command
  subparsers.add_parser("list", help="List all projects")

  # remove command
  remove_parser = subparsers.add_parser("remove", help="Remove a project")
  remove_parser.add_argument("project_name", help="Project identifier")

  # monitor command
  monitor_parser = subparsers.add_parser("monitor", help="Monitor a domain")
  monitor_parser.add_argument("domain", help="Domain to monitor")

  args = parser.parse_args()

  if not args.command:
    parser.print_help()
    sys.exit(1)

  if not CF_API_TOKEN:
    console.print("[red]Error: CLOUDFLARE_API_TOKEN not set[/red]")
    console.print("[dim]Set it in config/.env or environment[/dim]")
    sys.exit(1)

  if args.command == "deploy":
    deploy_project(args.project_name, args.custom_domain, args.manus_url)
  elif args.command == "status":
    get_project_status(args.project_name)
  elif args.command == "list":
    list_projects()
  elif args.command == "remove":
    remove_project(args.project_name)
  elif args.command == "monitor":
    monitor_domain(args.domain)


if __name__ == "__main__":
  main()
