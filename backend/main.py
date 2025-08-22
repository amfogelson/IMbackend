from fastapi import FastAPI, APIRouter, Response, HTTPException, Request
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
from starlette.staticfiles import StaticFiles
from starlette.responses import Response
from urllib.parse import unquote

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

def send_feedback_notification(feedback_type, feedback_message, feedback_id, user_email=""):
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
- User Email: {user_email if user_email else 'Not provided'}
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

def send_feedback_response(user_email, feedback_id, response_message):
    """Send response email to user who submitted feedback"""
    if not EMAIL_ENABLED or not all([EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_FROM]) or not user_email:
        print("Email notifications disabled, configuration incomplete, or no user email provided")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = user_email
        msg['Subject'] = f"Response to your feedback (ID: {feedback_id})"
        
        # Create email body
        body = f"""
Thank you for your feedback on the Icon Manager application.

We have reviewed your feedback and would like to respond:

{response_message}

If you have any further questions or concerns, please don't hesitate to reach out.

Best regards,
Icon Manager Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, user_email, text)
        server.quit()
        
        print(f"Response email sent to {user_email} for feedback ID {feedback_id}")
        return True
        
    except Exception as e:
        print(f"Error sending response email: {e}")
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

# Light/Dark mode directories (only for regular icons and single color icons)
ICON_DIR_LIGHT = ICON_DIR / "light"
ICON_DIR_DARK = ICON_DIR / "dark"
SINGLE_COLOR_DIR_LIGHT = COLORFUL_ICON_DIR / "SingleColor" / "light"
SINGLE_COLOR_DIR_DARK = COLORFUL_ICON_DIR / "SingleColor" / "dark"

# Create directories
ICON_DIR.mkdir(exist_ok=True)
ICON_DIR_LIGHT.mkdir(exist_ok=True)
ICON_DIR_DARK.mkdir(exist_ok=True)
COLORFUL_ICON_DIR.mkdir(exist_ok=True)
FLAG_DIR.mkdir(exist_ok=True)
SINGLE_COLOR_DIR_LIGHT.mkdir(exist_ok=True)
SINGLE_COLOR_DIR_DARK.mkdir(exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CORSAwareStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

# Replace static mounts with CORS-enabled static files
app.mount("/static-icons", CORSAwareStaticFiles(directory=ICON_DIR), name="static-icons")
app.mount("/static", CORSAwareStaticFiles(directory=ICON_DIR), name="static")
app.mount("/static-icons-light", CORSAwareStaticFiles(directory=ICON_DIR_LIGHT), name="static-icons-light")
app.mount("/static-icons-dark", CORSAwareStaticFiles(directory=ICON_DIR_DARK), name="static-icons-dark")
# If you have other static mounts (e.g., for colorful icons), add them here as well
app.mount("/colorful-icons", CORSAwareStaticFiles(directory=COLORFUL_ICON_DIR), name="colorful-icons")
app.mount("/single-color-files", CORSAwareStaticFiles(directory=COLORFUL_ICON_DIR / "SingleColor"), name="single-color-files")
app.mount("/single-color-files-light", CORSAwareStaticFiles(directory=SINGLE_COLOR_DIR_LIGHT), name="single-color-files-light")
app.mount("/single-color-files-dark", CORSAwareStaticFiles(directory=SINGLE_COLOR_DIR_DARK), name="single-color-files-dark")
# app.mount("/flags", StaticFiles(directory=FLAG_DIR), name="flags")  # Commented out to use custom endpoint with CORS

# --- Pydantic Model ---
class UpdateColorRequest(BaseModel):
    icon_name: str
    group_id: str
    color: str
    type: str = "icon"  # "icon" or "flag"
    folder: str = "Root"  # folder name for icons
    mode: str = "light"  # "light" or "dark"

class ExportPngRequest(BaseModel):
    icon_name: str
    type: str = "icon"  # "icon" or "flag"
    folder: str = "Root"  # folder name for icons
    mode: str = "light"  # "light" or "dark"

class GreyscaleRequest(BaseModel):
    icon_name: str
    folder: str = "Root"  # folder name for colorful icons
    mode: str = "light"  # "light" or "dark"

class RevertRequest(BaseModel):
    icon_name: str
    folder: str = "Root"  # folder name for colorful icons
    mode: str = "light"  # "light" or "dark"

class SingleColorUpdateRequest(BaseModel):
    icon_name: str
    color: str
    mode: str = "light"  # "light" or "dark"

class SingleColorRevertRequest(BaseModel):
    icon_name: str
    mode: str = "light"  # "light" or "dark"

class ZipExportRequest(BaseModel):
    items: list[str]  # List of icon names
    type: str = "icon"  # "icon", "colorful-icon", or "flag"
    folder: str = "Root"  # folder name for icons
    format: str = "svg"  # "svg" or "png"
    mode: str = "light"  # "light" or "dark"

class FeedbackRequest(BaseModel):
    type: str
    message: str
    email: str = ""  # Optional email for user to receive responses

class FeedbackResponseRequest(BaseModel):
    feedback_id: int
    response_message: str

# --- Feedback Storage ---
FEEDBACK_DIR = BASE_DIR / "feedback_submissions"
FEEDBACK_DIR.mkdir(exist_ok=True)

def get_icon_directory(icon_type: str, folder: str = "Root", mode: str = "light") -> Path:
    """Get the appropriate directory for icons based on type, folder, and mode"""
    if icon_type == "icon":
        if folder == "Root":
            return ICON_DIR_LIGHT if mode == "light" else ICON_DIR_DARK
        else:
            # For subfolders, use mode-specific directories
            base_dir = ICON_DIR_LIGHT if mode == "light" else ICON_DIR_DARK
            return base_dir / folder
    elif icon_type == "colorful-icon":
        # Colorful icons use the same directory regardless of mode
        return COLORFUL_ICON_DIR
    elif icon_type == "single-color":
        return SINGLE_COLOR_DIR_LIGHT if mode == "light" else SINGLE_COLOR_DIR_DARK
    elif icon_type == "flag":
        return FLAG_DIR
    else:
        return ICON_DIR

def load_feedback():
    """Load feedback from individual files"""
    feedback_list = []
    
    if FEEDBACK_DIR.exists():
        for file_path in FEEDBACK_DIR.glob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) >= 5:  # Updated to include email
                        feedback = {
                            "id": int(file_path.stem),  # filename without extension
                            "timestamp": lines[0].strip(),
                            "type": lines[1].strip(),
                            "status": lines[2].strip(),
                            "email": lines[3].strip(),
                            "message": "".join(lines[4:]).strip()  # rest of the file
                        }
                        feedback_list.append(feedback)
                    elif len(lines) >= 4:  # Backward compatibility for old format
                        feedback = {
                            "id": int(file_path.stem),
                            "timestamp": lines[0].strip(),
                            "type": lines[1].strip(),
                            "status": lines[2].strip(),
                            "email": "",
                            "message": "".join(lines[3:]).strip()
                        }
                        feedback_list.append(feedback)
            except Exception as e:
                print(f"Error reading feedback file {file_path}: {e}")
    
    return feedback_list

def save_feedback(feedback_type, feedback_message, email=""):
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
            f.write(f"{email}\n")  # user's email
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

@app.get("/flags/{flag_name}")
async def get_flag(flag_name: str, request: Request):
    """Serve flag files with proper CORS headers"""
    file_path = FLAG_DIR / flag_name
    if not file_path.exists():
        return Response(status_code=404, content="Flag not found")
    
    return FileResponse(
        file_path,
        media_type="image/svg+xml",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.post("/export-png")
async def export_png(req: ExportPngRequest):
    if not CAIRO_AVAILABLE:
        return {"error": "PNG export not available. cairosvg is not installed."}
    
    # Get the mode from the request, default to light
    mode = getattr(req, 'mode', 'light')
    
    if req.type == "icon":
        if req.folder == "Root":
            if mode == "dark":
                filepath = ICON_DIR_DARK / req.icon_name
            else:
                filepath = ICON_DIR_LIGHT / req.icon_name
        elif req.folder == "SingleColor":
            if mode == "dark":
                filepath = SINGLE_COLOR_DIR_DARK / req.icon_name
            else:
                filepath = SINGLE_COLOR_DIR_LIGHT / req.icon_name
        else:
            if mode == "dark":
                filepath = ICON_DIR_DARK / req.folder / req.icon_name
            else:
                filepath = ICON_DIR_LIGHT / req.folder / req.icon_name
    elif req.type == "colorful-icon":
        if req.folder == "Root":
            filepath = COLORFUL_ICON_DIR / req.icon_name
        else:
            filepath = COLORFUL_ICON_DIR / req.folder / req.icon_name
    elif req.type == "flag":
        filepath = FLAG_DIR / req.icon_name
    elif req.type == "bcore-logo":
        filepath = BASE_DIR / "frontend" / "public" / "Bcore_Images_Video" / "Logos" / req.icon_name
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

@app.post("/export-svg")
async def export_svg(req: ExportPngRequest):  # Reuse the same request model
    # Get the mode from the request, default to light
    mode = getattr(req, 'mode', 'light')
    
    if req.type == "icon":
        if req.folder == "Root":
            if mode == "dark":
                filepath = ICON_DIR_DARK / req.icon_name
            else:
                filepath = ICON_DIR_LIGHT / req.icon_name
        elif req.folder == "SingleColor":
            if mode == "dark":
                filepath = SINGLE_COLOR_DIR_DARK / req.icon_name
            else:
                filepath = SINGLE_COLOR_DIR_LIGHT / req.icon_name
        else:
            if mode == "dark":
                filepath = ICON_DIR_DARK / req.folder / req.icon_name
            else:
                filepath = ICON_DIR_LIGHT / req.folder / req.icon_name
    elif req.type == "colorful-icon":
        if req.folder == "Root":
            filepath = COLORFUL_ICON_DIR / req.icon_name
        else:
            filepath = COLORFUL_ICON_DIR / req.folder / req.icon_name
    elif req.type == "flag":
        filepath = FLAG_DIR / req.icon_name
    elif req.type == "bcore-logo":
        filepath = BASE_DIR / "frontend" / "public" / "Bcore_Images_Video" / "Logos" / req.icon_name
    else:
        return {"error": "Invalid type"}
    
    if not filepath.exists():
        return {"error": "File not found"}

    try:
        # Read the SVG file
        with open(filepath, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Return the SVG content as text for copy functionality
        return {"svg_content": svg_content}
    except Exception as e:
        return {"error": f"Failed to export SVG: {str(e)}"}

@app.post("/download-svg")
async def download_svg(req: ExportPngRequest):  # Reuse the same request model
    # Get the mode from the request, default to light
    mode = getattr(req, 'mode', 'light')
    
    if req.type == "icon":
        if req.folder == "Root":
            if mode == "dark":
                filepath = ICON_DIR_DARK / req.icon_name
            else:
                filepath = ICON_DIR_LIGHT / req.icon_name
        elif req.folder == "SingleColor":
            if mode == "dark":
                filepath = SINGLE_COLOR_DIR_DARK / req.icon_name
            else:
                filepath = SINGLE_COLOR_DIR_LIGHT / req.icon_name
        else:
            if mode == "dark":
                filepath = ICON_DIR_DARK / req.folder / req.icon_name
            else:
                filepath = ICON_DIR_LIGHT / req.folder / req.icon_name
    elif req.type == "colorful-icon":
        if req.folder == "Root":
            filepath = COLORFUL_ICON_DIR / req.icon_name
        else:
            filepath = COLORFUL_ICON_DIR / req.folder / req.icon_name
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
        
        # Return the SVG content as a downloadable file
        return StreamingResponse(
            io.BytesIO(svg_content.encode('utf-8')),
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": f"attachment; filename={req.icon_name}",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        return {"error": f"Failed to download SVG: {str(e)}"}

@app.post("/export-zip")
async def export_zip(req: ZipExportRequest):
    """Export multiple icons as a ZIP file"""
    try:
        # Create a ZIP file in memory
        zip_buffer = io.BytesIO()
        
        # Get the mode from the request, default to light
        mode = getattr(req, 'mode', 'light')
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for item_name in req.items:
                try:
                    # Determine the source file path
                    if req.type == "icon":
                        if req.folder == "Root":
                            if mode == "dark":
                                source_path = ICON_DIR_DARK / f"{item_name}.svg"
                            else:
                                source_path = ICON_DIR_LIGHT / f"{item_name}.svg"
                        else:
                            if mode == "dark":
                                source_path = ICON_DIR_DARK / req.folder / f"{item_name}.svg"
                            else:
                                source_path = ICON_DIR_LIGHT / req.folder / f"{item_name}.svg"
                    elif req.type == "colorful-icon":
                        if req.folder == "Root":
                            source_path = COLORFUL_ICON_DIR / f"{item_name}.svg"
                        else:
                            source_path = COLORFUL_ICON_DIR / req.folder / f"{item_name}.svg"
                    elif req.type == "single-color":
                        if mode == "dark":
                            source_path = SINGLE_COLOR_DIR_DARK / f"{item_name}.svg"
                        else:
                            source_path = SINGLE_COLOR_DIR_LIGHT / f"{item_name}.svg"
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
        
        # Get the appropriate directory based on type, folder, and mode
        icon_dir = get_icon_directory(req.type, req.folder, req.mode)
        
        if req.type == "icon" or req.type == "icons":
            print("DEBUG: Type is icon", flush=True)
            filepath = icon_dir / req.icon_name
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

        # Ensure the directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
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

@app.get("/single-color")
async def get_single_color_icons():
    # Get all files from both light and dark mode directories
    light_dir = SINGLE_COLOR_DIR_LIGHT
    dark_dir = SINGLE_COLOR_DIR_DARK
    
    all_files = set()
    
    # Get files from light directory
    if light_dir.exists():
        png_files = [f.stem for f in light_dir.glob("*.png")]
        svg_files = [f.stem for f in light_dir.glob("*.svg")]
        all_files.update(png_files + svg_files)
    
    # Get files from dark directory
    if dark_dir.exists():
        png_files = [f.stem for f in dark_dir.glob("*.png")]
        svg_files = [f.stem for f in dark_dir.glob("*.svg")]
        all_files.update(png_files + svg_files)
    
    # Return sorted list of unique files
    return {"icons": sorted(list(all_files))}

@app.post("/single-color/update")
async def update_single_color_icon(req: SingleColorUpdateRequest):
    """Update the color of a single color icon (PNG or SVG)"""
    # Use mode-specific directory
    single_color_dir = SINGLE_COLOR_DIR_LIGHT if req.mode == "light" else SINGLE_COLOR_DIR_DARK
    
    if not single_color_dir.exists():
        return {"error": f"SingleColor {req.mode} directory not found"}
    
    # Check for both PNG and SVG files
    png_file = single_color_dir / f"{req.icon_name}.png"
    svg_file = single_color_dir / f"{req.icon_name}.svg"
    
    if not png_file.exists() and not svg_file.exists():
        return {"error": "Icon not found"}
    
    try:
        if svg_file.exists():
            # Handle SVG file
            create_backup(svg_file)
            
            ET.register_namespace('', "http://www.w3.org/2000/svg")
            tree = ET.parse(svg_file)
            root = tree.getroot()
            
            # Update all elements that can have colors
            for element in root.findall(".//{http://www.w3.org/2000/svg}path") + root.findall(".//{http://www.w3.org/2000/svg}rect") + root.findall(".//{http://www.w3.org/2000/svg}circle") + root.findall(".//{http://www.w3.org/2000/svg}ellipse") + root.findall(".//{http://www.w3.org/2000/svg}polygon") + root.findall(".//{http://www.w3.org/2000/svg}polyline") + root.findall(".//{http://www.w3.org/2000/svg}line"):
                update_element_color(element, req.color)
            
            # Save the modified SVG
            tree.write(svg_file, encoding='utf-8', xml_declaration=True)
            
        elif png_file.exists():
            # For PNG files, we'll need to convert them to SVG or handle them differently
            # For now, we'll return an error suggesting to use SVG format
            return {"error": "PNG files cannot be recolored. Please use SVG format for color changes."}
        
        return {"status": "Color updated successfully"}
        
    except Exception as e:
        return {"error": f"Failed to update color: {str(e)}"}

@app.post("/single-color/revert")
async def revert_single_color_icon(req: SingleColorRevertRequest):
    """Revert a single color icon to its original state"""
    # Use mode-specific directory
    single_color_dir = SINGLE_COLOR_DIR_LIGHT if req.mode == "light" else SINGLE_COLOR_DIR_DARK
    
    if not single_color_dir.exists():
        return {"error": f"SingleColor {req.mode} directory not found"}
    
    # Check for both PNG and SVG files
    png_file = single_color_dir / f"{req.icon_name}.png"
    svg_file = single_color_dir / f"{req.icon_name}.svg"
    
    if not png_file.exists() and not svg_file.exists():
        return {"error": "Icon not found"}
    
    try:
        if svg_file.exists():
            # Reset to default color for the current mode
            ET.register_namespace('', "http://www.w3.org/2000/svg")
            tree = ET.parse(svg_file)
            root = tree.getroot()
            
            # Set default color based on mode
            default_color = "#282828" if req.mode == "light" else "#D3D3D3"
            
            # Update all elements to the default color
            for element in root.iter():
                if element.tag.endswith(('path', 'rect', 'circle', 'ellipse', 'polygon', 'polyline', 'line')):
                    if element.get('fill') and element.get('fill') != 'none':
                        element.set('fill', default_color)
            
            # Save the modified SVG
            tree.write(svg_file, encoding='utf-8', xml_declaration=True)
            return {"status": "Reverted to original color"}
        elif png_file.exists():
            # For PNG files, we'll need to handle them differently
            return {"error": "PNG files cannot be reverted. Please use SVG format for color changes."}
        
    except Exception as e:
        return {"error": f"Failed to revert color: {str(e)}"}

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
        feedback_id = save_feedback(req.type, req.message, req.email)
        
        if feedback_id:
            # Send email notification
            send_feedback_notification(req.type, req.message, feedback_id, req.email)
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

@app.post("/feedback/respond")
async def respond_to_feedback(req: FeedbackResponseRequest):
    """Send a response email to the user who submitted feedback"""
    try:
        # Load the feedback to get the user's email
        feedback_list = load_feedback()
        feedback = next((f for f in feedback_list if f["id"] == req.feedback_id), None)
        
        if not feedback:
            return {"error": "Feedback not found"}
        
        user_email = feedback.get("email", "")
        if not user_email:
            return {"error": "No email address provided with this feedback"}
        
        # Send response email
        if send_feedback_response(user_email, req.feedback_id, req.response_message):
            # Update status to 'responded'
            update_feedback_status_file(req.feedback_id, "responded")
            return {"status": "Response sent successfully"}
        else:
            return {"error": "Failed to send response email"}
    except Exception as e:
        return {"error": f"Failed to respond to feedback: {str(e)}"}

@app.get("/infographics")
def list_infographics():
    infographics_dir = os.path.join(os.path.dirname(__file__), "../infographics")
    files = [f for f in os.listdir(infographics_dir) if f.lower().endswith('.png')]
    # Return list of PNGs (filenames)
    return {"infographics": files}

@app.get("/infographics/{infographic_name}/download")
def download_infographic_pptx(infographic_name: str, theme: str = "light"):
    """
    Given an infographic PNG name and theme, return the appropriate PowerPoint file with all slides.
    This preserves the original shapes and formatting, even if there are some corruption issues.
    """
    base_dir = os.path.dirname(__file__)
    infographics_dir = os.path.join(base_dir, "../infographics")
    
    # Use the same BASE_DIR that's used for static mounts
    infographics_dir = str(BASE_DIR / "infographics")
    
    # Debug: Print the actual path being used
    print(f"[DEBUG] base_dir: {base_dir}")
    print(f"[DEBUG] infographics_dir: {infographics_dir}")
    print(f"[DEBUG] Files in directory: {os.listdir(infographics_dir) if os.path.exists(infographics_dir) else 'Directory not found'}")
    
    # Use the theme-specific master PowerPoint file
    master_pptx_path = os.path.join(infographics_dir, f"infographics_master_{theme}.pptx")
    
    # Fallback to the light theme if theme-specific file doesn't exist
    if not os.path.exists(master_pptx_path):
        if theme != "light":
            print(f"[WARNING] {theme} theme PPTX not found, falling back to light theme")
            master_pptx_path = os.path.join(infographics_dir, "infographics_master_light.pptx")
            theme = "light"  # Update theme for filename
    
    # Final fallback to any available PPTX file
    if not os.path.exists(master_pptx_path):
        # Look for any PPTX file in the directory
        pptx_files = [f for f in os.listdir(infographics_dir) if f.endswith('.pptx')]
        if pptx_files:
            master_pptx_path = os.path.join(infographics_dir, pptx_files[0])
            theme = pptx_files[0].replace('infographics_master_', '').replace('.pptx', '')
            print(f"[WARNING] Using fallback PPTX: {pptx_files[0]}")
        else:
            print(f"[ERROR] No PPTX files found in: {infographics_dir}")
            raise HTTPException(status_code=404, detail="No PowerPoint files available")
    
    print(f"[DEBUG] Download request for: {infographic_name} with theme: {theme}")
    print(f"[DEBUG] infographics_dir: {infographics_dir}")
    print(f"[DEBUG] master_pptx_path: {master_pptx_path}")

    # Return the PowerPoint file directly
    filename = f"infographics_master_{theme}.pptx"
    print(f"[DEBUG] Returning PPTX: {master_pptx_path} as {filename}")
    response = FileResponse(
        master_pptx_path, 
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", 
        filename=filename
    )
    return response





@app.get("/bcore/thumbnail/{filename:path}")
def serve_bcore_thumbnail(filename: str):
    """Serve BCORE video thumbnails"""
    # Decode URL-encoded filename
    decoded_filename = unquote(filename)
    
    print(f"[DEBUG] Thumbnail request for: {filename}")
    print(f"[DEBUG] Decoded filename: {decoded_filename}")
    
    # Create thumbnails directory path
    thumbnails_dir = Path(__file__).parent / "thumbnails"
    
    # Generate thumbnail filename - try both .png and .PNG
    thumbnail_filename_lower = f"{Path(decoded_filename).stem}.png"
    thumbnail_filename_upper = f"{Path(decoded_filename).stem}.PNG"
    thumbnail_path_lower = thumbnails_dir / thumbnail_filename_lower
    thumbnail_path_upper = thumbnails_dir / thumbnail_filename_upper
    
    print(f"[DEBUG] Looking for thumbnail: {thumbnail_path_lower}")
    print(f"[DEBUG] Also looking for: {thumbnail_path_upper}")
    
    # Check if thumbnail exists (try both cases)
    if thumbnail_path_lower.exists():
        thumbnail_path = thumbnail_path_lower
        print(f"[DEBUG] Found thumbnail (lowercase): {thumbnail_path}")
    elif thumbnail_path_upper.exists():
        thumbnail_path = thumbnail_path_upper
        print(f"[DEBUG] Found thumbnail (uppercase): {thumbnail_path}")
    else:
        raise HTTPException(status_code=404, detail=f"Thumbnail not found: {thumbnail_filename_lower} or {thumbnail_filename_upper}")
    
    print(f"[DEBUG] Serving thumbnail: {thumbnail_path}")
    return FileResponse(str(thumbnail_path), media_type="image/png")

@app.get("/bcore/{filename:path}")
def serve_bcore_file(filename: str):
    """Serve BCORE branding files from the frontend public directory"""
    # Decode URL-encoded filename
    decoded_filename = unquote(filename)
    
    # Use BASE_DIR to navigate to the frontend directory
    bcore_dir = BASE_DIR.parent / "frontend" / "public" / "Bcore_Images_Video"
    
    # Check if it's a video file and look in Videos subfolder
    if decoded_filename.lower().endswith(('.mp4', '.mov', '.avi')):
        file_path = bcore_dir / "Videos" / decoded_filename
    # Check if it's an SVG file and look in Logos subfolder
    elif decoded_filename.lower().endswith('.svg'):
        file_path = bcore_dir / "Logos" / decoded_filename
    # Check if it's an image file and look in Images subfolder
    elif decoded_filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        file_path = bcore_dir / "Images" / decoded_filename
    else:
        file_path = bcore_dir / decoded_filename
    
    print(f"[DEBUG] BCORE request for: {filename}")
    print(f"[DEBUG] Decoded filename: {decoded_filename}")
    print(f"[DEBUG] bcore_dir: {bcore_dir}")
    print(f"[DEBUG] file_path: {file_path}")
    print(f"[DEBUG] file exists: {file_path.exists()}")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    # Determine content type based on file extension
    content_type = "application/octet-stream"
    if decoded_filename.lower().endswith('.mp4'):
        content_type = "video/mp4"
    elif decoded_filename.lower().endswith('.mov'):
        content_type = "video/quicktime"
    elif decoded_filename.lower().endswith('.avi'):
        content_type = "video/x-msvideo"
    elif decoded_filename.lower().endswith('.png'):
        content_type = "image/png"
    elif decoded_filename.lower().endswith('.jpg') or decoded_filename.lower().endswith('.jpeg'):
        content_type = "image/jpeg"
    elif decoded_filename.lower().endswith('.gif'):
        content_type = "image/gif"
    elif decoded_filename.lower().endswith('.svg'):
        content_type = "image/svg+xml"
    
    return FileResponse(str(file_path), media_type=content_type)

# Now mount the static files for infographics (after the download endpoint)
app.mount("/infographics", CORSAwareStaticFiles(directory=BASE_DIR / "infographics"), name="infographics")

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

