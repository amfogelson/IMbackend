from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import xml.etree.ElementTree as ET
import re
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import io

# Try to import cairosvg, but make it optional
try:
    import cairosvg
    CAIRO_AVAILABLE = True
except ImportError:
    CAIRO_AVAILABLE = False
    print("Warning: cairosvg not available. PNG export will be disabled.")

# --- Setup Directories ---
BASE_DIR = Path(__file__).parent.parent
ICON_DIR = BASE_DIR / "exported_svgs"
FLAG_DIR = BASE_DIR / "flags"  # New directory for flags
ICON_DIR.mkdir(exist_ok=True)
FLAG_DIR.mkdir(exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=ICON_DIR), name="static")
app.mount("/flags", StaticFiles(directory=FLAG_DIR), name="flags")
app.mount("/static-icons", StaticFiles(directory=ICON_DIR), name="static-icons")

# --- Pydantic Model ---
class UpdateColorRequest(BaseModel):
    icon_name: str
    group_id: str
    color: str
    type: str = "icon"  # "icon" or "flag"
    folder: str = "Root"  # folder name for icons

class ExportPngRequest(BaseModel):
    icon_name: str
    type: str = "icon"  # "icon" or "flag"
    folder: str = "Root"  # folder name for icons

# --- Utility functions ---
def update_element_color(element, new_color):
    # Case 1: direct 'fill' attribute
    if 'fill' in element.attrib:
        element.set('fill', new_color)

    # Case 2: inline 'style' attribute (style="fill:#xxxxxx;stroke:none")
    if 'style' in element.attrib:
        style = element.attrib['style']
        style = re.sub(r'fill\s*:\s*#[0-9a-fA-F]{3,6}', f'fill:{new_color}', style)
        element.set('style', style)

@app.get("/")
async def root():
    return {"message": "Icon Manager Backend is running!", "cairo_available": CAIRO_AVAILABLE}

@app.get("/icons")
async def get_icons():
    # Get all folders and files in the ICON_DIR
    folders = {}
    
    # Get folders
    for folder_path in ICON_DIR.iterdir():
        if folder_path.is_dir():
            folder_name = folder_path.name
            # Get all SVG files in this folder
            svg_files = [f.stem for f in folder_path.glob("*.svg")]
            if svg_files:  # Only include folders that have SVG files
                folders[folder_name] = svg_files
    
    # Get SVG files in the root directory (not in folders)
    root_svgs = [f.stem for f in ICON_DIR.glob("*.svg")]
    if root_svgs:
        folders["Root"] = root_svgs
    
    return {"folders": folders}

@app.get("/icons/{folder_name}")
async def get_icons_from_folder(folder_name: str):
    if folder_name == "Root":
        # Get icons from root directory
        icons = [f.stem for f in ICON_DIR.glob("*.svg")]
    else:
        # Get icons from specific folder
        folder_path = ICON_DIR / folder_name
        if not folder_path.exists() or not folder_path.is_dir():
            return {"error": "Folder not found"}
        
        icons = [f.stem for f in folder_path.glob("*.svg")]
    
    return {"icons": icons}

@app.get("/flags")
async def get_flags():
    flags = [f.name for f in FLAG_DIR.glob("*.svg")]
    return {"flags": flags}

@app.post("/export-png")
async def export_png(req: ExportPngRequest):
    if not CAIRO_AVAILABLE:
        return {"error": "PNG export not available. cairosvg is not installed."}
    
    if req.type == "icon":
        if req.folder == "Root":
            filepath = ICON_DIR / req.icon_name
        else:
            filepath = ICON_DIR / req.folder / req.icon_name
    elif req.type == "flag":
        filepath = FLAG_DIR / req.icon_name
    else:
        return {"error": "Invalid type"}
    
    if not filepath.exists():
        return {"error": "File not found"}

    try:
        # Read the SVG file
        with open(filepath, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Convert SVG to PNG
        png_data = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'))
        
        # Create filename for PNG
        png_filename = req.icon_name.replace('.svg', '.png')
        
        return StreamingResponse(
            io.BytesIO(png_data),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={png_filename}"}
        )
    except Exception as e:
        return {"error": f"Failed to convert to PNG: {str(e)}"}

@app.get("/groups/{type}/{folder_name}/{icon_name}")
async def get_groups(type: str, folder_name: str, icon_name: str):
    if type == "icon":
        if folder_name == "Root":
            filepath = ICON_DIR / icon_name
        else:
            filepath = ICON_DIR / folder_name / icon_name
    elif type == "flag":
        filepath = FLAG_DIR / icon_name
    else:
        return {"groups": []}
    
    if not filepath.exists():
        return {"groups": []}

    ET.register_namespace('', "http://www.w3.org/2000/svg")
    tree = ET.parse(filepath)
    root = tree.getroot()
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}

    groups = []
    for g in root.findall(".//svg:g", namespaces):
        group_id = g.get("id")
        if group_id:
            # Check if this group contains other groups with IDs (parent groups)
            has_child_groups_with_ids = False
            for child in g:
                if child.tag.endswith('g') and child.get("id"):
                    has_child_groups_with_ids = True
                    break
            
            # Only include groups that don't contain other groups with IDs
            # This excludes parent/container groups like "Layer_2"
            if not has_child_groups_with_ids:
                groups.append(group_id)
    
    return {"groups": groups}

@app.post("/update_color")
async def update_color(req: UpdateColorRequest):
    if req.type == "icon":
        if req.folder == "Root":
            filepath = ICON_DIR / req.icon_name
        else:
            filepath = ICON_DIR / req.folder / req.icon_name
    elif req.type == "flag":
        filepath = FLAG_DIR / req.icon_name
    else:
        return {"error": "Invalid type"}
    
    if not filepath.exists():
        return {"error": "File not found"}

    ET.register_namespace('', "http://www.w3.org/2000/svg")
    tree = ET.parse(filepath)
    root = tree.getroot()
    namespaces = {"svg": "http://www.w3.org/2000/svg"}
    
    if req.group_id == "entire_flag":
        # For flags, update all elements in the SVG
        for element in root.iter():
            update_element_color(element, req.color)
    else:
        # For icons, update specific group
        groups = []
        for g in root.findall(".//svg:g", namespaces):
            group_id = g.get("id")
            if group_id:
                groups.append(group_id)

        target_group = root.find(f".//svg:g[@id='{req.group_id}']", namespaces)
        if target_group is None:
            return {"error": "Group not found"}

        # Update all descendants inside the group
        for element in target_group.iter():
            update_element_color(element, req.color)

    # Only remove <style> blocks directly under root
    for style_block in list(root.findall("svg:style", namespaces)):
        root.remove(style_block)

    tree.write(filepath, encoding='utf-8', xml_declaration=True)
    return {"status": "Color updated"}

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get("PORT", 8000))
    
    print(f"Starting server on port {port}")
    print(f"Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'development')}")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        print(f"Failed to start server: {e}")
        raise

