from fastapi import FastAPI, APIRouter, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import xml.etree.ElementTree as ET
import re
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import io
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import zipfile
from dotenv import load_dotenv
from pptx import Presentation
from pptx.util import Inches
from pptx.enum.shapes import MSO_SHAPE_TYPE
import tempfile
import shutil
from copy import deepcopy

# Load environment variables
load_dotenv()

print("DEBUG: Backend main.py loaded with updated code!")

# --- Email Configuration ---
EMAIL_ENABLED = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_FROM = os.getenv('EMAIL_FROM', '')
EMAIL_TO = os.getenv('EMAIL_TO', '')

def send_feedback_notification(feedback_type, feedback_message, feedback_id):
    """Send email notification for new feedback submission"""
    if not EMAIL_ENABLED or not all([EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_FROM, EMAIL_TO]):
        print("Email notifications disabled or configuration incomplete")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Subject'] = f"New Feedback Submission - {feedback_type} (ID: {feedback_id})"
        
        # Create email body
        body = f"""
New feedback has been submitted to the Icon Manager application.

Feedback Details:
- ID: {feedback_id}
- Type: {feedback_type}
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Message: {feedback_message}

You can view and manage this feedback through the admin interface.

Best regards,
Icon Manager System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, EMAIL_TO, text)
        server.quit()
        
        print(f"Email notification sent for feedback ID {feedback_id}")
        return True
        
    except Exception as e:
        print(f"Error sending email notification: {e}")
        return False

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
COLORFUL_ICON_DIR = BASE_DIR / "colorful_icons"  # New directory for colorful icons
FLAG_DIR = BASE_DIR / "flags"  # New directory for flags
ICON_DIR.mkdir(exist_ok=True)
COLORFUL_ICON_DIR.mkdir(exist_ok=True)
FLAG_DIR.mkdir(exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=ICON_DIR), name="static")
app.mount("/colorful-icons", StaticFiles(directory=COLORFUL_ICON_DIR), name="colorful-icons")
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

class GreyscaleRequest(BaseModel):
    icon_name: str
    folder: str = "Root"  # folder name for colorful icons

class RevertRequest(BaseModel):
    icon_name: str
    folder: str = "Root"  # folder name for colorful icons

class ZipExportRequest(BaseModel):
    items: list[str]  # List of icon names
    type: str = "icon"  # "icon", "colorful-icon", or "flag"
    folder: str = "Root"  # folder name for icons
    format: str = "svg"  # "svg" or "png"

class FeedbackRequest(BaseModel):
    type: str
    message: str

# --- Feedback Storage ---
FEEDBACK_DIR = BASE_DIR / "feedback_submissions"
FEEDBACK_DIR.mkdir(exist_ok=True)

def load_feedback():
    """Load feedback from individual files"""
    feedback_list = []
    
    if FEEDBACK_DIR.exists():
        for file_path in FEEDBACK_DIR.glob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) >= 4:
                        feedback = {
                            "id": int(file_path.stem),  # filename without extension
                            "timestamp": lines[0].strip(),
                            "type": lines[1].strip(),
                            "status": lines[2].strip(),
                            "message": "".join(lines[3:]).strip()  # rest of the file
                        }
                        feedback_list.append(feedback)
            except Exception as e:
                print(f"Error reading feedback file {file_path}: {e}")
    
    return feedback_list

def save_feedback(feedback_type, feedback_message):
    """Save a new feedback submission as a file"""
    try:
        # Get the next available ID
        existing_files = list(FEEDBACK_DIR.glob("*.txt"))
        next_id = 1
        if existing_files:
            existing_ids = [int(f.stem) for f in existing_files if f.stem.isdigit()]
            if existing_ids:
                next_id = max(existing_ids) + 1
        
        # Create the feedback file
        file_path = FEEDBACK_DIR / f"{next_id}.txt"
        timestamp = datetime.now().isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"{timestamp}\n")
            f.write(f"{feedback_type}\n")
            f.write("new\n")  # default status
            f.write(f"{feedback_message}\n")
        
        return next_id
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return None

def update_feedback_status_file(feedback_id, new_status):
    """Update the status of a feedback submission"""
    try:
        file_path = FEEDBACK_DIR / f"{feedback_id}.txt"
        if not file_path.exists():
            return False
        
        # Read the current file
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) >= 3:
            # Update the status line (3rd line)
            lines[2] = f"{new_status}\n"
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
        return False
    except Exception as e:
        print(f"Error updating feedback status: {e}")
        return False

# --- Utility functions ---
def update_element_color(element, new_color):
    """Update the color of an SVG element"""
    print(f"DEBUG: update_element_color called on {element.tag} with color {new_color}")
    
    # Case 1: direct 'fill' attribute
    if 'fill' in element.attrib:
        old_fill = element.get('fill')
        element.set('fill', new_color)
        print(f"DEBUG: Updated fill attribute: {old_fill} -> {new_color}")

    # Case 2: inline 'style' attribute (style="fill:#xxxxxx;stroke:none")
    if 'style' in element.attrib:
        style = element.attrib['style']
        old_style = style
        # Replace fill color in style attribute
        style = re.sub(r'fill\s*:\s*#[0-9a-fA-F]{3,6}', f'fill:{new_color}', style)
        # If no fill color was found, add it
        if 'fill:' not in style:
            style += f';fill:{new_color}'
        element.set('style', style)
        print(f"DEBUG: Updated style attribute: {old_style} -> {style}")

    # Case 3: If no fill attribute or style, add fill attribute
    if 'fill' not in element.attrib and 'style' not in element.attrib:
        element.set('fill', new_color)
        print(f"DEBUG: Added fill attribute: {new_color}")

def convert_to_greyscale(element):
    """Convert an SVG element to greyscale by applying a filter"""
    # Add a greyscale filter to the element
    element.set('filter', 'url(#greyscale)')
    
    # If the element has a style attribute, add the filter there too
    if 'style' in element.attrib:
        style = element.attrib['style']
        if 'filter:' not in style:
            style += ';filter:url(#greyscale)'
            element.set('style', style)

def create_backup(filepath):
    """Create a backup of the original SVG file"""
    backup_path = filepath.with_suffix('.svg.backup')
    if not backup_path.exists():
        import shutil
        shutil.copy2(filepath, backup_path)
    return backup_path

def restore_from_backup(filepath):
    """Restore the original SVG from backup"""
    backup_path = filepath.with_suffix('.svg.backup')
    if backup_path.exists():
        import shutil
        shutil.copy2(backup_path, filepath)
        return True
    return False

@app.get("/")
async def root():
    return {"message": "Icon Manager Backend is running!", "cairo_available": CAIRO_AVAILABLE}

@app.get("/test")
async def test():
    return {"message": "Test endpoint working!", "debug": "Backend is responding"}

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
    
    # Sort folders by icon count (descending), then alphabetically for same count
    sorted_folders = dict(sorted(folders.items(), key=lambda x: (-len(x[1]), x[0])))
    
    return {"folders": sorted_folders}

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
    
    # Sort icons alphabetically
    icons.sort()
    
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

@app.post("/export-zip")
async def export_zip(req: ZipExportRequest):
    """Export multiple icons as a ZIP file"""
    try:
        # Create a ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for item_name in req.items:
                try:
                    # Determine the source file path
                    if req.type == "icon":
                        if req.folder == "Root":
                            source_path = ICON_DIR / f"{item_name}.svg"
                        else:
                            source_path = ICON_DIR / req.folder / f"{item_name}.svg"
                    elif req.type == "colorful-icon":
                        if req.folder == "Root":
                            source_path = COLORFUL_ICON_DIR / f"{item_name}.svg"
                        else:
                            source_path = COLORFUL_ICON_DIR / req.folder / f"{item_name}.svg"
                    else:  # flag
                        source_path = FLAG_DIR / f"{item_name}.svg"
                    
                    if not source_path.exists():
                        continue
                    
                    # Determine the filename in the ZIP
                    if req.format == "png":
                        # Convert SVG to PNG
                        if CAIRO_AVAILABLE:
                            png_data = cairosvg.svg2png(bytestring=source_path.read_text(encoding='utf-8').encode('utf-8'))
                            zip_file.writestr(f"{item_name}.png", png_data)
                        else:
                            # Fallback to SVG if PNG conversion not available
                            with open(source_path, 'rb') as f:
                                zip_file.writestr(f"{item_name}.svg", f.read())
                    else:
                        # Export as SVG
                        with open(source_path, 'rb') as f:
                            zip_file.writestr(f"{item_name}.svg", f.read())
                            
                except Exception as e:
                    print(f"Error processing {item_name}: {e}")
                    continue
        
        # Prepare the response
        zip_buffer.seek(0)
        
        # Create a meaningful filename
        folder_name = req.folder if req.folder != "Root" else "icons"
        zip_filename = f"{folder_name}_{req.type}_{req.format}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )
        
    except Exception as e:
        return {"error": f"Failed to create ZIP: {str(e)}"}

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

@app.get("/svg/{type}/{folder_name}/{icon_name}")
async def get_svg_with_cors(type: str, folder_name: str, icon_name: str):
    """Serve SVG files with proper CORS headers for frontend fetch requests"""
    try:
        if type == "icon":
            # Construct the file path
            if folder_name == "Root":
                file_path = ICON_DIR / icon_name
            else:
                file_path = ICON_DIR / folder_name / icon_name
        elif type == "colorful-icon":
            # For colorful icons
            if folder_name == "Root":
                file_path = COLORFUL_ICON_DIR / icon_name
            else:
                file_path = COLORFUL_ICON_DIR / folder_name / icon_name
        else:
            # For flags
            file_path = FLAG_DIR / icon_name
        
        if not file_path.exists():
            return {"error": "File not found"}
        
        # Read the SVG content
        with open(file_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Return with proper headers
        from fastapi.responses import Response
        return Response(
            content=svg_content,
            media_type="image/svg+xml",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        print(f"Error serving SVG: {e}")
        return {"error": "Failed to serve SVG"}

@app.post("/update_color")
async def update_color(req: UpdateColorRequest):
    try:
        print(f"DEBUG: update_color called with {req}", flush=True)
        print("DEBUG: Starting function execution...", flush=True)
        
        if req.type == "icon" or req.type == "icons":
            print("DEBUG: Type is icon", flush=True)
            if req.folder == "Root":
                filepath = ICON_DIR / req.icon_name
            else:
                filepath = ICON_DIR / req.folder / req.icon_name
        elif req.type == "flag":
            print("DEBUG: Type is flag", flush=True)
            filepath = FLAG_DIR / req.icon_name
        else:
            print("DEBUG: Invalid type", flush=True)
            return {"error": "Invalid type"}
        
        print(f"DEBUG: Filepath: {filepath}", flush=True)
        
        if not filepath.exists():
            print(f"DEBUG: File not found: {filepath}", flush=True)
            return {"error": "File not found"}

        print(f"DEBUG: File exists, parsing SVG...", flush=True)
        ET.register_namespace('', "http://www.w3.org/2000/svg")
        tree = ET.parse(filepath)
        root = tree.getroot()
        namespaces = {"svg": "http://www.w3.org/2000/svg"}
        
        if req.group_id == "entire_flag":
            # For flags, update all elements in the SVG
            print(f"DEBUG: Updating entire flag with color {req.color}", flush=True)
            for element in root.iter():
                update_element_color(element, req.color)
        else:
            # For icons, update specific group
            print(f"DEBUG: Looking for group '{req.group_id}' in icon", flush=True)
            groups = []
            for g in root.findall(".//svg:g", namespaces):
                group_id = g.get("id")
                if group_id:
                    groups.append(group_id)

            print(f"DEBUG: Found groups: {groups}", flush=True)

            target_group = root.find(f".//svg:g[@id='{req.group_id}']", namespaces)
            if target_group is None:
                print(f"DEBUG: Group '{req.group_id}' not found!", flush=True)
                return {"error": "Group not found"}

            print(f"DEBUG: Found target group '{req.group_id}', updating with color {req.color}", flush=True)
            
            # Update all descendants inside the group
            updated_count = 0
            for element in target_group.iter():
                if element.tag.endswith(('path', 'rect', 'circle', 'ellipse', 'polygon', 'polyline', 'line')):
                    old_fill = element.get('fill', 'N/A')
                    old_style = element.get('style', 'N/A')
                    update_element_color(element, req.color)
                    new_fill = element.get('fill', 'N/A')
                    new_style = element.get('style', 'N/A')
                    if old_fill != new_fill or old_style != new_style:
                        updated_count += 1
                        print(f"DEBUG: Updated element {element.tag} - fill: {old_fill} -> {new_fill}, style: {old_style} -> {new_style}", flush=True)
            
            print(f"DEBUG: Updated {updated_count} elements in group '{req.group_id}'", flush=True)

        # Only remove <style> blocks directly under root
        for style_block in list(root.findall("svg:style", namespaces)):
            root.remove(style_block)

        # Write the file back
        print(f"DEBUG: Writing file back to {filepath}", flush=True)
        tree.write(filepath, encoding='utf-8', xml_declaration=True)
        print(f"DEBUG: File written successfully", flush=True)
        
        return {"status": "Color updated"}
    except Exception as e:
        print(f"DEBUG: Exception in update_color: {e}", flush=True)
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}", flush=True)
        return {"error": f"Internal server error: {str(e)}"}

@app.get("/colorful-icons")
async def get_colorful_icons():
    # Get all folders and files in the COLORFUL_ICON_DIR
    folders = {}
    
    # Get folders
    for folder_path in COLORFUL_ICON_DIR.iterdir():
        if folder_path.is_dir():
            folder_name = folder_path.name
            # Get all SVG files in this folder
            svg_files = [f.stem for f in folder_path.glob("*.svg")]
            if svg_files:  # Only include folders that have SVG files
                folders[folder_name] = svg_files
    
    # Get SVG files in the root directory (not in folders)
    root_svgs = [f.stem for f in COLORFUL_ICON_DIR.glob("*.svg")]
    if root_svgs:
        folders["Root"] = root_svgs
    
    # Sort folders by icon count (descending), then alphabetically for same count
    sorted_folders = dict(sorted(folders.items(), key=lambda x: (-len(x[1]), x[0])))
    
    return {"folders": sorted_folders}

@app.post("/greyscale")
async def convert_to_greyscale_endpoint(req: GreyscaleRequest):
    if req.folder == "Root":
        filepath = COLORFUL_ICON_DIR / f"{req.icon_name}.svg"
    else:
        filepath = COLORFUL_ICON_DIR / req.folder / f"{req.icon_name}.svg"
    
    if not filepath.exists():
        return {"error": "File not found"}

    try:
        # Create backup of original file before converting
        create_backup(filepath)
        
        ET.register_namespace('', "http://www.w3.org/2000/svg")
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Add greyscale filter definition if it doesn't exist
        defs = root.find(".//{http://www.w3.org/2000/svg}defs")
        if defs is None:
            defs = ET.SubElement(root, "defs")
        
        # Check if greyscale filter already exists
        existing_filter = defs.find(".//{http://www.w3.org/2000/svg}filter[@id='greyscale']")
        if existing_filter is None:
            # Create greyscale filter
            filter_elem = ET.SubElement(defs, "filter", id="greyscale")
            fe_color_matrix = ET.SubElement(filter_elem, "feColorMatrix", 
                                          type="matrix", 
                                          values="0.299 0.587 0.114 0 0 0.299 0.587 0.114 0 0 0.299 0.587 0.114 0 0 0 0 0 1 0")
        
        # Apply greyscale filter to all path and rect elements
        for element in root.findall(".//{http://www.w3.org/2000/svg}path") + root.findall(".//{http://www.w3.org/2000/svg}rect"):
            convert_to_greyscale(element)
        
        # Apply greyscale filter to all other elements that can have colors
        for element in root.findall(".//{http://www.w3.org/2000/svg}circle") + root.findall(".//{http://www.w3.org/2000/svg}ellipse") + root.findall(".//{http://www.w3.org/2000/svg}polygon") + root.findall(".//{http://www.w3.org/2000/svg}polyline") + root.findall(".//{http://www.w3.org/2000/svg}line"):
            convert_to_greyscale(element)
        
        # Save the modified SVG
        tree.write(filepath, encoding='utf-8', xml_declaration=True)
        
        return {"status": "Converted to greyscale"}
    except Exception as e:
        return {"error": f"Failed to convert to greyscale: {str(e)}"}

@app.post("/revert")
async def revert_to_color_endpoint(req: RevertRequest):
    if req.folder == "Root":
        filepath = COLORFUL_ICON_DIR / f"{req.icon_name}.svg"
    else:
        filepath = COLORFUL_ICON_DIR / req.folder / f"{req.icon_name}.svg"
    
    if not filepath.exists():
        return {"error": "File not found"}

    try:
        # Restore from backup
        if restore_from_backup(filepath):
            return {"status": "Reverted to original colors"}
        else:
            return {"error": "No backup found to revert from"}
    except Exception as e:
        return {"error": f"Failed to revert to original colors: {str(e)}"}

@app.get("/check-greyscale/{folder_name}/{icon_name}")
async def check_greyscale(folder_name: str, icon_name: str):
    if folder_name == "Root":
        filepath = COLORFUL_ICON_DIR / f"{icon_name}.svg"
    else:
        filepath = COLORFUL_ICON_DIR / folder_name / f"{icon_name}.svg"
    
    if not filepath.exists():
        return {"error": "File not found"}

    try:
        ET.register_namespace('', "http://www.w3.org/2000/svg")
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Check if greyscale filter exists in the SVG
        defs = root.find(".//{http://www.w3.org/2000/svg}defs")
        if defs is not None:
            greyscale_filter = defs.find(".//{http://www.w3.org/2000/svg}filter[@id='greyscale']")
            if greyscale_filter is not None:
                return {"is_greyscale": True}
        
        return {"is_greyscale": False}
    except Exception as e:
        return {"error": f"Failed to check greyscale status: {str(e)}"}

@app.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Submit feedback from users"""
    try:
        feedback_id = save_feedback(req.type, req.message)
        
        if feedback_id:
            # Send email notification
            send_feedback_notification(req.type, req.message, feedback_id)
            return {"status": "Feedback submitted successfully", "id": feedback_id}
        else:
            return {"error": "Failed to save feedback"}
    except Exception as e:
        return {"error": f"Failed to submit feedback: {str(e)}"}

@app.get("/feedback")
async def get_feedback():
    """Get all feedback (for creator/admin to view)"""
    try:
        feedback_list = load_feedback()
        # Sort by timestamp (newest first)
        feedback_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {"feedback": feedback_list}
    except Exception as e:
        return {"error": f"Failed to load feedback: {str(e)}"}

@app.put("/feedback/{feedback_id}/status")
async def update_feedback_status(feedback_id: int, status: str):
    """Update feedback status (e.g., 'read', 'in_progress', 'resolved')"""
    try:
        if update_feedback_status_file(feedback_id, status):
            return {"status": "Feedback status updated successfully"}
        else:
            return {"error": "Feedback not found"}
    except Exception as e:
        return {"error": f"Failed to update feedback status: {str(e)}"}

@app.get("/infographics")
def list_infographics():
    infographics_dir = os.path.join(os.path.dirname(__file__), "../infographics")
    files = [f for f in os.listdir(infographics_dir) if f.lower().endswith('.png')]
    # Return list of PNGs (filenames)
    return {"infographics": files}

@app.get("/infographics/{infographic_name}/download")
def download_infographic_pptx(infographic_name: str):
    """
    Given an infographic PNG name, return the original PowerPoint file with all slides.
    This preserves the original shapes and formatting, even if there are some corruption issues.
    """
    base_dir = os.path.dirname(__file__)
    infographics_dir = os.path.join(base_dir, "../infographics")
    
    # Use the original master PowerPoint file
    master_pptx_path = os.path.join(infographics_dir, "infographics_master.pptx")
    
    print(f"[DEBUG] Download request for: {infographic_name}")
    print(f"[DEBUG] infographics_dir: {infographics_dir}")
    print(f"[DEBUG] master_pptx_path: {master_pptx_path}")

    # Check if master PPTX exists
    if not os.path.exists(master_pptx_path):
        print(f"[ERROR] Master PPTX not found at: {master_pptx_path}")
        raise HTTPException(status_code=404, detail="Master PPTX not found")

    # Return the original PowerPoint file directly
    filename = "infographics_master.pptx"
    print(f"[DEBUG] Returning original PPTX: {master_pptx_path} as {filename}")
    response = FileResponse(
        master_pptx_path, 
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", 
        filename=filename
    )
    return response

# Now mount the static files for infographics (after the download endpoint)
app.mount("/infographics", StaticFiles(directory=BASE_DIR / "infographics"), name="infographics")

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

