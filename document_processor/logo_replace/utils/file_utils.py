import os
from pathlib import Path
import shutil
from typing import List, Tuple
import datetime

def get_file_extension(file_path: str) -> str:
    """Get the file extension in lowercase."""
    return os.path.splitext(file_path)[1].lower()

def is_supported_file(file_path: str) -> bool:
    """Check if the file type is supported."""
    supported_extensions = {
        # Documents
        '.docx', '.pdf', '.pptx',
        # Images
        '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff',
        # Videos
        '.mp4', '.avi', '.mov', '.wmv'
    }
    return get_file_extension(file_path) in supported_extensions

def get_supported_files(directory: str) -> List[Tuple[str, str]]:
    """Get all supported files in a directory and its subdirectories."""
    supported_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if is_supported_file(file_path):
                file_type = get_file_type(file_path)
                supported_files.append((file_path, file_type))
    return supported_files

def get_file_type(file_path: str) -> str:
    """Get the type of file based on its extension."""
    ext = get_file_extension(file_path)
    if ext in ['.docx']:
        return 'docx'
    elif ext in ['.pdf']:
        return 'pdf'
    elif ext in ['.pptx']:
        return 'pptx'
    elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']:
        return 'image'
    elif ext in ['.mp4', '.avi', '.mov', '.wmv']:
        return 'video'
    return 'unknown'

def create_output_path(input_path: str, suffix: str = '_updated') -> str:
    """Create an output path by adding a suffix before the extension."""
    directory = os.path.dirname(input_path)
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)
    return os.path.join(directory, f"{name}{suffix}{ext}")

def ensure_directory(directory: str) -> None:
    """Ensure a directory exists, create it if it doesn't."""
    Path(directory).mkdir(parents=True, exist_ok=True)

def backup_file(file_path, backup_dir=None):
    """
    Create a backup copy of a file.
    
    Args:
        file_path (str): Path to the file to back up
        backup_dir (str, optional): Directory to store backup. If None, uses same directory as file
        
    Returns:
        str: Path to the backup file
    """
    # Get file name and directory
    file_dir, file_name = os.path.split(file_path)
    
    # If backup directory not specified, use file's directory
    if backup_dir is None:
        backup_dir = file_dir
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Generate backup filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(file_name)
    backup_name = f"{name}_backup_{timestamp}{ext}"
    backup_path = os.path.join(backup_dir, backup_name)
    
    # Create backup
    shutil.copy2(file_path, backup_path)
    print(f"Created backup of {file_path} at {backup_path}")
    
    return backup_path 

