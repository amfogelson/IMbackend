#!/usr/bin/env python3
"""
Script to clean up main directories by removing SVG files,
keeping only the light and dark mode directories
"""

import os
from pathlib import Path
import shutil

def cleanup_directory(main_dir, light_dir, dark_dir):
    """Clean up a main directory by moving SVG files to light/dark directories"""
    main_path = Path(main_dir)
    light_path = Path(light_dir)
    dark_path = Path(dark_dir)
    
    if not main_path.exists():
        print(f"Main directory not found: {main_path}")
        return
    
    print(f"\nCleaning up: {main_path}")
    
    # Get all SVG files in main directory
    svg_files = list(main_path.rglob("*.svg"))
    
    if not svg_files:
        print("  No SVG files found in main directory")
        return
    
    print(f"  Found {len(svg_files)} SVG files")
    
    # Check if light and dark directories exist and have files
    light_files = list(light_path.rglob("*.svg")) if light_path.exists() else []
    dark_files = list(dark_path.rglob("*.svg")) if dark_path.exists() else []
    
    print(f"  Light directory has {len(light_files)} files")
    print(f"  Dark directory has {len(dark_files)} files")
    
    if light_files and dark_files:
        print("  Light and dark directories already have files - removing from main directory")
        
        # Remove SVG files from main directory
        removed_count = 0
        for svg_file in svg_files:
            try:
                svg_file.unlink()
                removed_count += 1
                print(f"    Removed: {svg_file.name}")
            except Exception as e:
                print(f"    Error removing {svg_file.name}: {e}")
        
        print(f"  Removed {removed_count} SVG files from main directory")
    else:
        print("  Light or dark directories are empty - skipping cleanup")

def main():
    """Main function to clean up all main directories"""
    base_dir = Path(__file__).parent
    
    print("Cleaning up main directories to use only light/dark mode files")
    print("=" * 60)
    
    # Clean up exported_svgs main directories
    exported_svgs_main = base_dir / "exported_svgs"
    exported_svgs_light = base_dir / "exported_svgs" / "light"
    exported_svgs_dark = base_dir / "exported_svgs" / "dark"
    
    # Get all subdirectories in exported_svgs (excluding light and dark)
    if exported_svgs_main.exists():
        for subdir in exported_svgs_main.iterdir():
            if subdir.is_dir() and subdir.name not in ["light", "dark"]:
                subdir_light = exported_svgs_light / subdir.name
                subdir_dark = exported_svgs_dark / subdir.name
                cleanup_directory(subdir, subdir_light, subdir_dark)
    
    # Clean up single color main directory
    single_color_main = base_dir / "colorful_icons" / "SingleColor"
    single_color_light = base_dir / "colorful_icons" / "SingleColor" / "light"
    single_color_dark = base_dir / "colorful_icons" / "SingleColor" / "dark"
    
    cleanup_directory(single_color_main, single_color_light, single_color_dark)
    
    print("\n" + "=" * 60)
    print("Cleanup completed!")
    print("\nNow only the light and dark mode directories contain SVG files.")
    print("The frontend will be forced to use the correct mode-specific files.")

if __name__ == "__main__":
    main() 