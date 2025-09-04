import os
from django.core.management import execute_from_command_line
from django.conf import settings

def test_file_handling():
    """Test file handling in the document processor"""
    
    # Ensure media directories exist
    from document_processor.views import ensure_media_dirs
    ensure_media_dirs()
    
    # Print directory structure
    print("\nMedia directory structure:")
    for root, dirs, files in os.walk(settings.MEDIA_ROOT):
        level = root.replace(str(settings.MEDIA_ROOT), '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logo_saas.settings')
    import django
    django.setup()
    
    test_file_handling() 