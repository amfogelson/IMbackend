#!/usr/bin/env python3
"""
Script to debug static file serving issues
"""

from pathlib import Path

def main():
    """Debug static file paths"""
    print("Debugging Static File Paths")
    print("=" * 50)
    
    # Check base directory
    base_dir = Path(__file__).parent
    print(f"Base directory: {base_dir}")
    
    # Check icon directories
    icon_dir = base_dir / "exported_svgs"
    icon_dir_light = icon_dir / "light"
    icon_dir_dark = icon_dir / "dark"
    
    print(f"\nIcon directories:")
    print(f"  ICON_DIR: {icon_dir} (exists: {icon_dir.exists()})")
    print(f"  ICON_DIR_LIGHT: {icon_dir_light} (exists: {icon_dir_light.exists()})")
    print(f"  ICON_DIR_DARK: {icon_dir_dark} (exists: {icon_dir_dark.exists()})")
    
    # Check if Military folder exists in dark directory
    military_dir = icon_dir_dark / "Military"
    print(f"  Military directory: {military_dir} (exists: {military_dir.exists()})")
    
    # Check if Target.svg exists
    target_file = military_dir / "Target.svg"
    print(f"  Target.svg: {target_file} (exists: {target_file.exists()})")
    
    # List some files in the dark directory
    if icon_dir_dark.exists():
        print(f"\nFiles in dark directory:")
        for item in list(icon_dir_dark.iterdir())[:5]:  # Show first 5 items
            print(f"  {item.name} ({'dir' if item.is_dir() else 'file'})")
    
    # Check single color directories
    colorful_dir = base_dir / "colorful_icons"
    single_color_light = colorful_dir / "SingleColor" / "light"
    single_color_dark = colorful_dir / "SingleColor" / "dark"
    
    print(f"\nSingle color directories:")
    print(f"  SINGLE_COLOR_LIGHT: {single_color_light} (exists: {single_color_light.exists()})")
    print(f"  SINGLE_COLOR_DARK: {single_color_dark} (exists: {single_color_dark.exists()})")

if __name__ == "__main__":
    main() 