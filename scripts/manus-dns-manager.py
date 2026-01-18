#!/usr/bin/env python3
"""
Manus DNS Manager - Level 1: Basic Cloudflare DNS Control

Direct Cloudflare API control for managing DNS records across all domains.
Supports create, update, delete, and list operations.

Usage:
  manus-dns-manager.py list [--domain DOMAIN]
  manus-dns-manager.py create --domain DOMAIN --type TYPE --name NAME --content CONTENT [--proxied]
  manus-dns-manager.py update --domain DOMAIN --name NAME --content CONTENT [--type TYPE]
  manus-dns-manager.py delete --domain DOMAIN --name NAME [--type TYPE]
  manus-dns-manager.py zones
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
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
CF_EMAIL = os.environ.get("CLOUDFLARE_EMAIL", "")


def get_headers() -> dict:
  """Get Cloudflare API headers."""
  if CF_API_TOKEN:
    return {
      "Authorization": f"Bearer {CF_API_TOKEN}",
      "Content-Type": "application/json"
    }
  elif CF_EMAIL:
    api_key = os.environ.get("CLOUDFLARE_API_KEY", "")
    return {
      "X-Auth-Email": CF_EMAIL,
      "X-Auth-Key": api_key,
      "Content-Type": "application/json"
    }
  else:
    console.print("[red]Error: CLOUDFLARE_API_TOKEN or CLOUDFLARE_EMAIL/API_KEY not set[/red]")
    sys.exit(1)


def get_zone_id(domain: str) -> Optional[str]:
  """Get zone ID for a domain."""
  with httpx.Client(timeout=30) as client:
    resp = client.get(
      f"{CF_API_BASE}/zones",
      headers=get_headers(),
      params={"name": domain}
    )

    if resp.status_code == 200:
      data = resp.json()
      if data.get("result"):
        return data["result"][0]["id"]
    return None


def list_zones():
  """List all zones/domains in the account."""
  with httpx.Client(timeout=30) as client:
    resp = client.get(
      f"{CF_API_BASE}/zones",
      headers=get_headers(),
      params={"per_page": 50}
    )

    if resp.status_code != 200:
      console.print(f"[red]Error {resp.status_code}: {resp.text}[/red]")
      return

    data = resp.json()
    zones = data.get("result", [])

    table = Table(title="Cloudflare Zones", box=box.ROUNDED)
    table.add_column("Domain", style="cyan")
    table.add_column("Zone ID", style="dim")
    table.add_column("Status", style="green")
    table.add_column("Plan", style="yellow")

    for zone in zones:
      table.add_row(
        zone["name"],
        zone["id"][:12] + "...",
        zone["status"],
        zone.get("plan", {}).get("name", "Unknown")
      )

    console.print(table)
    console.print(f"\n[dim]Total zones: {len(zones)}[/dim]")


def list_records(domain: Optional[str] = None):
  """List DNS records for a domain or all domains."""
  with httpx.Client(timeout=30) as client:
    if domain:
      zone_id = get_zone_id(domain)
      if not zone_id:
        console.print(f"[red]Zone not found for domain: {domain}[/red]")
        return
      zones = [{"id": zone_id, "name": domain}]
    else:
      resp = client.get(
        f"{CF_API_BASE}/zones",
        headers=get_headers(),
        params={"per_page": 50}
      )
      if resp.status_code != 200:
        console.print(f"[red]Error fetching zones: {resp.text}[/red]")
        return
      zones = resp.json().get("result", [])

    for zone in zones:
      resp = client.get(
        f"{CF_API_BASE}/zones/{zone['id']}/dns_records",
        headers=get_headers(),
        params={"per_page": 100}
      )

      if resp.status_code != 200:
        console.print(f"[red]Error fetching records for {zone['name']}: {resp.text}[/red]")
        continue

      records = resp.json().get("result", [])

      table = Table(title=f"DNS Records: {zone['name']}", box=box.ROUNDED)
      table.add_column("Type", style="magenta", width=6)
      table.add_column("Name", style="cyan")
      table.add_column("Content", style="green")
      table.add_column("Proxied", style="yellow", width=7)
      table.add_column("TTL", style="dim", width=6)

      for record in sorted(records, key=lambda x: (x["type"], x["name"])):
        proxied = "Yes" if record.get("proxied") else "No"
        ttl = "Auto" if record.get("ttl") == 1 else str(record.get("ttl", ""))
        content = record["content"]
        if len(content) > 40:
          content = content[:37] + "..."

        table.add_row(
          record["type"],
          record["name"].replace(f".{zone['name']}", ""),
          content,
          proxied,
          ttl
        )

      console.print(table)
      console.print(f"[dim]Records: {len(records)}[/dim]\n")


def create_record(domain: str, record_type: str, name: str, content: str, proxied: bool = False):
  """Create a new DNS record."""
  zone_id = get_zone_id(domain)
  if not zone_id:
    console.print(f"[red]Zone not found for domain: {domain}[/red]")
    return False

  # Construct full name if needed
  if name == "@":
    full_name = domain
  elif not name.endswith(domain):
    full_name = f"{name}.{domain}"
  else:
    full_name = name

  payload = {
    "type": record_type.upper(),
    "name": full_name,
    "content": content,
    "proxied": proxied if record_type.upper() in ["A", "AAAA", "CNAME"] else False,
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
        console.print(Panel(
          f"[green]Record created successfully![/green]\n\n"
          f"Type: [cyan]{record_type.upper()}[/cyan]\n"
          f"Name: [cyan]{full_name}[/cyan]\n"
          f"Content: [cyan]{content}[/cyan]\n"
          f"Proxied: [yellow]{'Yes' if proxied else 'No'}[/yellow]",
          title="DNS Record Created",
          border_style="green"
        ))
        return True
      else:
        errors = data.get("errors", [])
        console.print(f"[red]Error: {errors}[/red]")
        return False
    else:
      console.print(f"[red]Error {resp.status_code}: {resp.text}[/red]")
      return False


def update_record(domain: str, name: str, content: str, record_type: Optional[str] = None):
  """Update an existing DNS record."""
  zone_id = get_zone_id(domain)
  if not zone_id:
    console.print(f"[red]Zone not found for domain: {domain}[/red]")
    return False

  # Construct full name if needed
  if name == "@":
    full_name = domain
  elif not name.endswith(domain):
    full_name = f"{name}.{domain}"
  else:
    full_name = name

  with httpx.Client(timeout=30) as client:
    # Find existing record
    params = {"name": full_name}
    if record_type:
      params["type"] = record_type.upper()

    resp = client.get(
      f"{CF_API_BASE}/zones/{zone_id}/dns_records",
      headers=get_headers(),
      params=params
    )

    if resp.status_code != 200:
      console.print(f"[red]Error finding record: {resp.text}[/red]")
      return False

    records = resp.json().get("result", [])
    if not records:
      console.print(f"[red]No record found matching: {full_name}[/red]")
      return False

    record = records[0]
    record_id = record["id"]

    # Update record
    payload = {
      "type": record["type"],
      "name": record["name"],
      "content": content,
      "proxied": record.get("proxied", False),
      "ttl": record.get("ttl", 1)
    }

    resp = client.put(
      f"{CF_API_BASE}/zones/{zone_id}/dns_records/{record_id}",
      headers=get_headers(),
      json=payload
    )

    if resp.status_code == 200:
      data = resp.json()
      if data.get("success"):
        console.print(Panel(
          f"[green]Record updated successfully![/green]\n\n"
          f"Name: [cyan]{full_name}[/cyan]\n"
          f"Old Content: [dim]{record['content']}[/dim]\n"
          f"New Content: [cyan]{content}[/cyan]",
          title="DNS Record Updated",
          border_style="green"
        ))
        return True

    console.print(f"[red]Error updating record: {resp.text}[/red]")
    return False


def delete_record(domain: str, name: str, record_type: Optional[str] = None):
  """Delete a DNS record."""
  zone_id = get_zone_id(domain)
  if not zone_id:
    console.print(f"[red]Zone not found for domain: {domain}[/red]")
    return False

  # Construct full name if needed
  if name == "@":
    full_name = domain
  elif not name.endswith(domain):
    full_name = f"{name}.{domain}"
  else:
    full_name = name

  with httpx.Client(timeout=30) as client:
    # Find existing record
    params = {"name": full_name}
    if record_type:
      params["type"] = record_type.upper()

    resp = client.get(
      f"{CF_API_BASE}/zones/{zone_id}/dns_records",
      headers=get_headers(),
      params=params
    )

    if resp.status_code != 200:
      console.print(f"[red]Error finding record: {resp.text}[/red]")
      return False

    records = resp.json().get("result", [])
    if not records:
      console.print(f"[red]No record found matching: {full_name}[/red]")
      return False

    record = records[0]
    record_id = record["id"]

    # Delete record
    resp = client.delete(
      f"{CF_API_BASE}/zones/{zone_id}/dns_records/{record_id}",
      headers=get_headers()
    )

    if resp.status_code == 200:
      data = resp.json()
      if data.get("success"):
        console.print(Panel(
          f"[red]Record deleted![/red]\n\n"
          f"Type: [dim]{record['type']}[/dim]\n"
          f"Name: [dim]{full_name}[/dim]\n"
          f"Content: [dim]{record['content']}[/dim]",
          title="DNS Record Deleted",
          border_style="red"
        ))
        return True

    console.print(f"[red]Error deleting record: {resp.text}[/red]")
    return False


def main():
  parser = argparse.ArgumentParser(
    description="Manus DNS Manager - Cloudflare DNS Control",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  %(prog)s zones                                    # List all domains
  %(prog)s list                                     # List all DNS records
  %(prog)s list --domain example.com               # List records for one domain
  %(prog)s create --domain example.com --type CNAME --name app --content target.manus.space
  %(prog)s update --domain example.com --name app --content new-target.manus.space
  %(prog)s delete --domain example.com --name app
    """
  )

  subparsers = parser.add_subparsers(dest="command", help="Commands")

  # zones command
  subparsers.add_parser("zones", help="List all zones/domains")

  # list command
  list_parser = subparsers.add_parser("list", help="List DNS records")
  list_parser.add_argument("--domain", "-d", help="Domain to list records for")

  # create command
  create_parser = subparsers.add_parser("create", help="Create a DNS record")
  create_parser.add_argument("--domain", "-d", required=True, help="Domain name")
  create_parser.add_argument("--type", "-t", required=True, help="Record type (A, AAAA, CNAME, TXT, etc.)")
  create_parser.add_argument("--name", "-n", required=True, help="Record name (@ for root)")
  create_parser.add_argument("--content", "-c", required=True, help="Record content/value")
  create_parser.add_argument("--proxied", "-p", action="store_true", help="Enable Cloudflare proxy")

  # update command
  update_parser = subparsers.add_parser("update", help="Update a DNS record")
  update_parser.add_argument("--domain", "-d", required=True, help="Domain name")
  update_parser.add_argument("--name", "-n", required=True, help="Record name")
  update_parser.add_argument("--content", "-c", required=True, help="New content/value")
  update_parser.add_argument("--type", "-t", help="Record type (optional filter)")

  # delete command
  delete_parser = subparsers.add_parser("delete", help="Delete a DNS record")
  delete_parser.add_argument("--domain", "-d", required=True, help="Domain name")
  delete_parser.add_argument("--name", "-n", required=True, help="Record name")
  delete_parser.add_argument("--type", "-t", help="Record type (optional filter)")

  args = parser.parse_args()

  if not args.command:
    parser.print_help()
    sys.exit(1)

  console.print(Panel(
    "[bold cyan]Manus DNS Manager[/bold cyan]\n[dim]Cloudflare DNS Control[/dim]",
    border_style="cyan"
  ))

  if args.command == "zones":
    list_zones()
  elif args.command == "list":
    list_records(args.domain)
  elif args.command == "create":
    create_record(args.domain, args.type, args.name, args.content, args.proxied)
  elif args.command == "update":
    update_record(args.domain, args.name, args.content, args.type)
  elif args.command == "delete":
    delete_record(args.domain, args.name, args.type)


if __name__ == "__main__":
  main()
