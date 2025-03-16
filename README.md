# Akshar.AI

An integrated application that combines Google's Gemini AI with Google Maps API to extract route requests from images and provide directions.

## Features

- **Gemini AI Integration**: Extract route information from images using Google's advanced AI model
- **Natural Language Processing**: Understand various ways to ask for directions
- **Google Maps Integration**: Get detailed route information including:
  - Total distance
  - Estimated travel time
  - Step-by-step directions
- **Multiple Input Methods**:
  - Upload images containing route requests
  - Capture images directly using your device camera
  - Type route requests directly
- **Support for Different Transport Modes**:
  - Car/Driving
  - Walking
  - Bicycling
  - Transit (bus, train)

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Get a Google Maps API key:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the "Routes API" for your project
   - Create an API key in the "Credentials" section
   - Make sure billing is enabled for your Google Cloud project

4. Get a Gemini API key:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create an API key for Gemini
   - Make sure you have access to the Gemini Pro Vision model

5. Create a `.env` file in the project directory:
   - Add your Google Maps API key as `GOOGLE_MAPS_API_KEY=your_key_here`
   - Add your Gemini API key as `GEMINI_API_KEY=your_key_here`

## Usage

Run the Streamlit application:
```
streamlit run app.py
```

The application will open in your default web browser with three tabs:

### Image Upload Tab
1. Upload an image containing a route request
2. Click "Analyze Image & Find Route"
3. The application will:
   - Analyze the image using Gemini AI to extract route information
   - Identify origin, destination, and transport mode
   - Request route information from Google Maps API
   - Display the route details

### Camera Tab
1. Capture an image containing a route request using your device camera
2. Click "Analyze Image & Find Route"
3. The application will process the captured image the same way as uploaded images

### Text Input Tab
1. Type your route request directly
2. Click "Find Route"
3. The application will process your request and show the route information

## Example Inputs

The application can understand various phrasings, such as:
- "Pune to Mumbai by car"
- "I want to go from New York to Boston by train"
- "How to get from London to Paris"
- "Directions from Seattle to Portland by bicycle"
- "San Francisco to Los Angeles"

## Troubleshooting

### Gemini AI Issues
- Ensure the image has clear, visible content
- Try taking a clearer picture if the AI fails to understand the request
- When using the camera, ensure good lighting and a steady hand
- If Gemini fails to extract information, use the text input tab instead

### Google Maps API Issues
- Verify your API key is correctly entered in the `.env` file
- Make sure you've enabled the Routes API (not just the Directions API)
- Check that billing is enabled for your Google Cloud project
- Verify your API key has the necessary permissions

## Notes

- Both the Google Maps API and Gemini API have usage limits and may require billing. Check your Google Cloud Console for quota information.
- This application requires an internet connection to work.
- Gemini's accuracy depends on the clarity of the input image. 
