import fitz  # PyMuPDF
from PIL import Image
import io
from document_processor.logo_replace.utils.clip_utils import get_clip_model, get_image_embedding, is_similar_to_target
from document_processor.logo_replace.utils.file_utils import backup_file

def replace_logo_in_pdf(
    pdf_path: str,
    new_logo_path: str,
    old_logo_path: str,
    output_path: str = None,
    similarity_threshold: float = 0.93,
) -> bool:
    """Replace logo in a PDF file.
    
    Args:
        pdf_path: Path to the input PDF file
        new_logo_path: Path to the new logo image
        old_logo_path: Path to the old logo image for reference
        output_path: Path to save the modified PDF (defaults to appending '_updated' to input path)
        similarity_threshold: Threshold for logo similarity (default: 0.93)
        create_backup: Whether to create a backup of the original file (default: True)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if output_path is None:
        output_path = pdf_path.rsplit('.', 1)[0] + '_updated.pdf'
    

    # Load CLIP model
    model, preprocess = get_clip_model()
    
    # Load and embed the reference old logo
    old_logo_embedding = get_image_embedding(old_logo_path, model, preprocess)
    
    # Load the new logo
    new_logo = Image.open(new_logo_path)
    if new_logo.mode != "RGBA":              # covers RGB, L, 1, P, CMYK, etc.
        new_logo = new_logo.convert("RGBA")  # adds an opaque alpha channel
    buf = io.BytesIO()
    new_logo.save(buf, format="PNG")         # PNG keeps alpha if it exists
    new_logo_bytes = buf.getvalue()

    # new_logo_bytes = None
    
    # Open PDF
    pdf_document = fitz.open(pdf_path)
    replaced = False
    
    try:
        # Process each page
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # Get images on the page
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    
                    # Get additional image information
                    img_width = img[2]
                    img_height = img[3]
                    
                    # Extract image data
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Convert to PIL Image
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Check if image matches the target logo
                    is_similar, similarity = is_similar_to_target(
                        image, old_logo_embedding, model, preprocess, similarity_threshold
                    )
                    
                    if is_similar:
                        print(f"Replacing logo on page {page_num + 1}, image {img_index + 1} (similarity: {similarity:.4f})")
                        
                        # Try a different approach to handle the image
                        # Search for image reference on page
                        img_refs = []
                        img_bbox = None
                        
                        # Search the page contents for image references
                        for obj in page.get_images():
                            if obj[0] == xref:  # If this is our image
                                # Find all instances where this image is used on the page
                                for imgref in page.get_image_rects(obj[7]):  # obj[7] is the image name
                                    img_refs.append(imgref)
                        
                        if img_refs:
                            # Use the first occurrence of the image
                            img_bbox = img_refs[0]
                            
                            # Replace the image - use the redaction approach
                            annot = page.add_redact_annot(img_bbox)
                            page.apply_redactions()
                            
                            # Then insert the new logo
                            page.insert_image(img_bbox, stream=new_logo_bytes)
                            replaced = True
                        else:
                            # Fallback if we can't find the image rectangle
                            # Create a one-image PDF from the new logo
                            temp_pdf = fitz.open()
                            temp_page = temp_pdf.new_page(width=img_width, height=img_height)
                            temp_page.insert_image(fitz.Rect(0, 0, img_width, img_height), stream=new_logo_bytes)
                            
                            # Extract it as a PDF page
                            pdfbytes = temp_pdf.write()
                            temp_pdf.close()
                            
                            # Insert this as a PDF page image
                            page.show_pdf_page(
                                fitz.Rect(0, 0, img_width, img_height), 
                                fitz.open(stream=pdfbytes), 
                                0
                            )
                            replaced = True
                    
                except Exception as e:
                    print(f"Warning: Failed to process image {img_index + 1} on page {page_num + 1}: {str(e)}")
        
        if not replaced:
            print("No matching logos found for replacement.")
            return False
        
        # Save the modified PDF
        pdf_document.save(output_path)
        print(f"Successfully replaced logo(s) in {output_path}")
        return True
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return False
        
    finally:
        pdf_document.close()


        
if __name__ == "__main__":
    print("File utils module")  
    pdf_path = r"C:\odded\brand_logo\logo_management\test_files\2024 Year.pdf"
    new_logo_path = r"C:\odded\brand_logo\logo_management\test_files\logos\new_logo.png"
    old_logo_path = r"C:\odded\brand_logo\logo_management\test_files\logos\od_logo.png"
    output_path = r"C:\odded\brand_logo\logo_management\test_files\logos\2024 Year.pdf"
    
    replace_logo_in_pdf(
    pdf_path,
    new_logo_path,
    old_logo_path,
    output_path
    )