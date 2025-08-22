#!/usr/bin/env python3
"""
Script to copy BCORE files from frontend to backend for deployment
"""
import shutil
import os
from pathlib import Path

def copy_bcore_files():
    """Copy BCORE files from frontend to backend"""
    
    # Define paths
    frontend_bcore_dir = Path(__file__).parent.parent / "frontend" / "public" / "Bcore_Images_Video"
    backend_bcore_dir = Path(__file__).parent / "backend" / "bcore_files"
    
    print(f"Copying BCORE files from: {frontend_bcore_dir}")
    print(f"To: {backend_bcore_dir}")
    
    # Check if source directory exists
    if not frontend_bcore_dir.exists():
        print(f"Error: Source directory does not exist: {frontend_bcore_dir}")
        return False
    
    # Create destination directory
    backend_bcore_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Copy the entire directory
        if backend_bcore_dir.exists():
            shutil.rmtree(backend_bcore_dir)
        shutil.copytree(frontend_bcore_dir, backend_bcore_dir)
        
        print("✅ BCORE files copied successfully!")
        print(f"Files copied to: {backend_bcore_dir}")
        
        # List copied files
        for root, dirs, files in os.walk(backend_bcore_dir):
            for file in files:
                rel_path = Path(root) / file
                print(f"  - {rel_path.relative_to(backend_bcore_dir)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error copying BCORE files: {e}")
        return False

if __name__ == "__main__":
    copy_bcore_files()
