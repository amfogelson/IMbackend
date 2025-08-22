#!/usr/bin/env python3
"""
Script to test if the backend URLs are working correctly
"""

import requests
import time

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
    backend_url = "http://localhost:8000"
    
    print("Testing Backend URLs")
    print("=" * 50)
    
    # Test regular icon URLs
    test_url(f"{backend_url}/static-icons-light/Military/Target.svg", "Light mode regular icon")
    test_url(f"{backend_url}/static-icons-dark/Military/Target.svg", "Dark mode regular icon")
    
    # Test single color URLs
    test_url(f"{backend_url}/single-color-files-light/4LeafClover.svg", "Light mode single color icon")
    test_url(f"{backend_url}/single-color-files-dark/4LeafClover.svg", "Dark mode single color icon")
    
    # Test colorful icon URLs (should still work)
    test_url(f"{backend_url}/colorful-icons/Business/3D Pie Chart.svg", "Colorful icon")
    
    print("\n" + "=" * 50)
    print("URL Testing Complete")

if __name__ == "__main__":
    # Give the backend a moment to start
    print("Waiting for backend to start...")
    time.sleep(3)
    main() 