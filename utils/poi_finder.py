import os
import requests
import json
import polyline
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# Get API key from environment variables
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
print(f"API Key available: {bool(API_KEY)}")

# Define POI categories
POI_CATEGORIES = {
    "restaurants": {
        "name": "Restaurants",
        "types": ["restaurant", "food", "cafe", "bakery", "meal_takeaway"]
    },
    "hotels": {
        "name": "Hotels",
        "types": ["lodging", "hotel", "motel", "guest_house"]
    },
    "fuel": {
        "name": "Petrol Stations",
        "types": ["gas_station", "petrol_station", "fuel"]
    },
    "hospitals": {
        "name": "Hospitals & Clinics",
        "types": ["hospital", "doctor", "health", "clinic", "pharmacy"]
    },
    "attractions": {
        "name": "Attractions",
        "types": ["tourist_attraction", "museum", "park", "amusement_park", "zoo"]
    },
    "shopping": {
        "name": "Shopping",
        "types": ["shopping_mall", "store", "supermarket", "department_store"]
    }
}

def get_route_points(origin, destination, mode="driving"):
    """
    Get a list of points along the route to use for POI searches.
    
    Args:
        origin (str): Starting location
        destination (str): Ending location
        mode (str): Mode of transportation
        
    Returns:
        list: List of lat/lng points along the route
    """
    print(f"DEBUG - get_route_points: origin={origin}, destination={destination}, mode={mode}")
    
    # Convert mode to Google Maps API format
    mode_mapping = {
        "DRIVE": "driving",
        "WALK": "walking",
        "BICYCLE": "bicycling",
        "TRANSIT": "transit"
    }
    
    google_mode = mode_mapping.get(mode, "driving")
    print(f"DEBUG - Converted mode: {mode} -> {google_mode}")
    
    # Make request to Directions API
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "mode": google_mode,
        "key": API_KEY
    }
    
    print(f"DEBUG - Directions API request: {url} with params: {params}")
    
    try:
        response = requests.get(url, params=params)
        print(f"DEBUG - Directions API response status: {response.status_code}")
        
        data = response.json()
        print(f"DEBUG - Directions API response status: {data.get('status')}")
        
        if data["status"] != "OK":
            print(f"DEBUG - Directions API error: {data.get('error_message', 'No error message')}")
            return []
        
        # Extract the polyline from the route
        route = data["routes"][0]
        encoded_polyline = route["overview_polyline"]["points"]
        print(f"DEBUG - Got polyline: {encoded_polyline[:20]}...")
        
        # Decode the polyline to get points
        points = polyline.decode(encoded_polyline)
        print(f"DEBUG - Decoded {len(points)} points from polyline")
        
        # We don't need all points, just a sample along the route
        # Take points at regular intervals
        route_length = len(points)
        if route_length <= 5:
            print(f"DEBUG - Using all {route_length} points")
            return points
        
        # Take 5 points evenly distributed along the route
        sampled_points = [
            points[i] for i in [
                0,  # Origin
                route_length // 4,
                route_length // 2,
                (3 * route_length) // 4,
                route_length - 1  # Destination
            ]
        ]
        
        print(f"DEBUG - Sampled {len(sampled_points)} points from route")
        for i, point in enumerate(sampled_points):
            print(f"DEBUG - Point {i}: {point}")
        
        return sampled_points
    
    except Exception as e:
        print(f"DEBUG - Error in get_route_points: {str(e)}")
        return []

def find_poi_along_route(origin, destination, category, mode="DRIVE", radius=5000, max_results=10):
    """
    Find points of interest along a route.
    
    Args:
        origin (str): Starting location
        destination (str): Ending location
        category (str): Category of POI to search for
        mode (str): Mode of transportation
        radius (int): Search radius in meters
        max_results (int): Maximum number of results to return
        
    Returns:
        list: List of POIs along the route
    """
    print(f"DEBUG - find_poi_along_route: origin={origin}, destination={destination}, category={category}, mode={mode}")
    
    # Add debug output to Streamlit
    st.write("### Debug: POI Search")
    st.write(f"Searching for {category} along route from {origin} to {destination} by {mode}")
    
    # Check if API key is available and valid
    if not API_KEY:
        error_msg = "Google Maps API key is missing. Please add it to your .env file."
        print(f"DEBUG - ERROR: {error_msg}")
        st.error(error_msg)
        return []
    
    if len(API_KEY) < 20:  # Simple validation for API key format
        error_msg = f"Google Maps API key appears to be invalid (length: {len(API_KEY)}). Please check your .env file."
        print(f"DEBUG - ERROR: {error_msg}")
        st.error(error_msg)
        return []
    
    # Get the category details
    category_info = POI_CATEGORIES.get(category, POI_CATEGORIES["restaurants"])
    poi_types = category_info["types"]
    print(f"DEBUG - POI types for {category}: {poi_types}")
    
    # Get points along the route
    route_points = get_route_points(origin, destination, mode)
    
    if not route_points:
        print("DEBUG - No route points returned")
        st.error("Failed to get route points. Check the console for more details.")
        return []
    
    # Search for POIs at each point
    all_pois = []
    
    for i, point in enumerate(route_points):
        lat, lng = point
        print(f"DEBUG - Searching near point {i}: {lat}, {lng}")
        
        # Make request to Places API
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": poi_types[0],  # Use the first type as primary
            "key": API_KEY
        }
        
        print(f"DEBUG - Places API request: {url} with params: {params}")
        
        try:
            response = requests.get(url, params=params)
            print(f"DEBUG - Places API response status: {response.status_code}")
            
            data = response.json()
            print(f"DEBUG - Places API response status: {data.get('status')}")
            
            if data["status"] == "OK":
                print(f"DEBUG - Found {len(data['results'])} places near point {i}")
                
                # Add results to the list
                for place in data["results"]:
                    # Check if this place is already in our list (by place_id)
                    if not any(poi["place_id"] == place["place_id"] for poi in all_pois):
                        print(f"DEBUG - Adding place: {place['name']}")
                        
                        # Format the place data
                        poi = {
                            "name": place["name"],
                            "place_id": place["place_id"],
                            "address": place.get("vicinity", ""),
                            "rating": place.get("rating", 0),
                            "user_ratings_total": place.get("user_ratings_total", 0),
                            "location": place["geometry"]["location"],
                            "types": place.get("types", [])
                        }
                        
                        # Add photo reference if available
                        if "photos" in place and len(place["photos"]) > 0:
                            poi["photo_reference"] = place["photos"][0]["photo_reference"]
                            print(f"DEBUG - Photo reference available for {place['name']}")
                        
                        all_pois.append(poi)
            else:
                print(f"DEBUG - Places API error: {data.get('error_message', 'No error message')}")
                st.warning(f"Error searching near point {i}: {data.get('status')}")
        
        except Exception as e:
            print(f"DEBUG - Error in Places API request: {str(e)}")
            st.error(f"Error searching near point {i}: {str(e)}")
    
    print(f"DEBUG - Total POIs found: {len(all_pois)}")
    
    # Sort by rating (highest first)
    all_pois.sort(key=lambda x: (x["rating"] * min(x["user_ratings_total"], 100)), reverse=True)
    
    # Return limited number of results
    result = all_pois[:max_results]
    print(f"DEBUG - Returning {len(result)} POIs")
    
    # Show debug info in Streamlit
    if not result:
        st.warning("No POIs found along the route. Check the console for more details.")
    else:
        st.success(f"Found {len(result)} POIs along the route.")
    
    return result

def get_place_photo_url(photo_reference, max_width=400):
    """
    Get the URL for a place photo.
    
    Args:
        photo_reference (str): Photo reference from Places API
        max_width (int): Maximum width of the photo
        
    Returns:
        str: URL to the photo
    """
    if not photo_reference:
        print("DEBUG - No photo reference provided")
        return None
    
    url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={API_KEY}"
    print(f"DEBUG - Photo URL: {url[:100]}...")
    return url

def get_place_details(place_id):
    """
    Get detailed information about a place.
    
    Args:
        place_id (str): Place ID from Places API
        
    Returns:
        dict: Place details
    """
    print(f"DEBUG - get_place_details: place_id={place_id}")
    
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,opening_hours,url",
        "key": API_KEY
    }
    
    print(f"DEBUG - Place Details API request: {url} with params: {params}")
    
    try:
        response = requests.get(url, params=params)
        print(f"DEBUG - Place Details API response status: {response.status_code}")
        
        data = response.json()
        print(f"DEBUG - Place Details API response status: {data.get('status')}")
        
        if data["status"] == "OK":
            print(f"DEBUG - Got details for place: {data['result'].get('name')}")
            return data["result"]
        else:
            print(f"DEBUG - Place Details API error: {data.get('error_message', 'No error message')}")
            return None
    
    except Exception as e:
        print(f"DEBUG - Error in get_place_details: {str(e)}")
        return None 