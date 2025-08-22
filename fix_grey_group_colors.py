#!/usr/bin/env python3
"""
Script to fix Grey group colors that weren't updated properly
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re

# Register the SVG namespace
ET.register_namespace('', "http://www.w3.org/2000/svg")

def fix_grey_group_colors(filepath, target_color):
    """Fix Grey group colors in an SVG file"""
    try:
        print(f"Processing: {filepath.name}")
        
        # Parse the SVG
        tree = ET.parse(filepath)
        root = tree.getroot()
        namespaces = {"svg": "http://www.w3.org/2000/svg"}
        
        updated_count = 0
        
        # Find Grey group
        target_group = root.find(".//svg:g[@id='Grey']", namespaces)
        if target_group is not None:
            print(f"  - Found Grey group, updating to {target_color}")
            
            # Update the group's fill attribute
            current_fill = target_group.get('fill')
            if current_fill != target_color:
                target_group.set('fill', target_color)
                updated_count += 1
                print(f"    Updated group fill: {current_fill} -> {target_color}")
            
            # Update all descendants inside the group
            for element in target_group.iter():
                if element.tag.endswith(('path', 'rect', 'circle', 'ellipse', 'polygon', 'polyline', 'line')):
                    current_fill = element.get('fill', 'none')
                    if current_fill != 'none' and current_fill != target_color:
                        element.set('fill', target_color)
                        updated_count += 1
                        print(f"    Updated element fill: {current_fill} -> {target_color}")
        else:
            print(f"  - No Grey group found")
            return 0
        
        # Write the file back
        tree.write(filepath, encoding='utf-8', xml_declaration=True)
        print(f"  - Updated {updated_count} elements")
        
        return updated_count
        
    except Exception as e:
        print(f"  - Error processing {filepath}: {e}")
        return 0

def main():
    """Main function to fix Grey group colors"""
    base_dir = Path(__file__).parent
    
    # Light mode directories
    light_dirs = [
        base_dir / "exported_svgs" / "light"
    ]
    
    # Dark mode directories
    dark_dirs = [
        base_dir / "exported_svgs" / "dark"
    ]
    
    light_color = "#282828"
    dark_color = "#D3D3D3"
    
    total_light_updated = 0
    total_dark_updated = 0
    
    print("=" * 60)
    print("FIXING LIGHT MODE GREY GROUP COLORS")
    print("=" * 60)
    
    for light_dir in light_dirs:
        if not light_dir.exists():
            print(f"Directory not found: {light_dir}")
            continue
            
        print(f"\nProcessing directory: {light_dir}")
        
        # Process all SVG files in the directory
        for svg_file in light_dir.rglob("*.svg"):
            updated = fix_grey_group_colors(svg_file, light_color)
            if updated > 0:
                total_light_updated += 1
    
    print("\n" + "=" * 60)
    print("FIXING DARK MODE GREY GROUP COLORS")
    print("=" * 60)
    
    for dark_dir in dark_dirs:
        if not dark_dir.exists():
            print(f"Directory not found: {dark_dir}")
            continue
            
        print(f"\nProcessing directory: {dark_dir}")
        
        # Process all SVG files in the directory
        for svg_file in dark_dir.rglob("*.svg"):
            updated = fix_grey_group_colors(svg_file, dark_color)
            if updated > 0:
                total_dark_updated += 1
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Light mode files updated: {total_light_updated}")
    print(f"Dark mode files updated: {total_dark_updated}")
    print("Grey group colors have been fixed!")

if __name__ == "__main__":
    main() 