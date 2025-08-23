#!/usr/bin/env python3
"""
Create a simple icon for the Rust Game Controller application
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Create an ICO file from camera.png for the application"""
    try:
        # Load the camera.png image
        if os.path.exists("camera.png"):
            img = Image.open("camera.png")
            
            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Create multiple sizes for the ICO file
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
            images = []
            
            for size in sizes:
                resized_img = img.resize(size, Image.Resampling.LANCZOS)
                images.append(resized_img)
            
            # Save as ICO file with multiple sizes
            img.save("rust_controller.ico", format='ICO', sizes=sizes)
            print("Icon created from camera.png: rust_controller.ico")
            
            # Also save a copy as PNG for reference
            img.save("rust_controller.png", format='PNG')
            print("Icon created: rust_controller.png")
            
        else:
            print("camera.png not found. Creating a default icon...")
            create_default_icon()
            
    except Exception as e:
        print(f"Error creating icon from camera.png: {e}")
        print("Creating a default icon instead...")
        create_default_icon()

def create_default_icon():
    """Create a simple default icon for the application"""
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
    print("Default icon created: rust_controller.ico")
    
    # Also save as PNG for reference
    img.save("rust_controller.png", format='PNG')
    print("Default icon created: rust_controller.png")

if __name__ == "__main__":
    create_icon()
