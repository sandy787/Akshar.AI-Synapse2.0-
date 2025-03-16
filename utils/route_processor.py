import os
import re
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def parse_input(user_input):
    """
    Parse user input to extract origin and destination locations using NLP techniques.
    
    Args:
        user_input (str): User input string in natural language
        
    Returns:
        tuple: (origin, destination, mode_of_transport)
    """
    # Normalize input: convert to lowercase and remove extra spaces
    normalized_input = ' '.join(user_input.lower().split())
    
    # List of common transport modes and their API equivalents
    transport_modes = {
        "car": "DRIVE",
        "driving": "DRIVE",
        "drive": "DRIVE",
        "walk": "WALK",
        "walking": "WALK",
        "foot": "WALK",
        "on foot": "WALK",
        "bicycle": "BICYCLE",
        "bike": "BICYCLE",
        "cycling": "BICYCLE",
        "bicycling": "BICYCLE",
        "cycle": "BICYCLE",
        "transit": "TRANSIT",
        "bus": "TRANSIT",
        "train": "TRANSIT",
        "public transport": "TRANSIT",
        "public transportation": "TRANSIT",
        "metro": "TRANSIT",
        "subway": "TRANSIT",
        "rail": "TRANSIT"
    }
    
    # Default transport mode if none is specified
    default_mode = "DRIVE"
    
    # Try multiple patterns to extract information
    
    # Pattern 1: "from X to Y by Z"
    pattern1 = r"from\s+([A-Za-z0-9\s,.-]+)\s+to\s+([A-Za-z0-9\s,.-]+)(?:\s+by\s+([A-Za-z\s]+))?"
    
    # Pattern 2: "X to Y by Z"
    pattern2 = r"^([A-Za-z0-9\s,.-]+)\s+to\s+([A-Za-z0-9\s,.-]+)(?:\s+by\s+([A-Za-z\s]+))?"
    
    # Pattern 3: "directions from X to Y"
    pattern3 = r"directions\s+(?:from\s+)?([A-Za-z0-9\s,.-]+)\s+to\s+([A-Za-z0-9\s,.-]+)"
    
    # Pattern 4: "how to get from X to Y"
    pattern4 = r"how\s+to\s+get\s+(?:from\s+)?([A-Za-z0-9\s,.-]+)\s+to\s+([A-Za-z0-9\s,.-]+)"
    
    # Pattern 5: "X to Y" (simplest form)
    pattern5 = r"^([A-Za-z0-9\s,.-]+)\s+to\s+([A-Za-z0-9\s,.-]+)$"
    
    # Try each pattern in order
    for pattern in [pattern1, pattern2, pattern3, pattern4, pattern5]:
        match = re.search(pattern, normalized_input)
        if match:
            # Extract groups based on the number of capturing groups in the pattern
            groups = match.groups()
            if len(groups) >= 2:  # At least origin and destination
                origin = groups[0].strip()
                destination = groups[1].strip()
                
                # Extract transport mode if available (3rd group in some patterns)
                mode = None
                if len(groups) > 2 and groups[2]:
                    mode_text = groups[2].strip()
                    # Check if the extracted mode matches any known transport mode
                    for key in transport_modes:
                        if key in mode_text:
                            mode = transport_modes[key]
                            break
                
                # If no mode was found in the input, try to find it elsewhere in the text
                if not mode:
                    for key in transport_modes:
                        if key in normalized_input:
                            mode = transport_modes[key]
                            break
                
                # Use default mode if still not found
                if not mode:
                    mode = default_mode
                
                return origin, destination, mode
    
    # If no pattern matched, try a more flexible approach
    # Look for location names and transport modes in the text
    
    # Common prepositions and words that might indicate locations
    location_indicators = ["from", "to", "at", "in", "near", "starting", "ending", "origin", "destination"]
    
    words = normalized_input.split()
    potential_locations = []
    potential_mode = None
    
    # First, try to identify the transport mode
    for mode_key in transport_modes:
        if mode_key in normalized_input:
            potential_mode = transport_modes[mode_key]
            # Remove this mode from the input to avoid confusion with locations
            normalized_input = normalized_input.replace(mode_key, "")
            break
    
    # If no mode was found, use default
    if not potential_mode:
        potential_mode = default_mode
    
    # Now try to identify locations
    for i, word in enumerate(words):
        if word in location_indicators and i+1 < len(words):
            # The word after a location indicator might be a location
            potential_location = ""
            j = i + 1
            # Collect words until the next location indicator or end of sentence
            while j < len(words) and words[j] not in location_indicators:
                potential_location += words[j] + " "
                j += 1
            
            if potential_location:
                potential_locations.append(potential_location.strip())
    
    # If we found exactly two potential locations, use them as origin and destination
    if len(potential_locations) >= 2:
        return potential_locations[0], potential_locations[1], potential_mode
    
    # If all else fails, return None
    return None, None, None

def get_route_info(origin, destination, mode="DRIVE"):
    """
    Get route information from Google Routes API v2.
    
    Args:
        origin (str): Starting location
        destination (str): Ending location
        mode (str): Mode of transportation (DRIVE, WALK, BICYCLE, TRANSIT)
        
    Returns:
        dict: Route information including distance, duration, and steps
    """
    if not API_KEY:
        return {"error": "Google Maps API key not found. Please set GOOGLE_MAPS_API_KEY in .env file."}
    
    base_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.legs.steps,routes.legs.startLocation,routes.legs.endLocation"
    }
    
    payload = {
        "origin": {
            "address": origin
        },
        "destination": {
            "address": destination
        },
        "travelMode": mode,
        "routingPreference": "TRAFFIC_AWARE",
        "computeAlternativeRoutes": False,
        "routeModifiers": {
            "avoidTolls": False,
            "avoidHighways": False,
            "avoidFerries": False
        },
        "languageCode": "en-US",
        "units": "METRIC"
    }
    
    try:
        print(f"Requesting route from {origin} to {destination} by {mode.lower()}...")
        response = requests.post(base_url, headers=headers, data=json.dumps(payload))
        data = response.json()
        
        # Print only status code and basic info, not the full JSON
        print(f"API Response Status Code: {response.status_code}")
        
        if response.status_code == 200 and "routes" in data and data["routes"]:
            print("Route data received successfully")
            route = data["routes"][0]
            
            # Extract duration in seconds and convert to human-readable format
            duration_seconds = int(route.get("duration", "0").replace("s", ""))
            hours, remainder = divmod(duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_text = ""
            if hours > 0:
                duration_text += f"{hours} hour{'s' if hours > 1 else ''} "
            if minutes > 0:
                duration_text += f"{minutes} minute{'s' if minutes > 1 else ''} "
            if seconds > 0 and hours == 0:  # Only show seconds if less than an hour
                duration_text += f"{seconds} second{'s' if seconds > 1 else ''}"
            duration_text = duration_text.strip()
            
            # Extract distance in meters and convert to km
            distance_meters = int(route.get("distanceMeters", 0))
            distance_km = distance_meters / 1000
            distance_text = f"{distance_km:.1f} km"
            
            # Extract steps if available
            steps = []
            if "legs" in route and route["legs"]:
                for leg in route["legs"]:
                    if "steps" in leg:
                        for step in leg["steps"]:
                            # Extract step information
                            instruction = step.get("navigationInstruction", {}).get("instructions", "")
                            
                            # Calculate step distance
                            step_distance_meters = int(step.get("distanceMeters", 0))
                            step_distance = f"{step_distance_meters} m" if step_distance_meters < 1000 else f"{step_distance_meters/1000:.1f} km"
                            
                            steps.append({
                                "instruction": instruction,
                                "distance": step_distance
                            })
            
            result = {
                "origin": origin,
                "destination": destination,
                "distance": distance_text,
                "duration": duration_text,
                "steps": steps
            }
            
            return result
        else:
            error_message = data.get("error", {}).get("message", "Unknown error")
            print(f"Error: {error_message}")
            return {"error": f"Error: {error_message}"}
    
    except Exception as e:
        print(f"Exception: {str(e)}")
        return {"error": f"An error occurred: {str(e)}"}

def format_route_output(route_info):
    """
    Format route information into a readable string.
    
    Args:
        route_info (dict): Route information from get_route_info
        
    Returns:
        str: Formatted route information
    """
    if "error" in route_info:
        return f"Error: {route_info['error']}"
    
    output = [
        f"Route from {route_info['origin']} to {route_info['destination']}:",
        f"Total Distance: {route_info['distance']}",
        f"Estimated Time: {route_info['duration']}",
        "\nDirections:"
    ]
    
    if route_info["steps"]:
        for i, step in enumerate(route_info["steps"], 1):
            output.append(f"{i}. {step['instruction']} ({step['distance']})")
    else:
        output.append("Detailed directions not available.")
    
    return "\n".join(output)

def process_route_request(user_input):
    """
    Process a user's route request and return formatted directions.
    
    Args:
        user_input (str): User input string in natural language
        
    Returns:
        str: Formatted route information or error message
    """
    origin, destination, mode = parse_input(user_input)
    
    if not origin or not destination:
        return """I couldn't understand your request. Please try again with a clearer description of your journey.

Examples of requests I can understand:
- "Pune to Mumbai by car"
- "I want to go from New York to Boston by train"
- "How to get from London to Paris"
- "Directions from Seattle to Portland by bicycle"
- "San Francisco to Los Angeles"
"""
    
    route_info = get_route_info(origin, destination, mode)
    return format_route_output(route_info) 