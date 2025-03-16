import os
import streamlit as st
from PIL import Image
import io
import sys
import html
import traceback
import requests
from utils.gemini_processor import process_image_with_gemini
from utils.route_processor import process_route_request, parse_input
from utils.translator import translate_text, SUPPORTED_LANGUAGES
from utils.poi_finder import find_poi_along_route, POI_CATEGORIES, get_place_photo_url, get_place_details

# Set page configuration
st.set_page_config(
    page_title="Akshar.AI",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-bottom: 1rem;
    }
    .info-text {
        font-size: 1rem;
        color: #000000;
    }
    .highlight {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        color: #000000;
        font-weight: 500;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #4CAF50;
        color: #000000;
        font-weight: 500;
    }
    .error-box {
        background-color: #FFEBEE;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #F44336;
        color: #000000;
        font-weight: 500;
    }
    .route-box {
        background-color: #FFF8E1;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #FFC107;
        color: #000000;
        font-weight: 500;
    }
    .route-box strong, .success-box strong, .error-box strong, .highlight strong {
        color: #000000;
        font-weight: 700;
    }
    .route-directions {
        color: #000000;
        font-weight: normal;
        line-height: 1.5;
    }
    div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF;
    }
    .debug-section {
        background-color: #E0E0E0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 2rem;
        border-left: 5px solid #9E9E9E;
    }
    .language-selector {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .translated-box {
        background-color: #E1F5FE;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        border-left: 5px solid #03A9F4;
        color: #000000;
    }
    .poi-box {
        background-color: #F3E5F5;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        border-left: 5px solid #9C27B0;
        color: #000000;
    }
    .poi-card {
        background-color: #FFFFFF;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        border: 1px solid #E0E0E0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .poi-name {
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    .poi-address {
        font-size: 0.9rem;
        color: #616161;
        margin-bottom: 0.5rem;
    }
    .poi-rating {
        color: #FFC107;
        font-weight: 500;
    }
    .poi-details {
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def test_google_maps_api():
    """Test Google Maps API connectivity"""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not api_key:
        return False, "Google Maps API key is missing. Please add it to your .env file."
    
    # Test with a simple geocoding request
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": "New York",
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("status") == "OK":
            return True, "Google Maps API is working correctly."
        else:
            return False, f"Google Maps API error: {data.get('status')} - {data.get('error_message', 'No error message')}"
    
    except Exception as e:
        return False, f"Error connecting to Google Maps API: {str(e)}"

def sanitize_text(text):
    """Sanitize text to prevent HTML injection"""
    if text is None:
        return ""
    return html.escape(str(text))

def process_image_for_route(image):
    """Process an image to extract route information using Gemini"""
    with st.spinner("Processing image with Gemini..."):
        # Create a debug expander
        with st.expander("Debug Information", expanded=False):
            st.write("Processing image with Gemini API...")
            
            # Extract route information from image using Gemini
            route_info = process_image_with_gemini(image)
            
            # Debug output will be shown inside the expander by the gemini_processor
        
        if route_info.get("error"):
            error_msg = sanitize_text(route_info['error'])
            st.markdown(f"<div class='error-box'>Error processing image: {error_msg}</div>", unsafe_allow_html=True)
            return False
        
        origin = sanitize_text(route_info.get("origin"))
        destination = sanitize_text(route_info.get("destination"))
        mode = sanitize_text(route_info.get("mode", "DRIVE"))
        
        if origin and destination:
            st.markdown(f"<div class='success-box'><strong>Gemini Analysis:</strong> Successfully extracted route information from the image.</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='highlight'><strong>Detected Route Request:</strong> From {origin} to {destination} by {mode.lower()}</div>", unsafe_allow_html=True)
            
            # Process the route request
            with st.spinner("Finding route..."):
                # Create a query string in the format expected by process_route_request
                query = f"from {origin} to {destination} by {mode.lower()}"
                route_directions = process_route_request(query)
                
                # Get selected language
                selected_language = st.session_state.get('selected_language', 'English')
                
                # Translate route directions if needed
                if selected_language != 'English':
                    with st.spinner(f"Translating to {selected_language}..."):
                        translated_directions = translate_text(route_directions, selected_language)
                        
                        # Sanitize and format translated directions
                        translated_directions_safe = sanitize_text(translated_directions)
                        formatted_translated_route = translated_directions_safe.replace('\n', '<br>')
                        
                        # Display translated directions
                        st.markdown(f"<div class='translated-box'><strong>Directions in {selected_language}:</strong><div class='route-directions'>{formatted_translated_route}</div></div>", unsafe_allow_html=True)
                
                # Always show English directions
                route_directions_safe = sanitize_text(route_directions)
                formatted_route = route_directions_safe.replace('\n', '<br>')
                st.markdown(f"<div class='route-box'><strong>Directions in English:</strong><div class='route-directions'>{formatted_route}</div></div>", unsafe_allow_html=True)
                
                # Show POI search options
                display_poi_search_options(origin, destination, mode)
            
            return True
        else:
            st.markdown("<div class='error-box'>Could not detect a valid route request in the image. Please try another image or use the text input tab.</div>", unsafe_allow_html=True)
            return False

def display_poi_search_options(origin, destination, mode):
    """Display options to search for POIs along the route"""
    st.markdown("<h3>Find Places Along Your Route</h3>", unsafe_allow_html=True)
    st.write("Discover points of interest along your journey:")
    
    # Create columns for POI category buttons
    cols = st.columns(3)
    
    # Add a button for each POI category
    for i, (category_id, category_info) in enumerate(POI_CATEGORIES.items()):
        col_idx = i % 3
        with cols[col_idx]:
            if st.button(f"🔍 {category_info['name']}", key=f"poi_{category_id}"):
                # Debug info
                st.write(f"Clicked on category: {category_info['name']} (ID: {category_id})")
                st.write(f"Origin: {origin}, Destination: {destination}, Mode: {mode}")
                
                # Create debug expander
                with st.expander("Debug Information", expanded=True):
                    st.write(f"Starting POI search with parameters:")
                    st.write(f"- Origin: {origin}")
                    st.write(f"- Destination: {destination}")
                    st.write(f"- Category: {category_id}")
                    st.write(f"- Mode: {mode}")
                    
                    # Test Google Maps API connectivity
                    api_key_available = bool(os.getenv('GOOGLE_MAPS_API_KEY'))
                    st.write(f"- API Key available: {api_key_available}")
                    
                    if api_key_available:
                        # Test API connectivity
                        is_working, message = test_google_maps_api()
                        if is_working:
                            st.success(message)
                        else:
                            st.error(message)
                            st.error("POI search cannot proceed without a working Google Maps API connection.")
                            return
                    else:
                        st.error("Google Maps API key is missing. Please add it to your .env file.")
                        return
                
                search_and_display_pois(origin, destination, category_id, mode)

def search_and_display_pois(origin, destination, category, mode):
    """Search for and display POIs along the route"""
    category_name = POI_CATEGORIES[category]["name"]
    
    with st.spinner(f"Searching for {category_name} along your route..."):
        try:
            # Create debug expander
            with st.expander("POI Search Process", expanded=True):
                st.write(f"### Searching for {category_name}")
                st.write("This may take a moment as we search multiple points along your route...")
                
                # Find POIs along the route
                pois = find_poi_along_route(origin, destination, category, mode)
                
                if pois:
                    st.write(f"✅ Found {len(pois)} {category_name}")
                else:
                    st.write(f"❌ No {category_name} found along this route")
            
            if pois:
                st.markdown(f"<div class='poi-box'><strong>Found {len(pois)} {category_name} along your route:</strong></div>", unsafe_allow_html=True)
                
                # Display POIs in a grid
                cols = st.columns(2)
                
                for i, poi in enumerate(pois):
                    col_idx = i % 2
                    with cols[col_idx]:
                        with st.container():
                            # Create a card for each POI
                            st.markdown(f"""
                            <div class='poi-card'>
                                <div class='poi-name'>{sanitize_text(poi['name'])}</div>
                                <div class='poi-address'>{sanitize_text(poi['address'])}</div>
                                <div class='poi-rating'>{'★' * int(poi.get('rating', 0))} {poi.get('rating', 'No rating')} ({poi.get('user_ratings_total', 0)} reviews)</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Add a button to show more details
                            if st.button("Show Details", key=f"details_{poi['place_id']}"):
                                display_place_details(poi['place_id'])
                            
                            # If there's a photo, display it
                            if 'photo_reference' in poi:
                                photo_url = get_place_photo_url(poi['photo_reference'])
                                if photo_url:
                                    st.image(photo_url, width=200)
            else:
                st.markdown(f"<div class='error-box'>No {category_name} found along this route. Try another category or increase the search radius.</div>", unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error searching for {category_name}: {str(e)}")
            st.write("### Debug Information")
            st.write("An error occurred during the POI search. Here are the details:")
            st.code(traceback.format_exc())
            print(f"ERROR in search_and_display_pois: {str(e)}")
            print(traceback.format_exc())

def display_place_details(place_id):
    """Display detailed information about a place"""
    with st.spinner("Loading place details..."):
        try:
            details = get_place_details(place_id)
            
            if details:
                st.markdown(f"### {details.get('name', 'Place Details')}")
                st.markdown(f"**Address:** {details.get('formatted_address', 'Not available')}")
                
                if 'formatted_phone_number' in details:
                    st.markdown(f"**Phone:** {details['formatted_phone_number']}")
                
                if 'website' in details:
                    st.markdown(f"**Website:** [{details['website']}]({details['website']})")
                
                if 'opening_hours' in details and 'weekday_text' in details['opening_hours']:
                    st.markdown("**Opening Hours:**")
                    for hours in details['opening_hours']['weekday_text']:
                        st.markdown(f"- {hours}")
                
                if 'url' in details:
                    st.markdown(f"[View on Google Maps]({details['url']})")
            else:
                st.error("Could not load place details. Please try again.")
                
                # Debug info
                st.write("### Debug Information")
                st.write(f"Failed to get details for place_id: {place_id}")
                st.write(f"API Key available: {bool(os.getenv('GOOGLE_MAPS_API_KEY'))}")
        
        except Exception as e:
            st.error(f"Error loading place details: {str(e)}")
            st.write("### Debug Information")
            st.write("An error occurred while loading place details. Here are the details:")
            st.code(traceback.format_exc())
            print(f"ERROR in display_place_details: {str(e)}")
            print(traceback.format_exc())

def display_route_with_translation(origin, destination, mode, user_input):
    """Display route information with translation option"""
    # Sanitize user input before displaying
    origin_safe = sanitize_text(origin)
    destination_safe = sanitize_text(destination)
    mode_safe = sanitize_text(mode.lower())
    
    st.markdown(f"<div class='highlight'><strong>Detected Route Request:</strong> From {origin_safe} to {destination_safe} by {mode_safe}</div>", unsafe_allow_html=True)
    
    # Process the route request
    with st.spinner("Finding route..."):
        route_info = process_route_request(user_input)
        
        # Get selected language
        selected_language = st.session_state.get('selected_language', 'English')
        
        # Translate route directions if needed
        if selected_language != 'English':
            with st.spinner(f"Translating to {selected_language}..."):
                translated_info = translate_text(route_info, selected_language)
                
                # Sanitize and format translated info
                translated_info_safe = sanitize_text(translated_info)
                formatted_translated_route = translated_info_safe.replace('\n', '<br>')
                
                # Display translated directions
                st.markdown(f"<div class='translated-box'><strong>Directions in {selected_language}:</strong><div class='route-directions'>{formatted_translated_route}</div></div>", unsafe_allow_html=True)
        
        # Always show English directions
        route_info_safe = sanitize_text(route_info)
        formatted_route = route_info_safe.replace('\n', '<br>')
        st.markdown(f"<div class='route-box'><strong>Directions in English:</strong><div class='route-directions'>{formatted_route}</div></div>", unsafe_allow_html=True)
        
        # Show POI search options
        display_poi_search_options(origin, destination, mode)

def main():
    # Initialize session state for language selection
    if 'selected_language' not in st.session_state:
        st.session_state['selected_language'] = 'English'
    
    # Header
    st.markdown("<h1 class='main-header'>Akshar.AI</h1>", unsafe_allow_html=True)
    st.markdown("<p class='info-text' style='color: #FFFFFF;'> Upload an image containing a route request or type your request directly.</p>", unsafe_allow_html=True)
    
    # Language selector in the sidebar
    st.sidebar.markdown("## Language Settings")
    selected_language = st.sidebar.selectbox(
        "Select language for directions:",
        options=list(SUPPORTED_LANGUAGES.keys()),
        index=list(SUPPORTED_LANGUAGES.keys()).index(st.session_state['selected_language'])
    )
    st.session_state['selected_language'] = selected_language
    
    if selected_language != 'English':
        st.sidebar.info(f"Directions will be translated to {selected_language} using Gemini AI.")
    
    # POI search settings
    st.sidebar.markdown("## Points of Interest")
    st.sidebar.info("After finding a route, you can search for places along your journey like restaurants, hotels, petrol stations, and more.")
    
    # Add a test button for POI search
    if st.sidebar.button("Test POI Search"):
        with st.sidebar:
            st.write("### POI Search Test")
            
            # Test Google Maps API connectivity
            is_working, message = test_google_maps_api()
            if is_working:
                st.success("✅ Google Maps API is working")
            else:
                st.error(f"❌ Google Maps API error: {message}")
                st.stop()
            
            # Test a simple POI search
            try:
                st.write("Testing POI search with sample data...")
                test_origin = "New York"
                test_destination = "Brooklyn"
                test_category = "restaurants"
                
                # Get route points
                from utils.poi_finder import get_route_points
                points = get_route_points(test_origin, test_destination)
                
                if points:
                    st.success(f"✅ Found {len(points)} points along the route")
                    
                    # Test Places API with the first point
                    if len(points) > 0:
                        lat, lng = points[0]
                        st.write(f"Testing Places API near {lat}, {lng}...")
                        
                        # Make a direct Places API request
                        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
                        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                        params = {
                            "location": f"{lat},{lng}",
                            "radius": 5000,
                            "type": "restaurant",
                            "key": api_key
                        }
                        
                        response = requests.get(url, params=params)
                        data = response.json()
                        
                        if data.get("status") == "OK":
                            st.success(f"✅ Places API found {len(data.get('results', []))} restaurants")
                        else:
                            st.error(f"❌ Places API error: {data.get('status')} - {data.get('error_message', 'No error message')}")
                else:
                    st.error("❌ Could not get route points")
            
            except Exception as e:
                st.error(f"❌ Error during POI search test: {str(e)}")
                st.code(traceback.format_exc())
    
    # Debug mode toggle in sidebar
    st.sidebar.markdown("---")
    debug_mode = st.sidebar.checkbox("Enable Debug Mode", value=True)
    if debug_mode:
        st.sidebar.info("Debug mode is enabled. You'll see detailed information about API responses.")
        
        # Show API key status
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if api_key:
            st.sidebar.success(f"Google Maps API Key is set (length: {len(api_key)})")
        else:
            st.sidebar.error("Google Maps API Key is not set!")
            
        # Test polyline package
        try:
            import polyline
            test_line = polyline.encode([(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)])
            decoded = polyline.decode(test_line)
            if len(decoded) == 3:
                st.sidebar.success("Polyline package is working correctly.")
            else:
                st.sidebar.error("Polyline package test failed.")
        except Exception as e:
            st.sidebar.error(f"Polyline package error: {str(e)}")
            st.sidebar.warning("Please install polyline: pip install polyline==2.0.0")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📷 Image Upload", "📱 Camera", "⌨️ Text Input"])
    
    with tab1:
        st.markdown("<h2 class='sub-header'>Upload Image</h2>", unsafe_allow_html=True)
        st.markdown("<p class='info-text' style='color: #FFFFFF;'>Upload an image containing text like 'How to get from New York to Boston' or 'Directions from London to Paris'.</p>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            # Display the uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            # Process the image with Gemini when button is clicked
            if st.button("Analyze Image & Find Route", key="upload_button"):
                process_image_for_route(image)
    
    with tab2:
        st.markdown("<h2 class='sub-header'>Camera Capture</h2>", unsafe_allow_html=True)
        st.markdown("<p class='info-text' style='color: #FFFFFF;'>Capture an image with your camera containing text like 'How to get from New York to Boston' or 'Directions from London to Paris'.</p>", unsafe_allow_html=True)
        
        # Camera settings
        st.markdown("<div class='highlight'><strong>Camera Tips:</strong><br>- Ensure good lighting<br>- Hold the camera steady<br>- Make sure text is clearly visible<br>- Position text in the center of the frame</div>", unsafe_allow_html=True)
        
        # Camera input with options
        camera_image = st.camera_input("Take a picture", help="Capture an image containing your route request")
        
        if camera_image is not None:
            # Display the captured image
            image = Image.open(camera_image)
            
            # Add image enhancement options
            st.markdown("<p class='info-text'>Image captured! You can process it directly or try again if the text isn't clear.</p>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                # Process the image with Gemini when button is clicked
                if st.button("Analyze Image & Find Route", key="camera_button"):
                    process_image_for_route(image)
            with col2:
                if st.button("Take Another Picture", key="retake_button"):
                    st.experimental_rerun()
    
    with tab3:
        st.markdown("<h2 class='sub-header'>Text Input</h2>", unsafe_allow_html=True)
        st.markdown("<p class='info-text'>Enter your route request directly.</p>", unsafe_allow_html=True)
        
        # Examples
        st.markdown("<div class='highlight'><strong>Examples:</strong><br>- Pune to Mumbai by car<br>- How to get from New York to Boston<br>- Directions from Seattle to Portland by bicycle<br>- San Francisco to Los Angeles</div>", unsafe_allow_html=True)
        
        # Text input
        user_input = st.text_input("Enter your route request:")
        
        if st.button("Find Route") and user_input:
            # Parse the input to find route information
            origin, destination, mode = parse_input(user_input)
            
            if origin and destination:
                display_route_with_translation(origin, destination, mode, user_input)
            else:
                st.markdown("<div class='error-box'>Could not understand your request. Please try again with a clearer description.</div>", unsafe_allow_html=True)
    
    # Add information about the application
    st.sidebar.markdown("## About")
    st.sidebar.markdown("This application combines Google's Gemini AI with Google Maps API to extract route requests from images and provide directions.")
    
    st.sidebar.markdown("## How to Use")
    st.sidebar.markdown("1. **Image Upload**: Upload an image containing a route request")
    st.sidebar.markdown("2. **Camera**: Capture an image with your device camera")
    st.sidebar.markdown("3. **Text Input**: Or type your request directly")
    st.sidebar.markdown("4. **Get Directions**: The app will process your request and show the route information")
    st.sidebar.markdown("5. **Language Selection**: Choose your preferred language for directions")
    st.sidebar.markdown("6. **Find Places**: Discover restaurants, hotels, and more along your route")
    
    st.sidebar.markdown("## Supported Formats")
    st.sidebar.markdown("- 'Pune to Mumbai by car'")
    st.sidebar.markdown("- 'How to get from New York to Boston'")
    st.sidebar.markdown("- 'Directions from Seattle to Portland by bicycle'")
    st.sidebar.markdown("- 'San Francisco to Los Angeles'")

if __name__ == "__main__":
    main() 