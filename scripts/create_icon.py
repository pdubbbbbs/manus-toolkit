#!/usr/bin/env python3
"""Generate a custom Manus DNS icon for macOS app."""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
from pathlib import Path

def create_manus_icon(size):
  """Create a modern Manus DNS icon at the specified size."""
  # Create image with transparency
  img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
  draw = ImageDraw.Draw(img)

  # Colors from the user's theme
  bg_dark = (10, 10, 15, 255)        # Dark background
  accent_cyan = (0, 129, 242, 255)   # Primary cyan accent
  accent_glow = (0, 200, 255, 180)   # Lighter cyan for glow
  white = (255, 255, 255, 255)
  gray = (100, 100, 120, 255)

  # Dimensions
  padding = size // 8
  center = size // 2
  radius = size // 2 - padding

  # Draw rounded rectangle background with gradient effect
  corner_radius = size // 5

  # Background - dark with subtle gradient
  for i in range(corner_radius):
    alpha = 255
    color = (12 + i//4, 12 + i//4, 18 + i//4, alpha)
    draw.rounded_rectangle(
      [padding//2 + i//2, padding//2 + i//2,
       size - padding//2 - i//2, size - padding//2 - i//2],
      radius=corner_radius - i//2,
      fill=color
    )

  # Main background
  draw.rounded_rectangle(
    [padding//2, padding//2, size - padding//2, size - padding//2],
    radius=corner_radius,
    fill=(16, 16, 24, 255)
  )

  # Draw glowing border
  for i in range(3):
    opacity = 120 - i * 30
    draw.rounded_rectangle(
      [padding//2 + i, padding//2 + i,
       size - padding//2 - i, size - padding//2 - i],
      radius=corner_radius - i,
      outline=(0, 129, 242, opacity),
      width=2
    )

  # Draw network/globe circles
  circle_center = (center, center - size//20)
  main_radius = size // 3

  # Outer globe circle
  draw.ellipse(
    [circle_center[0] - main_radius, circle_center[1] - main_radius,
     circle_center[0] + main_radius, circle_center[1] + main_radius],
    outline=accent_cyan,
    width=max(2, size // 80)
  )

  # Horizontal ellipse (equator)
  draw.ellipse(
    [circle_center[0] - main_radius, circle_center[1] - main_radius // 3,
     circle_center[0] + main_radius, circle_center[1] + main_radius // 3],
    outline=gray,
    width=max(1, size // 120)
  )

  # Vertical ellipse (meridian)
  draw.ellipse(
    [circle_center[0] - main_radius // 3, circle_center[1] - main_radius,
     circle_center[0] + main_radius // 3, circle_center[1] + main_radius],
    outline=gray,
    width=max(1, size // 120)
  )

  # Draw DNS nodes as glowing dots
  node_positions = [
    (center - main_radius//2, center - main_radius//2),
    (center + main_radius//2, center - main_radius//3),
    (center - main_radius//3, center + main_radius//4),
    (center + main_radius//3, center + main_radius//2),
    (center, center - main_radius + size//20),
  ]

  node_size = max(4, size // 30)
  for pos in node_positions:
    # Glow
    for g in range(3):
      glow_size = node_size + g * 2
      opacity = 100 - g * 30
      draw.ellipse(
        [pos[0] - glow_size, pos[1] - glow_size,
         pos[0] + glow_size, pos[1] + glow_size],
        fill=(0, 200, 255, opacity)
      )
    # Core
    draw.ellipse(
      [pos[0] - node_size//2, pos[1] - node_size//2,
       pos[0] + node_size//2, pos[1] + node_size//2],
      fill=white
    )

  # Draw connection lines between nodes
  line_width = max(1, size // 100)
  for i, pos1 in enumerate(node_positions):
    for pos2 in node_positions[i+1:i+3]:
      draw.line([pos1, pos2], fill=(0, 129, 242, 100), width=line_width)

  # Draw "M" letter in the center
  font_size = size // 4
  try:
    font = ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", font_size)
  except:
    try:
      font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
      font = ImageFont.load_default()

  # Draw M with glow effect
  m_pos = (center, center + size//10)

  # Glow layers
  for offset in [(0, 2), (2, 0), (-2, 0), (0, -2), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
    draw.text(
      (m_pos[0] + offset[0], m_pos[1] + offset[1]),
      "M",
      fill=(0, 129, 242, 60),
      font=font,
      anchor="mm"
    )

  # Main letter
  draw.text(m_pos, "M", fill=white, font=font, anchor="mm")

  # Add "DNS" text below
  dns_font_size = size // 10
  try:
    dns_font = ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", dns_font_size)
  except:
    try:
      dns_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", dns_font_size)
    except:
      dns_font = ImageFont.load_default()

  draw.text(
    (center, size - padding - size//12),
    "DNS",
    fill=accent_cyan,
    font=dns_font,
    anchor="mm"
  )

  return img


def main():
  # Icon sizes required for macOS
  sizes = [16, 32, 64, 128, 256, 512, 1024]

  # Create iconset directory
  iconset_path = Path("/Users/dubs415/CLAUDE/manus-toolkit/Manus DNS.iconset")
  iconset_path.mkdir(exist_ok=True)

  print("Generating Manus DNS icon...")

  for size in sizes:
    # Regular resolution
    icon = create_manus_icon(size)
    icon.save(iconset_path / f"icon_{size}x{size}.png")
    print(f"  Created {size}x{size}")

    # Retina (@2x) - skip 1024 as it's already max
    if size <= 512:
      icon_2x = create_manus_icon(size * 2)
      icon_2x.save(iconset_path / f"icon_{size}x{size}@2x.png")
      print(f"  Created {size}x{size}@2x")

  print(f"\nIconset created at: {iconset_path}")
  print("Converting to .icns...")

  # Convert to icns
  icns_path = "/Users/dubs415/CLAUDE/manus-toolkit/Manus DNS.icns"
  os.system(f'iconutil -c icns "{iconset_path}" -o "{icns_path}"')

  if os.path.exists(icns_path):
    print(f"Icon created: {icns_path}")
  else:
    print("Error creating .icns file")


if __name__ == "__main__":
  main()
