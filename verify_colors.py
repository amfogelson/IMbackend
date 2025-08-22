#!/usr/bin/env python3
"""
Script to verify the colors in light and dark mode SVG files
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re

# Register the SVG namespace
ET.register_namespace('', "http://www.w3.org/2000/svg")

def analyze_svg_colors(filepath):
    """Analyze the colors in an SVG file"""
    try:
        print(f"\nAnalyzing: {filepath.name}")
        
        # Parse the SVG
        tree = ET.parse(filepath)
        root = tree.getroot()
        namespaces = {"svg": "http://www.w3.org/2000/svg"}
        
        colors_found = set()
        grey_group_colors = set()
        
        # Check if it's a single color icon
        if "SingleColor" in str(filepath):
            print(f"  - Single color icon detected")
            for element in root.iter():
                if element.tag.endswith(('path', 'rect', 'circle', 'ellipse', 'polygon', 'polyline', 'line')):
                    fill_color = element.get('fill', 'none')
                    if fill_color != 'none':
                        colors_found.add(fill_color)
                        print(f"    Found fill color: {fill_color}")
        else:
            # Check for Grey group
            target_group = root.find(".//svg:g[@id='Grey']", namespaces)
            if target_group is not None:
                print(f"  - Grey group found")
                for element in target_group.iter():
                    if element.tag.endswith(('path', 'rect', 'circle', 'ellipse', 'polygon', 'polyline', 'line')):
                        fill_color = element.get('fill', 'none')
                        if fill_color != 'none':
                            grey_group_colors.add(fill_color)
                            print(f"    Grey group fill color: {fill_color}")
            else:
                print(f"  - No Grey group found")
        
        return colors_found, grey_group_colors
        
    except Exception as e:
        print(f"  - Error analyzing {filepath}: {e}")
        return set(), set()

def main():
    """Main function to verify colors in light and dark mode SVGs"""
    base_dir = Path(__file__).parent
    
    # Directories to check
    light_dirs = [
        base_dir / "exported_svgs" / "light",
        base_dir / "colorful_icons" / "SingleColor" / "light"
    ]
    
    dark_dirs = [
        base_dir / "exported_svgs" / "dark",
        base_dir / "colorful_icons" / "SingleColor" / "dark"
    ]
    
    print("=" * 60)
    print("VERIFYING LIGHT MODE COLORS")
    print("=" * 60)
    
    light_colors = set()
    light_grey_colors = set()
    
    for light_dir in light_dirs:
        if not light_dir.exists():
            print(f"Directory not found: {light_dir}")
            continue
            
        print(f"\nChecking directory: {light_dir}")
        
        # Check first few files in each directory
        svg_files = list(light_dir.rglob("*.svg"))[:5]  # Check first 5 files
        for svg_file in svg_files:
            colors, grey_colors = analyze_svg_colors(svg_file)
            light_colors.update(colors)
            light_grey_colors.update(grey_colors)
    
    print("\n" + "=" * 60)
    print("VERIFYING DARK MODE COLORS")
    print("=" * 60)
    
    dark_colors = set()
    dark_grey_colors = set()
    
    for dark_dir in dark_dirs:
        if not dark_dir.exists():
            print(f"Directory not found: {dark_dir}")
            continue
            
        print(f"\nChecking directory: {dark_dir}")
        
        # Check first few files in each directory
        svg_files = list(dark_dir.rglob("*.svg"))[:5]  # Check first 5 files
        for svg_file in svg_files:
            colors, grey_colors = analyze_svg_colors(svg_file)
            dark_colors.update(colors)
            dark_grey_colors.update(grey_colors)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Light mode single color fills: {light_colors}")
    print(f"Light mode Grey group fills: {light_grey_colors}")
    print(f"Dark mode single color fills: {dark_colors}")
    print(f"Dark mode Grey group fills: {dark_grey_colors}")
    
    # Check if colors are correct
    expected_light = {"#282828"}
    expected_dark = {"#D3D3D3"}
    
    print(f"\nExpected light mode: {expected_light}")
    print(f"Expected dark mode: {expected_dark}")
    
    if light_colors == expected_light and dark_colors == expected_dark:
        print("✅ Colors are correct!")
    else:
        print("❌ Colors need to be updated")

if __name__ == "__main__":
    main() 