import pytesseract
from PIL import Image
import cv2
import numpy as np
import os
import io

def preprocess_image(image):
    """
    Preprocess the image to improve OCR accuracy.
    
    Args:
        image (PIL.Image): The input image
        
    Returns:
        numpy.ndarray: Preprocessed image
    """
    # Convert PIL image to numpy array
    img = np.array(image)
    
    # Convert to grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img
    
    # Apply thresholding to get a binary image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Apply noise reduction
    denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
    
    return denoised

def extract_text_from_image(image):
    """
    Extract text from an image using OCR.
    
    Args:
        image (PIL.Image or str): The input image or path to the image
        
    Returns:
        str: Extracted text
    """
    try:
        # If image is a file path, open it
        if isinstance(image, str):
            image = Image.open(image)
        
        # Preprocess the image
        preprocessed_img = preprocess_image(image)
        
        # Apply OCR
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(preprocessed_img, config=custom_config)
        
        # Clean up the text
        text = text.strip()
        
        return text
    except Exception as e:
        print(f"Error in OCR processing: {str(e)}")
        return None

def extract_text_from_file(file):
    """
    Extract text from an uploaded file.
    
    Args:
        file: The uploaded file object
        
    Returns:
        str: Extracted text
    """
    try:
        # Read the file
        image = Image.open(file)
        
        # Extract text
        text = extract_text_from_image(image)
        
        return text
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None

def detect_route_request(text):
    """
    Check if the extracted text contains a route request.
    
    Args:
        text (str): The extracted text
        
    Returns:
        bool: True if text contains a route request, False otherwise
    """
    if not text:
        return False
    
    # Keywords that might indicate a route request
    route_keywords = [
        "from", "to", "directions", "route", "how to get",
        "navigate", "travel", "go from", "way to", "path"
    ]
    
    # Check if any of the keywords are in the text
    text_lower = text.lower()
    for keyword in route_keywords:
        if keyword in text_lower:
            return True
    
    return False 