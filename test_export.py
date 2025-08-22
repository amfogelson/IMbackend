#!/usr/bin/env python3
"""
Test script to verify export functionality reads from correct directories
"""

import requests
import json

def test_export_endpoints():
    """Test the export endpoints to see if they read from correct directories"""
    base_url = "http://localhost:8000"
    
    print("Testing Export Endpoints")
    print("=" * 50)
    
    # Test data for different scenarios
    test_cases = [
        {
            "name": "Regular Icon - Light Mode",
            "endpoint": "/download-svg",
            "data": {
                "icon_name": "3D Pie Chart.svg",
                "type": "icon",
                "folder": "Business",
                "mode": "light"
            }
        },
        {
            "name": "Regular Icon - Dark Mode", 
            "endpoint": "/download-svg",
            "data": {
                "icon_name": "3D Pie Chart.svg",
                "type": "icon",
                "folder": "Business",
                "mode": "dark"
            }
        },
        {
            "name": "Single Color Icon - Light Mode",
            "endpoint": "/download-svg", 
            "data": {
                "icon_name": "4LeafClover.svg",
                "type": "icon",
                "folder": "SingleColor",
                "mode": "light"
            }
        },
        {
            "name": "Single Color Icon - Dark Mode",
            "endpoint": "/download-svg",
            "data": {
                "icon_name": "4LeafClover.svg", 
                "type": "icon",
                "folder": "SingleColor",
                "mode": "dark"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print(f"Endpoint: {test_case['endpoint']}")
        print(f"Data: {json.dumps(test_case['data'], indent=2)}")
        
        try:
            response = requests.post(f"{base_url}{test_case['endpoint']}", json=test_case['data'])
            
            if response.status_code == 200:
                print("✅ SUCCESS: Got response")
                
                # Check if it's an SVG response
                if 'svg+xml' in response.headers.get('content-type', ''):
                    svg_content = response.text
                    print(f"📄 SVG Content Length: {len(svg_content)} characters")
                    
                    # Check for color information
                    if '#282828' in svg_content:
                        print("🔍 Found #282828 color in SVG")
                    if '#00ABF6' in svg_content:
                        print("🔍 Found #00ABF6 color in SVG")
                    if '#D3D3D3' in svg_content:
                        print("🔍 Found #D3D3D3 color in SVG")
                        
                    # Show first few lines
                    lines = svg_content.split('\n')[:5]
                    print("📝 First few lines:")
                    for line in lines:
                        print(f"   {line}")
                else:
                    print("⚠️  Response is not SVG content")
                    print(f"Content-Type: {response.headers.get('content-type')}")
            else:
                print(f"❌ ERROR: Status {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
    
    print("\n" + "=" * 50)
    print("Export Testing Complete")

if __name__ == "__main__":
    test_export_endpoints()
