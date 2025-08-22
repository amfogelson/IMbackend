#!/usr/bin/env python3
"""
Script to copy BCORE files from frontend to backend for deployment
"""
import shutil
import os
from pathlib import Path

def copy_bcore_files():
    """Copy BCORE files and infographics from frontend to backend"""
    
    # Define paths
    frontend_bcore_dir = Path(__file__).parent.parent / "frontend" / "public" / "Bcore_Images_Video"
    backend_bcore_dir = Path(__file__).parent / "backend" / "bcore_files"
    
    infographics_source_dir = Path(__file__).parent / "infographics"
    infographics_dest_dir = Path(__file__).parent / "backend" / "infographics"
    
    print(f"Copying BCORE files from: {frontend_bcore_dir}")
    print(f"To: {backend_bcore_dir}")
    
    print(f"Copying infographics from: {infographics_source_dir}")
    print(f"To: {infographics_dest_dir}")
    
    # Check if source directories exist
    if not frontend_bcore_dir.exists():
        print(f"Error: BCORE source directory does not exist: {frontend_bcore_dir}")
        return False
    
    if not infographics_source_dir.exists():
        print(f"Error: Infographics source directory does not exist: {infographics_source_dir}")
        return False
    
    # Create destination directories
    backend_bcore_dir.mkdir(parents=True, exist_ok=True)
    infographics_dest_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Copy BCORE files
        if backend_bcore_dir.exists():
            shutil.rmtree(backend_bcore_dir)
        shutil.copytree(frontend_bcore_dir, backend_bcore_dir)
        
        print("✅ BCORE files copied successfully!")
        print(f"Files copied to: {backend_bcore_dir}")
        
        # List copied BCORE files
        for root, dirs, files in os.walk(backend_bcore_dir):
            for file in files:
                rel_path = Path(root) / file
                print(f"  - {rel_path.relative_to(backend_bcore_dir)}")
        
        # Copy infographics
        if infographics_dest_dir.exists():
            shutil.rmtree(infographics_dest_dir)
        shutil.copytree(infographics_source_dir, infographics_dest_dir)
        
        print("✅ Infographics copied successfully!")
        print(f"Files copied to: {infographics_dest_dir}")
        
        # List copied infographics files
        for root, dirs, files in os.walk(infographics_dest_dir):
            for file in files:
                rel_path = Path(root) / file
                print(f"  - {rel_path.relative_to(infographics_dest_dir)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error copying files: {e}")
        return False

if __name__ == "__main__":
    copy_bcore_files()
