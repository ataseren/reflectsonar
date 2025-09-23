#!/usr/bin/env python3
"""
Utility script to help fix logo transparency issues
"""

def check_logo_requirements():
    """Check if logo file exists and provide guidance"""
    import os
    
    logo_files = ["reflect-sonar.png", "toolsentinel-logo.png"]
    
    print("=== Logo File Check ===")
    
    for logo_file in logo_files:
        if os.path.exists(logo_file):
            print(f"✅ Found: {logo_file}")
            file_size = os.path.getsize(logo_file)
            print(f"   Size: {file_size} bytes ({file_size/1024:.1f} KB)")
        else:
            print(f"❌ Missing: {logo_file}")
    
    print("\n=== Logo Requirements ===")
    print("📋 Optimal logo specifications:")
    print("   • Format: PNG with transparent background")
    print("   • Size: Any size (will be auto-scaled)")
    print("   • Background: Transparent (alpha channel)")
    print("   • Colors: Any, but avoid pure black if using black removal")
    
    print("\n=== Fixing Black Background ===")
    print("If your logo has a black background, try these solutions:")
    print()
    print("🔧 Method 1 - Image Editor (Recommended):")
    print("   1. Open logo in GIMP, Photoshop, or online editor")
    print("   2. Use 'Select by Color' tool to select black background")
    print("   3. Delete selected area or make it transparent")
    print("   4. Save as PNG with transparency")
    
    print("\n🔧 Method 2 - Python PIL (if PIL available):")
    print("   Run: python convert_logo_transparency.py")
    
    print("\n🔧 Method 3 - Online Tools:")
    print("   • remove.bg - Automatic background removal")
    print("   • photopea.com - Free online Photoshop")
    print("   • canva.com - Background remover tool")
    
    print("\n📝 Testing:")
    print("   Run: python test_logo_positioning.py")
    print("   Check the generated PDF for transparency results")

def create_pil_converter():
    """Create a PIL-based logo converter script"""
    converter_script = '''#!/usr/bin/env python3
"""
Convert logo to remove black background using PIL
"""
try:
    from PIL import Image
    import numpy as np
    
    def convert_logo_transparency(input_file="reflect-sonar.png", output_file="reflect-sonar-transparent.png"):
        """Convert black background to transparent"""
        try:
            # Open image
            img = Image.open(input_file)
            img = img.convert("RGBA")
            
            # Convert to numpy array
            data = np.array(img)
            
            # Define black color (with some tolerance)
            black = [0, 0, 0, 255]  # RGBA
            
            # Make black pixels transparent
            # You can adjust the tolerance (30) if needed
            tolerance = 30
            
            # Calculate distance from black for each pixel
            diff = np.abs(data[:,:,:3] - black[:3])  # Compare RGB only
            black_mask = np.all(diff <= tolerance, axis=2)  # True where pixel is close to black
            
            # Set alpha to 0 (transparent) for black pixels
            data[black_mask, 3] = 0
            
            # Convert back to image and save
            result_img = Image.fromarray(data, 'RGBA')
            result_img.save(output_file)
            
            print(f"✅ Converted {input_file} → {output_file}")
            print("📋 Black background removed, saved with transparency")
            
        except Exception as e:
            print(f"❌ Error converting logo: {e}")
            print("💡 Make sure PIL (Pillow) is installed: pip install Pillow")
    
    if __name__ == "__main__":
        convert_logo_transparency()
        
except ImportError:
    print("❌ PIL (Pillow) not available")
    print("💡 Install with: pip install Pillow")
    print("💡 Or use image editing software instead")
'''
    
    with open("convert_logo_transparency.py", "w") as f:
        f.write(converter_script)
    
    print("📝 Created: convert_logo_transparency.py")
    print("   Run this script if you have PIL/Pillow installed")

if __name__ == "__main__":
    check_logo_requirements()
    print("\n" + "="*50)
    create_pil_converter()