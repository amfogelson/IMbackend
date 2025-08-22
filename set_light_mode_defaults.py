#!/usr/bin/env python3
"""
Script to set all light mode SVGs to have Grey group and single color fills as #282828
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
import re

# Register the SVG namespace
ET.register_namespace('', "http://www.w3.org/2000/svg")

def update_element_color(element, color):
    """Update the color of an SVG element"""
    # Update fill attribute
    if element.get('fill') and element.get('fill') != 'none':
        element.set('fill', color)
    
    # Update style attribute
    style = element.get('style', '')
    if style:
        # Replace fill color in style
        style = re.sub(r'fill:\s*[^;]+;?', f'fill: {color};', style)
        # If no fill in style, add it
        if 'fill:' not in style:
            style += f'; fill: {color};'
        element.set('style', style)

def process_svg_file(filepath, target_color):
    """Process a single SVG file to update Grey group and single color fills"""
    try:
        print(f"Processing: {filepath}")
        
        # Parse the SVG
        tree = ET.parse(filepath)
        root = tree.getroot()
        namespaces = {"svg": "http://www.w3.org/2000/svg"}
        
        updated_count = 0
        
        # For single color icons, update all elements
        if "SingleColor" in str(filepath):
            print(f"  - Single color icon detected, updating all elements to {target_color}")
            for element in root.iter():
                if element.tag.endswith(('path', 'rect', 'circle', 'ellipse', 'polygon', 'polyline', 'line')):
                    old_fill = element.get('fill', 'N/A')
                    old_style = element.get('style', 'N/A')
                    update_element_color(element, target_color)
                    new_fill = element.get('fill', 'N/A')
                    new_style = element.get('style', 'N/A')
                    if old_fill != new_fill or old_style != new_style:
                        updated_count += 1
        else:
            # For regular icons, update Grey group
            print(f"  - Regular icon detected, updating Grey group to {target_color}")
            target_group = root.find(".//svg:g[@id='Grey']", namespaces)
            if target_group is not None:
                # Update all descendants inside the Grey group
                for element in target_group.iter():
                    if element.tag.endswith(('path', 'rect', 'circle', 'ellipse', 'polygon', 'polyline', 'line')):
                        old_fill = element.get('fill', 'N/A')
                        old_style = element.get('style', 'N/A')
                        update_element_color(element, target_color)
                        new_fill = element.get('fill', 'N/A')
                        new_style = element.get('style', 'N/A')
                        if old_fill != new_fill or old_style != new_style:
                            updated_count += 1
            else:
                print(f"  - No Grey group found in {filepath}")
        
        # Remove style blocks that might interfere
        for style_block in list(root.findall("svg:style", namespaces)):
            root.remove(style_block)
        
        # Write the file back
        tree.write(filepath, encoding='utf-8', xml_declaration=True)
        print(f"  - Updated {updated_count} elements")
        
        return updated_count > 0
        
    except Exception as e:
        print(f"  - Error processing {filepath}: {e}")
        return False

def main():
    """Main function to process all light mode SVGs"""
    base_dir = Path(__file__).parent
    
    # Light mode directories
    light_dirs = [
        base_dir / "exported_svgs" / "light",
        base_dir / "colorful_icons" / "SingleColor" / "light"
    ]
    
    target_color = "#282828"  # Dark grey for light mode
    total_files = 0
    updated_files = 0
    
    print(f"Setting light mode defaults to {target_color}")
    print("=" * 50)
    
    for light_dir in light_dirs:
        if not light_dir.exists():
            print(f"Directory not found: {light_dir}")
            continue
            
        print(f"\nProcessing directory: {light_dir}")
        
        # Process all SVG files in the directory
        for svg_file in light_dir.rglob("*.svg"):
            total_files += 1
            if process_svg_file(svg_file, target_color):
                updated_files += 1
    
    print("\n" + "=" * 50)
    print(f"Summary:")
    print(f"  Total files processed: {total_files}")
    print(f"  Files updated: {updated_files}")
    print(f"  Target color: {target_color}")
    print("Light mode defaults set successfully!")

if __name__ == "__main__":
    main() 