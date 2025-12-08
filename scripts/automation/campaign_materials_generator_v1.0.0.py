#!/usr/bin/env python3
"""
DAVE FOR MAYOR - COMPREHENSIVE CAMPAIGN MATERIALS GENERATOR
============================================================
This script generates ALL campaign materials for three slogans.
Designed to be run by Claude Code for easy regeneration.

SLOGANS:
1. "weird enough to care"
2. "biggest room in the world / is room for improvement"  
3. "mayor that listens / government that responds"

USAGE:
    python generate_all_materials.py

OUTPUT:
    /mnt/user-data/outputs/campaign_materials/
"""

from PIL import Image, ImageDraw, ImageFont
import math
import os
import qrcode

# =============================================================================
# CONFIGURATION - UPDATE THESE FOR YOUR SYSTEM
# =============================================================================

# Output directory - change to your preferred location
OUTPUT_BASE = './campaign_materials'

# =============================================================================
# FONT CONFIGURATION - Script will try each path until one works
# =============================================================================

import platform

SYSTEM = platform.system()

if SYSTEM == 'Darwin':  # macOS
    TYPEWRITER_PATHS = [
        '/Library/Fonts/Courier New Bold.ttf',
        '/System/Library/Fonts/Courier.dfont',
        '/Library/Fonts/TeX Gyre Cursor Bold.otf',
    ]
    SERIF_ITALIC_PATHS = [
        '/Library/Fonts/Times New Roman Italic.ttf',
        '/System/Library/Fonts/Times.ttc',
    ]
    SERIF_REGULAR_PATHS = [
        '/Library/Fonts/Times New Roman.ttf',
        '/System/Library/Fonts/Times.ttc',
    ]
    SERIF_BOLD_PATHS = [
        '/Library/Fonts/Times New Roman Bold.ttf',
        '/System/Library/Fonts/Times.ttc',
    ]
elif SYSTEM == 'Windows':
    TYPEWRITER_PATHS = [
        'C:/Windows/Fonts/courbd.ttf',
        'C:/Windows/Fonts/cour.ttf',
    ]
    SERIF_ITALIC_PATHS = [
        'C:/Windows/Fonts/timesi.ttf',
        'C:/Windows/Fonts/times.ttf',
    ]
    SERIF_REGULAR_PATHS = [
        'C:/Windows/Fonts/times.ttf',
    ]
    SERIF_BOLD_PATHS = [
        'C:/Windows/Fonts/timesbd.ttf',
        'C:/Windows/Fonts/times.ttf',
    ]
else:  # Linux and others
    TYPEWRITER_PATHS = [
        '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrecursor-bold.otf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf',
    ]
    SERIF_ITALIC_PATHS = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf',
    ]
    SERIF_REGULAR_PATHS = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
    ]
    SERIF_BOLD_PATHS = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',
    ]

def find_font(paths):
    """Find first available font from list of paths"""
    for path in paths:
        if os.path.exists(path):
            return path
    return None

# These will be set after imports
TYPEWRITER_BOLD = None
SERIF_ITALIC = None
SERIF_REGULAR = None
SERIF_BOLD = None

# Brand Colors
NAVY = (0, 32, 91)
GOLD = (255, 199, 44)
WHITE = (255, 255, 255)
LIGHT_GOLD = (255, 223, 128)

# Slogans Configuration
SLOGANS = {
    'weird': {
        'name': 'weird_enough_to_care',
        'line1': 'weird enough to care',
        'line2': None,  # Single line slogan
        'short': 'weird enough to care'
    },
    'biggest': {
        'name': 'biggest_room',
        'line1': 'biggest room in the world',
        'line2': 'is room for improvement',
        'short': 'room for improvement'
    },
    'mayor': {
        'name': 'mayor_that_listens',
        'line1': 'mayor that listens',
        'line2': 'government that responds',
        'short': 'listens & responds'
    }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def ensure_dir(path):
    """Create directory if it doesn't exist"""
    os.makedirs(path, exist_ok=True)
    return path

def get_font(font_path, size):
    """Load font with fallback"""
    try:
        return ImageFont.truetype(font_path, size)
    except:
        return ImageFont.load_default()

def center_text(draw, text, font, y, width, fill):
    """Draw centered text"""
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (width - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]  # Return height

def draw_slogan(draw, slogan_key, x, y, font_size, fill, width=None, center=True):
    """Draw slogan (handles 1 or 2 line slogans)"""
    s = SLOGANS[slogan_key]
    font = get_font(SERIF_ITALIC, font_size)
    
    if s['line2']:
        # Two line slogan
        if center and width:
            center_text(draw, s['line1'], font, y, width, fill)
            center_text(draw, s['line2'], font, y + font_size + 10, width, fill)
        else:
            draw.text((x, y), s['line1'], font=font, fill=fill)
            draw.text((x, y + font_size + 10), s['line2'], font=font, fill=fill)
        return font_size * 2 + 10
    else:
        # Single line slogan
        if center and width:
            center_text(draw, s['line1'], font, y, width, fill)
        else:
            draw.text((x, y), s['line1'], font=font, fill=fill)
        return font_size

# =============================================================================
# MATERIAL GENERATORS
# =============================================================================

def create_palm_cards(slogan_key):
    """
    Palm Card - 4x6 inches at 150 DPI (600x900px)
    Pocket-sized handout for door-to-door canvassing
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 600, 900
    img = Image.new('RGB', (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    
    # Gold border
    draw.rectangle([15, 15, w-15, h-15], outline=GOLD, width=4)
    
    # DAVE
    font_dave = get_font(TYPEWRITER_BOLD, 140)
    center_text(draw, "DAVE", font_dave, 80, w, GOLD)
    
    # Slogan
    draw_slogan(draw, slogan_key, 0, 260, 42, GOLD, w, center=True)
    
    # Divider line
    draw.line([(100, 420), (w-100, 420)], fill=GOLD, width=2)
    
    # Key message
    font_msg = get_font(SERIF_REGULAR, 28)
    messages = [
        "Independent for Mayor",
        "Louisville 2026",
        "",
        "✓ 46 Mini Police Substations",
        "✓ 18 Community Wellness Centers", 
        "✓ Zero Tax Increases"
    ]
    y = 450
    for msg in messages:
        if msg:
            center_text(draw, msg, font_msg, y, w, WHITE)
        y += 38
    
    # Website
    font_web = get_font(SERIF_BOLD, 36)
    center_text(draw, "rundaverun.org", font_web, h - 100, w, GOLD)
    
    img.save(f'{out_dir}/palm_card.png')
    print(f"  Created: {s['name']}/palm_card.png")

def create_facebook_cover(slogan_key):
    """
    Facebook Cover Photo - 820x312px (recommended size)
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 820, 312
    img = Image.new('RGB', (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    
    # DAVE on left
    font_dave = get_font(TYPEWRITER_BOLD, 140)
    draw.text((50, 80), "DAVE", font=font_dave, fill=GOLD)
    
    # Slogan on right
    font_slogan = get_font(SERIF_ITALIC, 36)
    if s['line2']:
        draw.text((400, 100), s['line1'], font=font_slogan, fill=GOLD)
        draw.text((400, 145), s['line2'], font=font_slogan, fill=GOLD)
    else:
        draw.text((400, 120), s['line1'], font=font_slogan, fill=GOLD)
    
    # Website
    font_web = get_font(SERIF_REGULAR, 28)
    draw.text((400, 220), "rundaverun.org", font=font_web, fill=WHITE)
    
    img.save(f'{out_dir}/facebook_cover.png')
    print(f"  Created: {s['name']}/facebook_cover.png")

def create_linkedin_banner(slogan_key):
    """
    LinkedIn Banner - 1584x396px
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 1584, 396
    img = Image.new('RGB', (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    
    # DAVE
    font_dave = get_font(TYPEWRITER_BOLD, 180)
    draw.text((100, 100), "DAVE", font=font_dave, fill=GOLD)
    
    # Slogan
    font_slogan = get_font(SERIF_ITALIC, 48)
    if s['line2']:
        draw.text((650, 130), s['line1'], font=font_slogan, fill=GOLD)
        draw.text((650, 190), s['line2'], font=font_slogan, fill=GOLD)
    else:
        draw.text((650, 160), s['line1'], font=font_slogan, fill=GOLD)
    
    # Website & tagline
    font_web = get_font(SERIF_REGULAR, 36)
    draw.text((650, 280), "rundaverun.org | Independent for Mayor | Louisville 2026", font=font_web, fill=WHITE)
    
    img.save(f'{out_dir}/linkedin_banner.png')
    print(f"  Created: {s['name']}/linkedin_banner.png")

def create_profile_picture(slogan_key):
    """
    Circular Profile Picture - 400x400px with circular mask
    For all social media platforms
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    size = 400
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw circular background
    draw.ellipse([0, 0, size, size], fill=NAVY)
    
    # Gold ring
    draw.ellipse([8, 8, size-8, size-8], outline=GOLD, width=6)
    
    # DAVE centered
    font_dave = get_font(TYPEWRITER_BOLD, 110)
    bbox = draw.textbbox((0, 0), "DAVE", font=font_dave)
    x = (size - (bbox[2] - bbox[0])) // 2
    y = (size - (bbox[3] - bbox[1])) // 2 - 20
    draw.text((x, y), "DAVE", font=font_dave, fill=GOLD)
    
    # Small tagline
    font_tag = get_font(SERIF_ITALIC, 28)
    center_text(draw, "for Mayor", font_tag, 270, size, WHITE)
    
    img.save(f'{out_dir}/profile_picture.png')
    
    # Also save smaller sizes
    for s_size in [200, 150, 100]:
        resized = img.resize((s_size, s_size), Image.LANCZOS)
        resized.save(f'{out_dir}/profile_picture_{s_size}.png')
    
    print(f"  Created: {s['name']}/profile_picture.png (+ 3 sizes)")

def create_instagram_story(slogan_key):
    """
    Instagram/TikTok Story - 1080x1920px (9:16 vertical)
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 1080, 1920
    img = Image.new('RGB', (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    
    # Gold border
    draw.rectangle([30, 30, w-30, h-30], outline=GOLD, width=6)
    
    # DAVE - large
    font_dave = get_font(TYPEWRITER_BOLD, 280)
    center_text(draw, "DAVE", font_dave, 500, w, GOLD)
    
    # Slogan
    font_slogan = get_font(SERIF_ITALIC, 70)
    if s['line2']:
        center_text(draw, s['line1'], font_slogan, 900, w, GOLD)
        center_text(draw, s['line2'], font_slogan, 990, w, GOLD)
    else:
        center_text(draw, s['line1'], font_slogan, 950, w, GOLD)
    
    # Call to action
    font_cta = get_font(SERIF_BOLD, 50)
    center_text(draw, "for MAYOR", font_cta, 1200, w, WHITE)
    center_text(draw, "Louisville 2026", font_cta, 1270, w, WHITE)
    
    # Website
    font_web = get_font(SERIF_REGULAR, 60)
    center_text(draw, "rundaverun.org", font_web, 1550, w, GOLD)
    
    img.save(f'{out_dir}/instagram_story.png')
    print(f"  Created: {s['name']}/instagram_story.png")

def create_door_hanger(slogan_key):
    """
    Door Hanger - 4x9 inches at 150 DPI (600x1350px)
    With door knob cutout indication
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 600, 1350
    img = Image.new('RGB', (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    
    # Gold border
    draw.rectangle([15, 15, w-15, h-15], outline=GOLD, width=4)
    
    # Door knob hole indicator (circle at top)
    hole_y = 80
    hole_r = 50
    draw.ellipse([w//2 - hole_r, hole_y - hole_r, w//2 + hole_r, hole_y + hole_r], 
                 outline=GOLD, width=3)
    draw.line([(w//2 - hole_r, hole_y), (w//2 + hole_r, hole_y)], fill=GOLD, width=2)
    
    # DAVE
    font_dave = get_font(TYPEWRITER_BOLD, 130)
    center_text(draw, "DAVE", font_dave, 180, w, GOLD)
    
    # Slogan
    draw_slogan(draw, slogan_key, 0, 350, 38, GOLD, w, center=True)
    
    # Divider
    draw.line([(80, 500), (w-80, 500)], fill=GOLD, width=2)
    
    # Message
    font_head = get_font(SERIF_BOLD, 32)
    center_text(draw, "Sorry we missed you!", font_head, 540, w, WHITE)
    
    font_body = get_font(SERIF_REGULAR, 26)
    messages = [
        "",
        "Dave Biggers is running",
        "as an Independent for Mayor",
        "of Louisville in 2026.",
        "",
        "Key Priorities:",
        "• 46 Mini Police Substations",
        "• 18 Wellness Centers",
        "• Zero Tax Increases",
        "• Participatory Budgeting"
    ]
    y = 600
    for msg in messages:
        if msg:
            center_text(draw, msg, font_body, y, w, WHITE)
        y += 36
    
    # Website at bottom
    font_web = get_font(SERIF_BOLD, 40)
    center_text(draw, "rundaverun.org", font_web, h - 120, w, GOLD)
    
    img.save(f'{out_dir}/door_hanger.png')
    print(f"  Created: {s['name']}/door_hanger.png")

def create_flyer(slogan_key):
    """
    Flyer/Handbill - 8.5x11 inches at 100 DPI (850x1100px)
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 850, 1100
    img = Image.new('RGB', (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    
    # Gold border
    draw.rectangle([20, 20, w-20, h-20], outline=GOLD, width=5)
    
    # DAVE
    font_dave = get_font(TYPEWRITER_BOLD, 180)
    center_text(draw, "DAVE", font_dave, 60, w, GOLD)
    
    # Slogan
    draw_slogan(draw, slogan_key, 0, 280, 50, GOLD, w, center=True)
    
    # Divider
    draw.line([(100, 430), (w-100, 430)], fill=GOLD, width=3)
    
    # Main content
    font_head = get_font(SERIF_BOLD, 40)
    center_text(draw, "Independent for Mayor", font_head, 470, w, WHITE)
    center_text(draw, "Louisville 2026", font_head, 520, w, WHITE)
    
    font_body = get_font(SERIF_REGULAR, 28)
    policies = [
        "",
        "A NEW APPROACH TO PUBLIC SAFETY:",
        "",
        "✓ 46 Mini Police Substations",
        "   One in every neighborhood",
        "",
        "✓ 18 Community Wellness Centers", 
        "   Mental health & crisis response",
        "",
        "✓ Evidence-Based Policies",
        "   Proven in cities nationwide",
        "",
        "✓ Zero Tax Increases",
        "   Within the existing $1.025B budget"
    ]
    y = 580
    for line in policies:
        if line:
            center_text(draw, line, font_body, y, w, WHITE)
        y += 34
    
    # Website
    font_web = get_font(SERIF_BOLD, 48)
    center_text(draw, "rundaverun.org", font_web, h - 100, w, GOLD)
    
    img.save(f'{out_dir}/flyer.png')
    print(f"  Created: {s['name']}/flyer.png")

def create_volunteer_badge(slogan_key):
    """
    Volunteer Badge - 3x4 inches at 150 DPI (450x600px)
    Name tag style badge
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 450, 600
    img = Image.new('RGB', (w, h), WHITE)
    draw = ImageDraw.Draw(img)
    
    # Navy header
    draw.rectangle([0, 0, w, 150], fill=NAVY)
    
    # DAVE in header
    font_dave = get_font(TYPEWRITER_BOLD, 70)
    center_text(draw, "DAVE", font_dave, 20, w, GOLD)
    
    # Slogan small
    font_slogan = get_font(SERIF_ITALIC, 22)
    if s['line2']:
        center_text(draw, s['line1'], font_slogan, 100, w, WHITE)
        center_text(draw, s['line2'], font_slogan, 125, w, WHITE)
    else:
        center_text(draw, s['line1'], font_slogan, 110, w, WHITE)
    
    # "VOLUNTEER" label
    font_label = get_font(SERIF_BOLD, 36)
    center_text(draw, "VOLUNTEER", font_label, 180, w, NAVY)
    
    # Name area (blank for writing)
    draw.rectangle([40, 250, w-40, 400], outline=NAVY, width=2)
    font_name_label = get_font(SERIF_REGULAR, 20)
    draw.text((50, 255), "NAME:", font=font_name_label, fill=NAVY)
    
    # Website at bottom
    font_web = get_font(SERIF_REGULAR, 28)
    center_text(draw, "rundaverun.org", font_web, 500, w, NAVY)
    
    # Gold stripe at bottom
    draw.rectangle([0, h-30, w, h], fill=GOLD)
    
    img.save(f'{out_dir}/volunteer_badge.png')
    print(f"  Created: {s['name']}/volunteer_badge.png")

def create_table_banner(slogan_key):
    """
    Table Banner - 6x2 feet at 50 DPI (3600x1200px)
    For event tables
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 3600, 1200
    img = Image.new('RGB', (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    
    # Gold border
    draw.rectangle([20, 20, w-20, h-20], outline=GOLD, width=8)
    
    # DAVE - large
    font_dave = get_font(TYPEWRITER_BOLD, 500)
    center_text(draw, "DAVE", font_dave, 150, w, GOLD)
    
    # Slogan
    font_slogan = get_font(SERIF_ITALIC, 120)
    if s['line2']:
        center_text(draw, s['line1'], font_slogan, 750, w, GOLD)
        center_text(draw, s['line2'], font_slogan, 900, w, GOLD)
    else:
        center_text(draw, s['line1'], font_slogan, 850, w, GOLD)
    
    # Website on sides
    font_web = get_font(SERIF_REGULAR, 80)
    draw.text((100, h - 150), "rundaverun.org", font=font_web, fill=WHITE)
    bbox = draw.textbbox((0, 0), "rundaverun.org", font=font_web)
    draw.text((w - 100 - (bbox[2] - bbox[0]), h - 150), "rundaverun.org", font=font_web, fill=WHITE)
    
    img.save(f'{out_dir}/table_banner.png')
    print(f"  Created: {s['name']}/table_banner.png")

def create_popup_banner(slogan_key):
    """
    Pop-up/Retractable Banner - 33x80 inches at 50 DPI (1650x4000px)
    Vertical standing banner
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 1650, 4000
    img = Image.new('RGB', (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    
    # Gold border
    draw.rectangle([30, 30, w-30, h-30], outline=GOLD, width=10)
    
    # DAVE at top
    font_dave = get_font(TYPEWRITER_BOLD, 400)
    center_text(draw, "DAVE", font_dave, 200, w, GOLD)
    
    # Slogan
    font_slogan = get_font(SERIF_ITALIC, 100)
    if s['line2']:
        center_text(draw, s['line1'], font_slogan, 750, w, GOLD)
        center_text(draw, s['line2'], font_slogan, 880, w, GOLD)
    else:
        center_text(draw, s['line1'], font_slogan, 800, w, GOLD)
    
    # "for MAYOR"
    font_mayor = get_font(SERIF_BOLD, 150)
    center_text(draw, "for MAYOR", font_mayor, 1150, w, WHITE)
    
    # Key points
    font_points = get_font(SERIF_REGULAR, 70)
    points = [
        "46 Mini Police Substations",
        "18 Community Wellness Centers",
        "Evidence-Based Policies",
        "Zero Tax Increases"
    ]
    y = 1600
    for point in points:
        center_text(draw, f"• {point}", font_points, y, w, WHITE)
        y += 120
    
    # Louisville 2026
    font_city = get_font(SERIF_BOLD, 100)
    center_text(draw, "Louisville 2026", font_city, 2800, w, GOLD)
    
    # Website large at bottom
    font_web = get_font(SERIF_BOLD, 120)
    center_text(draw, "rundaverun.org", font_web, 3500, w, GOLD)
    
    img.save(f'{out_dir}/popup_banner.png')
    print(f"  Created: {s['name']}/popup_banner.png")

def create_qr_code():
    """
    QR Code Graphics linking to rundaverun.org
    Creates styled QR codes with branding
    """
    out_dir = ensure_dir(f'{OUTPUT_BASE}/shared')
    
    # Generate base QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data('https://rundaverun.org')
    qr.make(fit=True)
    
    # Create QR with brand colors
    qr_img = qr.make_image(fill_color=NAVY, back_color=WHITE)
    qr_img = qr_img.convert('RGB')
    qr_size = qr_img.size[0]
    
    # Create branded version with label
    w, h = qr_size + 40, qr_size + 100
    img = Image.new('RGB', (w, h), WHITE)
    draw = ImageDraw.Draw(img)
    
    # Paste QR
    img.paste(qr_img, (20, 20))
    
    # Add label below
    font_label = get_font(SERIF_BOLD, 24)
    center_text(draw, "Scan to Learn More", font_label, qr_size + 30, w, NAVY)
    center_text(draw, "rundaverun.org", font_label, qr_size + 60, w, NAVY)
    
    img.save(f'{out_dir}/qr_code_branded.png')
    
    # Plain QR
    qr_img.save(f'{out_dir}/qr_code_plain.png')
    
    # Large version for print
    qr_large = qr_img.resize((600, 600), Image.NEAREST)
    qr_large.save(f'{out_dir}/qr_code_large.png')
    
    print(f"  Created: shared/qr_code_branded.png")
    print(f"  Created: shared/qr_code_plain.png")
    print(f"  Created: shared/qr_code_large.png")

def create_email_header(slogan_key):
    """
    Email Header - 600x200px
    For email campaigns
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 600, 200
    img = Image.new('RGB', (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    
    # DAVE on left
    font_dave = get_font(TYPEWRITER_BOLD, 90)
    draw.text((30, 50), "DAVE", font=font_dave, fill=GOLD)
    
    # Slogan on right
    font_slogan = get_font(SERIF_ITALIC, 26)
    if s['line2']:
        draw.text((280, 60), s['line1'], font=font_slogan, fill=GOLD)
        draw.text((280, 95), s['line2'], font=font_slogan, fill=GOLD)
    else:
        draw.text((280, 75), s['line1'], font=font_slogan, fill=GOLD)
    
    # Website
    font_web = get_font(SERIF_REGULAR, 22)
    draw.text((280, 140), "rundaverun.org", font=font_web, fill=WHITE)
    
    img.save(f'{out_dir}/email_header.png')
    print(f"  Created: {s['name']}/email_header.png")

def create_donation_card(slogan_key):
    """
    Donation/Thank You Card - 5x7 inches at 100 DPI (500x700px)
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 500, 700
    
    # Front
    img = Image.new('RGB', (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([15, 15, w-15, h-15], outline=GOLD, width=3)
    
    font_dave = get_font(TYPEWRITER_BOLD, 120)
    center_text(draw, "DAVE", font_dave, 150, w, GOLD)
    
    draw_slogan(draw, slogan_key, 0, 320, 32, GOLD, w, center=True)
    
    font_sub = get_font(SERIF_REGULAR, 28)
    center_text(draw, "for Mayor", font_sub, 450, w, WHITE)
    center_text(draw, "Louisville 2026", font_sub, 490, w, WHITE)
    
    font_web = get_font(SERIF_BOLD, 32)
    center_text(draw, "rundaverun.org", font_web, h - 80, w, GOLD)
    
    img.save(f'{out_dir}/card_front.png')
    
    # Back (thank you)
    img = Image.new('RGB', (w, h), WHITE)
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([15, 15, w-15, h-15], outline=NAVY, width=3)
    
    font_thanks = get_font(SERIF_BOLD, 40)
    center_text(draw, "Thank You!", font_thanks, 100, w, NAVY)
    
    font_body = get_font(SERIF_REGULAR, 24)
    messages = [
        "Your support makes",
        "this campaign possible.",
        "",
        "Together, we're building",
        "a Louisville that works",
        "for everyone.",
        "",
        "— Dave Biggers"
    ]
    y = 200
    for msg in messages:
        if msg:
            center_text(draw, msg, font_body, y, w, NAVY)
        y += 40
    
    # Gold stripe at bottom
    draw.rectangle([0, h-50, w, h], fill=GOLD)
    
    img.save(f'{out_dir}/card_back.png')
    print(f"  Created: {s['name']}/card_front.png")
    print(f"  Created: {s['name']}/card_back.png")

def create_letterhead(slogan_key):
    """
    Letterhead - 8.5x11 at 100 DPI (850x1100px)
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 850, 1100
    img = Image.new('RGB', (w, h), WHITE)
    draw = ImageDraw.Draw(img)
    
    # Navy header bar
    draw.rectangle([0, 0, w, 120], fill=NAVY)
    
    # DAVE in header
    font_dave = get_font(TYPEWRITER_BOLD, 60)
    draw.text((50, 30), "DAVE", font=font_dave, fill=GOLD)
    
    # Slogan in header
    font_slogan = get_font(SERIF_ITALIC, 22)
    if s['line2']:
        draw.text((250, 35), s['line1'], font=font_slogan, fill=GOLD)
        draw.text((250, 62), s['line2'], font=font_slogan, fill=GOLD)
    else:
        draw.text((250, 45), s['line1'], font=font_slogan, fill=GOLD)
    
    # Website in header
    font_web = get_font(SERIF_REGULAR, 20)
    bbox = draw.textbbox((0, 0), "rundaverun.org", font=font_web)
    draw.text((w - 50 - (bbox[2] - bbox[0]), 50), "rundaverun.org", font=font_web, fill=WHITE)
    
    # Gold line under header
    draw.rectangle([0, 120, w, 125], fill=GOLD)
    
    # Footer
    font_footer = get_font(SERIF_REGULAR, 16)
    footer_text = "Dave Biggers for Mayor • Louisville 2026 • rundaverun.org"
    bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    draw.text(((w - (bbox[2] - bbox[0])) // 2, h - 50), footer_text, font=font_footer, fill=NAVY)
    
    # Gold line above footer
    draw.rectangle([100, h - 70, w - 100, h - 68], fill=GOLD)
    
    img.save(f'{out_dir}/letterhead.png')
    print(f"  Created: {s['name']}/letterhead.png")

def create_mug_design(slogan_key):
    """
    Mug Design - wrap-around template 900x350px
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 900, 350
    img = Image.new('RGB', (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    
    # DAVE on left
    font_dave = get_font(TYPEWRITER_BOLD, 140)
    draw.text((50, 100), "DAVE", font=font_dave, fill=GOLD)
    
    # Slogan in middle
    font_slogan = get_font(SERIF_ITALIC, 36)
    if s['line2']:
        draw.text((450, 110), s['line1'], font=font_slogan, fill=GOLD)
        draw.text((450, 155), s['line2'], font=font_slogan, fill=GOLD)
    else:
        draw.text((450, 130), s['line1'], font=font_slogan, fill=GOLD)
    
    # Website on right
    font_web = get_font(SERIF_REGULAR, 28)
    draw.text((450, 230), "rundaverun.org", font=font_web, fill=WHITE)
    
    img.save(f'{out_dir}/mug_design.png')
    print(f"  Created: {s['name']}/mug_design.png")

def create_tote_bag(slogan_key):
    """
    Tote Bag Design - 12x12 inch print area (1200x1200px at 100 DPI)
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    size = 1200
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # DAVE
    font_dave = get_font(TYPEWRITER_BOLD, 300)
    center_text(draw, "DAVE", font_dave, 300, size, NAVY)
    
    # Slogan
    font_slogan = get_font(SERIF_ITALIC, 70)
    if s['line2']:
        center_text(draw, s['line1'], font_slogan, 680, size, NAVY)
        center_text(draw, s['line2'], font_slogan, 770, size, NAVY)
    else:
        center_text(draw, s['line1'], font_slogan, 720, size, NAVY)
    
    img.save(f'{out_dir}/tote_bag.png')
    print(f"  Created: {s['name']}/tote_bag.png")

def create_hat_design(slogan_key):
    """
    Hat/Cap Design - front panel 400x300px
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    w, h = 400, 300
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # DAVE
    font_dave = get_font(TYPEWRITER_BOLD, 100)
    center_text(draw, "DAVE", font_dave, 80, w, NAVY)
    
    # Short slogan or "2026"
    font_sub = get_font(SERIF_ITALIC, 32)
    center_text(draw, "Louisville 2026", font_sub, 200, w, NAVY)
    
    img.save(f'{out_dir}/hat_design.png')
    print(f"  Created: {s['name']}/hat_design.png")

def create_sticker_diecut(slogan_key):
    """
    Die-cut Sticker Design - various shapes
    """
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/{s["name"]}')
    
    # Circular sticker
    size = 400
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Circle background
    draw.ellipse([10, 10, size-10, size-10], fill=NAVY)
    draw.ellipse([20, 20, size-20, size-20], outline=GOLD, width=4)
    
    # DAVE
    font_dave = get_font(TYPEWRITER_BOLD, 90)
    center_text(draw, "DAVE", font_dave, 120, size, GOLD)
    
    # Short text
    font_sub = get_font(SERIF_ITALIC, 28)
    center_text(draw, "for Mayor", font_sub, 230, size, WHITE)
    center_text(draw, "2026", font_sub, 265, size, WHITE)
    
    img.save(f'{out_dir}/sticker_circle.png')
    
    # Rectangular sticker
    w, h = 500, 200
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Rounded rectangle
    draw.rounded_rectangle([5, 5, w-5, h-5], radius=20, fill=NAVY)
    draw.rounded_rectangle([10, 10, w-10, h-10], radius=18, outline=GOLD, width=3)
    
    # DAVE
    font_dave = get_font(TYPEWRITER_BOLD, 80)
    draw.text((30, 50), "DAVE", font=font_dave, fill=GOLD)
    
    # 2026
    font_year = get_font(SERIF_BOLD, 50)
    draw.text((300, 70), "2026", font=font_year, fill=WHITE)
    
    img.save(f'{out_dir}/sticker_rect.png')
    
    print(f"  Created: {s['name']}/sticker_circle.png")
    print(f"  Created: {s['name']}/sticker_rect.png")

# =============================================================================
# BUTTON GENERATOR
# =============================================================================

# 33 College-style color schemes
BUTTON_COLORS = {
    'black_white': {'bg': (30, 30, 30), 'text': (255, 255, 255)},
    'brown_cream': {'bg': (78, 54, 41), 'text': (245, 235, 220)},
    'navy_gold': {'bg': (0, 32, 91), 'text': (255, 199, 44)},
    'purple_gold': {'bg': (75, 0, 130), 'text': (255, 215, 0)},
    'teal_white': {'bg': (0, 102, 102), 'text': (255, 255, 255)},
    'crimson_cream': {'bg': (153, 0, 0), 'text': (245, 235, 220)},
    'crimson_white': {'bg': (153, 0, 0), 'text': (255, 255, 255)},
    'green_gold': {'bg': (0, 100, 0), 'text': (255, 215, 0)},
    'green_white': {'bg': (0, 100, 0), 'text': (255, 255, 255)},
    'red_white': {'bg': (200, 16, 46), 'text': (255, 255, 255)},
    'red_black': {'bg': (200, 16, 46), 'text': (0, 0, 0)},
    'orange_white': {'bg': (255, 130, 0), 'text': (255, 255, 255)},
    'orange_black': {'bg': (255, 130, 0), 'text': (0, 0, 0)},
    'yellow_black': {'bg': (255, 215, 0), 'text': (0, 0, 0)},
    'pink_white': {'bg': (255, 105, 180), 'text': (255, 255, 255)},
    'maroon_white': {'bg': (128, 0, 0), 'text': (255, 255, 255)},
    'royalblue_white': {'bg': (0, 35, 102), 'text': (255, 255, 255)},
    'kelly_green_white': {'bg': (0, 128, 0), 'text': (255, 255, 255)},
    'olive_tan': {'bg': (85, 107, 47), 'text': (210, 180, 140)},
    'silver_black': {'bg': (192, 192, 192), 'text': (0, 0, 0)},
    'gray_blue': {'bg': (128, 128, 128), 'text': (135, 206, 235)},
    'scarlet_gray': {'bg': (200, 16, 46), 'text': (128, 128, 128)},
    'white_navy': {'bg': (255, 255, 255), 'text': (0, 32, 91)},
    'cream_brick': {'bg': (245, 235, 220), 'text': (139, 69, 19)},
    'tan_white': {'bg': (210, 180, 140), 'text': (255, 255, 255)},
    'cardinal_red_white': {'bg': (196, 30, 58), 'text': (255, 255, 255)},
    'uk_blue_white': {'bg': (0, 51, 160), 'text': (255, 255, 255)},
    'louisville_blue_gold': {'bg': (0, 32, 91), 'text': (255, 199, 44)},
    'louisville_gold_blue': {'bg': (255, 199, 44), 'text': (0, 32, 91)},
    'forest_green_gold': {'bg': (34, 139, 34), 'text': (255, 215, 0)},
    'burgundy_gold': {'bg': (128, 0, 32), 'text': (255, 215, 0)},
    'charcoal_gold': {'bg': (54, 69, 79), 'text': (255, 215, 0)},
    'slate_white': {'bg': (112, 128, 144), 'text': (255, 255, 255)},
}

BUTTON_SIZES = [400, 320, 200, 128]

def draw_arc_text(draw, text, center, radius, start_angle, end_angle, font, fill, top=True):
    """Draw text along an arc"""
    if not text:
        return
    
    chars = list(text)
    n = len(chars)
    
    if n == 0:
        return
    
    total_angle = end_angle - start_angle
    if n > 1:
        angle_step = total_angle / (n - 1)
    else:
        angle_step = 0
    
    for i, char in enumerate(chars):
        if n > 1:
            angle = start_angle + i * angle_step
        else:
            angle = (start_angle + end_angle) / 2
        
        rad = math.radians(angle)
        x = center[0] + radius * math.cos(rad)
        y = center[1] - radius * math.sin(rad)
        
        char_img = Image.new('RGBA', (60, 60), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_img)
        
        bbox = char_draw.textbbox((0, 0), char, font=font)
        char_w = bbox[2] - bbox[0]
        char_h = bbox[3] - bbox[1]
        
        char_draw.text((30 - char_w // 2, 30 - char_h // 2), char, font=font, fill=fill)
        
        if top:
            rotation = 90 - angle
        else:
            rotation = 270 - angle
        
        rotated = char_img.rotate(rotation, resample=Image.BICUBIC, expand=True)
        
        paste_x = int(x - rotated.width // 2)
        paste_y = int(y - rotated.height // 2)
        
        draw._image.paste(rotated, (paste_x, paste_y), rotated)

def create_button(slogan_key, color_name, size):
    """Create a single button"""
    s = SLOGANS[slogan_key]
    colors = BUTTON_COLORS[color_name]
    
    bg_color = colors['bg']
    text_color = colors['text']
    
    canvas = 400
    img = Image.new('RGBA', (canvas, canvas), (128, 128, 128, 255))
    draw = ImageDraw.Draw(img)
    
    center = (canvas // 2, canvas // 2)
    radius = 180
    
    # Circle
    draw.ellipse([center[0] - radius, center[1] - radius,
                  center[0] + radius, center[1] + radius],
                 fill=bg_color, outline=text_color, width=4)
    
    # DAVE
    font_size = int(size * 0.22)
    font_dave = get_font(TYPEWRITER_BOLD, font_size)
    bbox = draw.textbbox((0, 0), "DAVE", font=font_dave)
    dave_w = bbox[2] - bbox[0]
    dave_h = bbox[3] - bbox[1]
    dave_y = center[1] - 55
    draw.text((center[0] - dave_w // 2, dave_y - dave_h // 2), "DAVE",
              font=font_dave, fill=text_color)
    
    # Arc text
    arc_font_size = int(size * 0.07)
    arc_font = get_font(SERIF_ITALIC, arc_font_size)
    
    # Top arc
    draw_arc_text(draw, s['line1'], center, radius - 32, 150, 30, arc_font, text_color, top=True)
    
    # Bottom arc
    if s['line2']:
        draw_arc_text(draw, s['line2'], center, radius - 45, 210, 330, arc_font, text_color, top=False)
    
    # Resize
    if size != canvas:
        img = img.resize((size, size), Image.LANCZOS)
    
    return img

def generate_buttons(slogan_key):
    """Generate all button variations for a slogan"""
    s = SLOGANS[slogan_key]
    out_dir = ensure_dir(f'{OUTPUT_BASE}/buttons_{s["name"]}')
    
    count = 0
    for color_name in BUTTON_COLORS:
        for size in BUTTON_SIZES:
            img = create_button(slogan_key, color_name, size)
            filename = f'{out_dir}/button_{color_name}_{size}.png'
            img.save(filename)
            count += 1
    
    print(f"  Created: {count} buttons in buttons_{s['name']}/")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def generate_all():
    """Generate all materials for all slogans"""
    
    # Initialize fonts
    global TYPEWRITER_BOLD, SERIF_ITALIC, SERIF_REGULAR, SERIF_BOLD
    TYPEWRITER_BOLD = find_font(TYPEWRITER_PATHS)
    SERIF_ITALIC = find_font(SERIF_ITALIC_PATHS)
    SERIF_REGULAR = find_font(SERIF_REGULAR_PATHS)
    SERIF_BOLD = find_font(SERIF_BOLD_PATHS)
    
    if not all([TYPEWRITER_BOLD, SERIF_ITALIC, SERIF_REGULAR, SERIF_BOLD]):
        print("WARNING: Some fonts not found. Using defaults.")
        print(f"  Typewriter: {TYPEWRITER_BOLD or 'NOT FOUND'}")
        print(f"  Serif Italic: {SERIF_ITALIC or 'NOT FOUND'}")
        print(f"  Serif Regular: {SERIF_REGULAR or 'NOT FOUND'}")
        print(f"  Serif Bold: {SERIF_BOLD or 'NOT FOUND'}")
    
    print("=" * 70)
    print("DAVE FOR MAYOR - CAMPAIGN MATERIALS GENERATOR")
    print("=" * 70)
    
    # Shared materials (QR codes)
    print("\n[SHARED MATERIALS]")
    create_qr_code()
    
    # Per-slogan materials
    for key in SLOGANS:
        print(f"\n[{SLOGANS[key]['name'].upper()}]")
        
        create_palm_cards(key)
        create_facebook_cover(key)
        create_linkedin_banner(key)
        create_profile_picture(key)
        create_instagram_story(key)
        create_door_hanger(key)
        create_flyer(key)
        create_volunteer_badge(key)
        create_table_banner(key)
        create_popup_banner(key)
        create_email_header(key)
        create_donation_card(key)
        create_letterhead(key)
        create_mug_design(key)
        create_tote_bag(key)
        create_hat_design(key)
        create_sticker_diecut(key)
        
        # Generate buttons
        generate_buttons(key)
    
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE!")
    print("=" * 70)
    print(f"\nOutput: {OUTPUT_BASE}/")
    print("\nFolders created:")
    print("  - weird_enough_to_care/     (materials)")
    print("  - biggest_room/             (materials)")
    print("  - mayor_that_listens/       (materials)")
    print("  - buttons_weird_enough_to_care/")
    print("  - buttons_biggest_room/")
    print("  - buttons_mayor_that_listens/")
    print("  - shared/                   (QR codes)")
    print("\nTotal: ~500 files")

if __name__ == "__main__":
    generate_all()
