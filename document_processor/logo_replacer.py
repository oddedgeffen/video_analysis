import os
import tempfile
from pathlib import Path
from django.conf import settings

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import specialized processors
from document_processor.logo_replace.docx_processor import replace_logo_in_docx
from document_processor.logo_replace.pptx_processor import replace_logo_in_pptx
from document_processor.logo_replace.pdf_processor import replace_logo_in_pdf



def ensure_dir_exists(path):
    """Ensure directory exists, create if it doesn't"""
    os.makedirs(os.path.dirname(path), exist_ok=True)

def get_processed_path(original_path, debug=False):
    """Generate path for processed file in the processed directory"""
    filename = os.path.basename(original_path)
    name, ext = os.path.splitext(filename)
    processed_filename = f"{name}_processed{ext}"
    
    # Use the same directory as the input file
    processed_dir = os.path.dirname(original_path)
    return os.path.join(processed_dir, processed_filename)

def replace_logo(document_path, old_logo_path, new_logo_path, debug=False):
    """
    Replace instances of old_logo with new_logo in the document.
    
    Args:
        document_path: Path to the document
        old_logo_path: Path to the old logo image
        new_logo_path: Path to the new logo image
        
    Returns:
        Path to the processed document
    """
    # Get file extension to determine document type
    ext = Path(document_path).suffix.lower()
    
    # Log processing start
    print(f"Processing document: {document_path}")
    print(f"Document type: {ext}")
    
    # Get output path in processed directory    
    output_path = get_processed_path(document_path, debug)

    # Process document based on type
    if ext == '.pdf':
        return process_pdf(document_path, old_logo_path, new_logo_path, output_path)
    elif ext == '.docx':
        return process_docx(document_path, old_logo_path, new_logo_path, output_path)
    elif ext == '.pptx':
        return process_pptx(document_path, old_logo_path, new_logo_path, output_path)
    else:
        raise ValueError(f"Unsupported document type: {ext}")

def process_pdf(document_path, old_logo_path, new_logo_path, output_path):
    
    # Call the actual PDF logo replacement function
    success = replace_logo_in_pdf(
        pdf_path=document_path,
        old_logo_path=old_logo_path,
        new_logo_path=new_logo_path,
        output_path=output_path,
        similarity_threshold=0.93,
    )
    
    if not success:
        raise Exception("Failed to replace logo in PDF")
    
    return output_path

def process_docx(document_path, old_logo_path, new_logo_path, output_path):
    
    # Call the actual DOCX logo replacement function
    success = replace_logo_in_docx(
        docx_path=document_path,
        old_logo_path=old_logo_path,
        new_logo_path=new_logo_path,
        output_path=output_path,
        similarity_threshold=0.93,
    )
    
    if not success:
        raise Exception("Failed to replace logo in DOCX")
    
    return output_path

def process_pptx(document_path, old_logo_path, new_logo_path, output_path):
    
    # Call the actual PPTX logo replacement function
    success = replace_logo_in_pptx(
        pptx_path=document_path,
        old_logo_path=old_logo_path,
        new_logo_path=new_logo_path,
        output_path=output_path,
        similarity_threshold=0.93,
    )
    
    if not success:
        raise Exception("Failed to replace logo in PPTX")
    
    return output_path

if __name__ == "__main__":
    # document_path = r"C:\odded\brand_logo\logo_management\test_files\marketing_report.docx"
    # document_path = r"C:\odded\brand_logo\logo_management\test_files\COMPANY MEETING.pptx"
    # document_path = r"C:\odded\brand_logo\logo_management\test_files\2024 Year.pdf"
    document_path = r"C:\Users\User\Downloads\mortgage.pdf"
    new_logo_path = r"C:\odded\brand_logo\logo_management\test_files\logos\new_logo.png"
    # old_logo_path = r"C:\odded\brand_logo\logo_management\test_files\logos\od_logo.png"
    old_logo_path = r"C:\odded\logo_saas_docu\image_0.png"
    old_logo_path = r"C:\Users\User\Downloads\mortgage_old_logo.png"
    
    replace_logo(document_path, old_logo_path, new_logo_path, debug=True)
    
    
