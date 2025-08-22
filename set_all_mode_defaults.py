#!/usr/bin/env python3
"""
Combined script to set all light and dark mode SVG defaults
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run both light and dark mode scripts"""
    base_dir = Path(__file__).parent
    
    print("Setting all mode defaults for SVG files")
    print("=" * 60)
    
    # Run light mode script
    print("\n1. Setting LIGHT mode defaults (#282828)...")
    print("-" * 40)
    try:
        result = subprocess.run([sys.executable, base_dir / "set_light_mode_defaults.py"], 
                              capture_output=True, text=True, cwd=base_dir)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except Exception as e:
        print(f"Error running light mode script: {e}")
    
    # Run dark mode script
    print("\n2. Setting DARK mode defaults (#D3D3D3)...")
    print("-" * 40)
    try:
        result = subprocess.run([sys.executable, base_dir / "set_dark_mode_defaults.py"], 
                              capture_output=True, text=True, cwd=base_dir)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except Exception as e:
        print(f"Error running dark mode script: {e}")
    
    print("\n" + "=" * 60)
    print("All mode defaults have been set!")
    print("\nSummary:")
    print("  ✅ Light mode: Grey group and single color fills set to #282828")
    print("  ✅ Dark mode: Grey group and single color fills set to #D3D3D3")
    print("\nYour SVG files are now ready for light/dark mode switching!")

if __name__ == "__main__":
    main() 