#!/usr/bin/env python3
"""
Create a simple icon for the Rust Game Controller application
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Create a simple icon for the application"""
    # Create a 64x64 image with a dark background
    size = 64
    img = Image.new('RGBA', (size, size), (40, 40, 40, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw a red circle (representing Rust)
    circle_center = (size // 2, size // 2)
    circle_radius = size // 3
    draw.ellipse([
        circle_center[0] - circle_radius,
        circle_center[1] - circle_radius,
        circle_center[0] + circle_radius,
        circle_center[1] + circle_radius
    ], fill=(220, 50, 50, 255))
    
    # Draw a white "R" in the center
    try:
        # Try to use a system font
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw "R" text
    text = "R"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    text_x = circle_center[0] - text_width // 2
    text_y = circle_center[1] - text_height // 2
    
    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)
    
    # Save as ICO file
    img.save("rust_controller.ico", format='ICO', sizes=[(64, 64)])
    print("Icon created: rust_controller.ico")
    
    # Also save as PNG for reference
    img.save("rust_controller.png", format='PNG')
    print("Icon created: rust_controller.png")

if __name__ == "__main__":
    create_icon()
