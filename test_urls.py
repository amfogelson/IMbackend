#!/usr/bin/env python3
"""
Script to test if the backend URLs are working correctly
"""

import requests
import sys
from pathlib import Path

def test_url(url, description):
    """Test if a URL is accessible"""
    try:
        print(f"Testing {description}: {url}")
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"  ✅ SUCCESS: {response.status_code}")
            return True
        else:
            print(f"  ❌ FAILED: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False

def main():
    """Test various backend URLs"""
    # You can change this to your actual backend URL
    backend_url = "http://localhost:8000"
    
    print("Testing Backend URLs")
    print("=" * 50)
    
    # Test regular icon URLs
    test_url(f"{backend_url}/static-icons-light/Business/3D Pie Chart.svg", "Light mode regular icon")
    test_url(f"{backend_url}/static-icons-dark/Business/3D Pie Chart.svg", "Dark mode regular icon")
    
    # Test single color URLs
    test_url(f"{backend_url}/single-color-files-light/4LeafClover.svg", "Light mode single color icon")
    test_url(f"{backend_url}/single-color-files-dark/4LeafClover.svg", "Dark mode single color icon")
    
    # Test colorful icon URLs (should still work)
    test_url(f"{backend_url}/colorful-icons/Business/3D Pie Chart.svg", "Colorful icon")
    
    print("\n" + "=" * 50)
    print("URL Testing Complete")
    
    # Also check if files exist locally
    print("\nChecking Local Files:")
    print("=" * 50)
    
    base_dir = Path(__file__).parent
    
    # Check light mode files
    light_icon = base_dir / "exported_svgs" / "light" / "Business" / "3D Pie Chart.svg"
    dark_icon = base_dir / "exported_svgs" / "dark" / "Business" / "3D Pie Chart.svg"
    light_single = base_dir / "colorful_icons" / "SingleColor" / "light" / "4LeafClover.svg"
    dark_single = base_dir / "colorful_icons" / "SingleColor" / "dark" / "4LeafClover.svg"
    
    print(f"Light mode icon exists: {light_icon.exists()}")
    print(f"Dark mode icon exists: {dark_icon.exists()}")
    print(f"Light mode single color exists: {light_single.exists()}")
    print(f"Dark mode single color exists: {dark_single.exists()}")

if __name__ == "__main__":
    main() 