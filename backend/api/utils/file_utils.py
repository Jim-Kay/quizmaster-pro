import re

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a filename.
    
    Args:
        filename: The string to be sanitized
        
    Returns:
        A sanitized string safe for use as a filename
    """
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Remove any non-alphanumeric characters (except underscores and hyphens)
    filename = re.sub(r'[^\w\-]', '', filename)
    
    # Convert to lowercase
    filename = filename.lower()
    
    # Ensure the filename is not empty
    if not filename:
        filename = 'untitled'
        
    # Truncate if too long (max 255 chars is common filesystem limit)
    if len(filename) > 255:
        filename = filename[:255]
        
    return filename
