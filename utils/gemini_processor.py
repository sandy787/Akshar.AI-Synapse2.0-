import os
import google.generativeai as genai
from PIL import Image
import io
import re
import json
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# Configure the Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def process_image_with_gemini(image):
    """
    Process an image using Gemini to extract route information.
    
    Args:
        image (PIL.Image): The input image
        
    Returns:
        dict: Extracted route information with keys 'origin', 'destination', and 'mode'
    """
    try:
        # Debug: Print that we're starting the Gemini processing
        print("Starting Gemini image processing...")
        
        # Convert PIL image to bytes if needed
        if isinstance(image, Image.Image):
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            # Debug: Print image size
            print(f"Image size: {len(img_byte_arr.getvalue())} bytes")
        else:
            img_byte_arr = image
            
        # Create prompt for Gemini
        prompt = """
        Look at this image and extract travel route information.
        Identify the origin (starting point), destination (ending point), and mode of transport (default to 'car' if not specified).
        Return the information in a clear, structured format with only ASCII characters.
        Format your response as:
        Origin: [origin location]
        Destination: [destination location]
        Mode: [mode of transport]
        """
        
        # Debug: Print the prompt
        print(f"Sending prompt to Gemini: {prompt}")
        
        # Generate content with Gemini using the standard API
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Debug: Print image dimensions
        image_data = image if isinstance(image, Image.Image) else Image.open(img_byte_arr)
        print(f"Image dimensions: {image_data.size}")
        
        # Call Gemini API
        response = model.generate_content([prompt, image_data])
        
        # Debug: Print raw response
        print(f"Raw Gemini response: {response.text}")
        
        # Add debug output to Streamlit
        st.write("### Debug: Gemini Response")
        st.write(f"```\n{response.text}\n```")
        
        # Clean the response text to remove any non-printable or non-ASCII characters
        cleaned_text = clean_text(response.text)
        
        # Debug: Print cleaned text
        print(f"Cleaned response text: {cleaned_text}")
        
        # Process the response to extract structured information
        route_info = extract_route_info_from_response(cleaned_text)
        
        # Debug: Print extracted route info
        print(f"Extracted route info: {json.dumps(route_info)}")
        
        return route_info
        
    except Exception as e:
        print(f"Error processing image with Gemini: {str(e)}")
        # Add error to Streamlit for debugging
        st.error(f"Gemini API Error: {str(e)}")
        return {"origin": None, "destination": None, "mode": "DRIVE", "error": str(e)}

def clean_text(text):
    """
    Clean text by removing non-printable and non-ASCII characters.
    
    Args:
        text (str or dict): The text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Handle case where text is a dictionary
    if isinstance(text, dict):
        # If it has a 'text' key, use that
        if "text" in text:
            text = text["text"]
        # Otherwise, convert to string
        else:
            text = str(text)
    
    # Replace non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    
    # Replace control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text

def extract_route_info_from_response(response_text):
    """
    Extract structured route information from Gemini's response.
    
    Args:
        response_text (str or dict): The text response from Gemini
        
    Returns:
        dict: Extracted route information with keys 'origin', 'destination', and 'mode'
    """
    # Default values
    route_info = {
        "origin": None,
        "destination": None,
        "mode": "DRIVE"  # Default mode is driving
    }
    
    if not response_text:
        return route_info
    
    # Handle case where response_text is a dictionary
    if isinstance(response_text, dict):
        # If it's already a dictionary with the expected structure, return it
        if all(key in response_text for key in ["origin", "destination"]):
            return response_text
        # If it has a 'text' key, use that
        elif "text" in response_text:
            response_text = response_text["text"]
        # Otherwise, convert to string
        else:
            response_text = str(response_text)
    
    # Process the response text to extract information
    # This is a simple implementation - in production, you might want more robust parsing
    response_lower = response_text.lower()
    
    # Look for origin/from indicators
    origin_indicators = ["origin:", "from:", "starting point:", "start:"]
    for indicator in origin_indicators:
        if indicator in response_lower:
            try:
                # Extract text after the indicator until the next newline or common separator
                start_idx = response_lower.find(indicator) + len(indicator)
                end_idx = min(
                    x for x in [
                        response_lower.find("\n", start_idx),
                        response_lower.find(".", start_idx),
                        response_lower.find(",", start_idx),
                        len(response_lower)
                    ] if x > start_idx
                )
                route_info["origin"] = response_text[start_idx:end_idx].strip()
                break
            except Exception:
                # If there's an error in parsing, continue to the next indicator
                continue
    
    # Look for destination/to indicators
    dest_indicators = ["destination:", "to:", "ending point:", "end:"]
    for indicator in dest_indicators:
        if indicator in response_lower:
            try:
                # Extract text after the indicator until the next newline or common separator
                start_idx = response_lower.find(indicator) + len(indicator)
                end_idx = min(
                    x for x in [
                        response_lower.find("\n", start_idx),
                        response_lower.find(".", start_idx),
                        response_lower.find(",", start_idx),
                        len(response_lower)
                    ] if x > start_idx
                )
                route_info["destination"] = response_text[start_idx:end_idx].strip()
                break
            except Exception:
                # If there's an error in parsing, continue to the next indicator
                continue
    
    # Look for mode of transport indicators
    mode_indicators = ["mode:", "transport:", "transportation:", "by:", "using:"]
    for indicator in mode_indicators:
        if indicator in response_lower:
            try:
                # Extract text after the indicator until the next newline or common separator
                start_idx = response_lower.find(indicator) + len(indicator)
                end_idx = min(
                    x for x in [
                        response_lower.find("\n", start_idx),
                        response_lower.find(".", start_idx),
                        response_lower.find(",", start_idx),
                        len(response_lower)
                    ] if x > start_idx
                )
                mode_text = response_text[start_idx:end_idx].strip().lower()
                
                # Map the extracted mode to the appropriate API value
                mode_mapping = {
                    "car": "DRIVE",
                    "driving": "DRIVE",
                    "drive": "DRIVE",
                    "walk": "WALK",
                    "walking": "WALK",
                    "foot": "WALK",
                    "bicycle": "BICYCLE",
                    "bike": "BICYCLE",
                    "cycling": "BICYCLE",
                    "transit": "TRANSIT",
                    "bus": "TRANSIT",
                    "train": "TRANSIT",
                    "public": "TRANSIT"
                }
                
                for key, value in mode_mapping.items():
                    if key in mode_text:
                        route_info["mode"] = value
                        break
                
                break
            except Exception:
                # If there's an error in parsing, continue to the next indicator
                continue
    
    # If we couldn't extract structured information, try a more general approach
    if route_info["origin"] is None or route_info["destination"] is None:
        try:
            # Look for common patterns like "X to Y" or "from X to Y"
            if " to " in response_lower:
                parts = response_lower.split(" to ")
                if "from " in parts[0]:
                    route_info["origin"] = parts[0].split("from ")[1].strip()
                else:
                    route_info["origin"] = parts[0].strip()
                
                route_info["destination"] = parts[1].split(" by ")[0].strip()
                
                # Check if mode is specified after "by"
                if " by " in parts[1]:
                    mode_text = parts[1].split(" by ")[1].strip().lower()
                    mode_mapping = {
                        "car": "DRIVE",
                        "driving": "DRIVE",
                        "walk": "WALK",
                        "walking": "WALK",
                        "bicycle": "BICYCLE",
                        "bike": "BICYCLE",
                        "transit": "TRANSIT",
                        "bus": "TRANSIT",
                        "train": "TRANSIT"
                    }
                    for key, value in mode_mapping.items():
                        if key in mode_text:
                            route_info["mode"] = value
                            break
        except Exception:
            # If there's an error in the general approach, just return what we have
            pass
    
    return route_info 