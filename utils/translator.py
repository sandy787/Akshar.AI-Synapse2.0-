import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# List of supported Indian languages
SUPPORTED_LANGUAGES = {
    "English": "English",
    "Hindi": "Hindi",
    "Bengali": "Bengali",
    "Telugu": "Telugu",
    "Marathi": "Marathi",
    "Tamil": "Tamil",
    "Urdu": "Urdu",
    "Gujarati": "Gujarati",
    "Kannada": "Kannada",
    "Malayalam": "Malayalam",
    "Punjabi": "Punjabi"
}

def translate_text(text, target_language):
    """
    Translate text to the target language using Gemini.
    
    Args:
        text (str): The text to translate
        target_language (str): The target language
        
    Returns:
        str: Translated text
    """
    if target_language == "English" or not text:
        return text
    
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create prompt for translation
        prompt = f"""
        Translate the following text from English to {target_language}. 
        Maintain the formatting and structure of the original text.
        Keep any numbers, place names, and special terms intact.
        
        Text to translate:
        {text}
        """
        
        # Generate translation
        response = model.generate_content(prompt)
        
        # Return the translated text
        return response.text.strip()
        
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return f"Translation error: {str(e)}\n\nOriginal text:\n{text}" 