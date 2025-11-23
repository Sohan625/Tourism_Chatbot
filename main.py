import requests
import json
from typing import Optional

# ============================================
# CHILD AGENT 1: Weather Agent
# ============================================
class WeatherAgent:
    """Fetches weather info using Open-Meteo API"""
    
    def __init__(self):
        self.api_url = "https://api.open-meteo.com/v1/forecast"
    
    def get_weather(self, lat: float, lon: float) -> dict:
        """Get current weather for given coordinates"""
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,precipitation_probability",
            "timezone": "auto"
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            return {
                "success": True,
                "temperature": current.get("temperature_2m"),
                "rain_chance": current.get("precipitation_probability", 0)
            }
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}


# ============================================
# CHILD AGENT 2: Places Agent
# ============================================
class PlacesAgent:
    """Fetches tourist attractions using Overpass API"""
    
    def __init__(self):
        self.api_url = "https://overpass-api.de/api/interpreter"
    
    def get_tourist_places(self, lat: float, lon: float, limit: int = 5) -> dict:
        """Get tourist attractions near given coordinates"""
        
        # Overpass QL query to find tourist attractions within 15km radius
        query = f"""
        [out:json][timeout:25];
        (
          node["tourism"="attraction"](around:15000,{lat},{lon});
          way["tourism"="attraction"](around:15000,{lat},{lon});
          node["tourism"="museum"](around:15000,{lat},{lon});
          way["tourism"="museum"](around:15000,{lat},{lon});
          node["leisure"="park"]["name"](around:15000,{lat},{lon});
          way["leisure"="park"]["name"](around:15000,{lat},{lon});
          node["historic"](around:15000,{lat},{lon});
          way["historic"](around:15000,{lat},{lon});
        );
        out body;
        >;
        out skel qt;
        """
        
        try:
            response = requests.post(self.api_url, data={"data": query}, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract place names
            places = []
            seen_names = set()
            
            for element in data.get("elements", []):
                tags = element.get("tags", {})
                name = tags.get("name")
                
                if name and name not in seen_names:
                    seen_names.add(name)
                    places.append(name)
                    
                    if len(places) >= limit:
                        break
            
            return {"success": True, "places": places}
            
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}


# ============================================
# GEOCODING HELPER
# ============================================
class GeocodingService:
    """Converts place names to coordinates using Nominatim API"""
    
    def __init__(self):
        self.api_url = "https://nominatim.openstreetmap.org/search"
    
    def get_coordinates(self, place_name: str) -> dict:
        """Get lat/lon for a place name"""
        params = {
            "q": place_name,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "TourismAgentApp/1.0"  # Required by Nominatim
        }
        
        try:
            response = requests.get(self.api_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return {"success": False, "error": "Place not found"}
            
            location = data[0]
            return {
                "success": True,
                "lat": float(location["lat"]),
                "lon": float(location["lon"]),
                "display_name": location.get("display_name", place_name)
            }
            
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}


# ============================================
# PARENT AGENT: Tourism AI Agent (Orchestrator)
# ============================================
class TourismAgent:
    """Main orchestrator that coordinates child agents"""
    
    def __init__(self):
        self.geocoder = GeocodingService()
        self.weather_agent = WeatherAgent()
        self.places_agent = PlacesAgent()
    
    def parse_user_intent(self, user_input: str) -> dict:
        """Figure out what the user wants"""
        input_lower = user_input.lower()
        
        wants_weather = any(word in input_lower for word in [
            "weather", "temperature", "rain", "sunny", "climate", "hot", "cold", "forecast"
        ])
        
        wants_places = any(word in input_lower for word in [
            "places", "visit", "attractions", "see", "tourist", "plan", "trip", "go to", "explore"
        ])
        
        # If user just says they're going somewhere, assume they want places
        if not wants_weather and not wants_places:
            if "going to" in input_lower or "plan" in input_lower:
                wants_places = True
        
        return {
            "wants_weather": wants_weather,
            "wants_places": wants_places
        }
    
    def extract_place_name(self, user_input: str) -> Optional[str]:
        """Extract the destination from user input"""
        input_lower = user_input.lower()
        
        # Common patterns to find place names
        patterns = [
            "going to go to ", "going to ", "visit ", "to ", "in ", 
            "plan my trip to ", "traveling to ", "headed to "
        ]
        
        for pattern in patterns:
            if pattern in input_lower:
                idx = input_lower.find(pattern) + len(pattern)
                # Get the rest and clean it up
                rest = user_input[idx:].strip()
                # Take until we hit a comma, period, or common stop words
                for stop in [",", ".", "?", "!", " what", " and", " let", " i "]:
                    if stop in rest.lower():
                        rest = rest[:rest.lower().find(stop)]
                return rest.strip()
        
        return None
    
    def process_request(self, user_input: str) -> str:
        """Main method to handle user requests"""
        
        # Step 1: Extract the place name
        place_name = self.extract_place_name(user_input)
        
        if not place_name:
            return "I couldn't figure out which place you want to visit. Could you please mention the destination?"
        
        # Step 2: Get coordinates for the place
        geo_result = self.geocoder.get_coordinates(place_name)
        
        if not geo_result["success"]:
            return f"I'm sorry, I don't know if '{place_name}' exists or I couldn't find it. Could you check the spelling or try a different place?"
        
        lat, lon = geo_result["lat"], geo_result["lon"]
        place_display = place_name.title()
        
        # Step 3: Parse what the user wants
        intent = self.parse_user_intent(user_input)
        
        response_parts = []
        
        # Step 4: Get weather if requested
        if intent["wants_weather"]:
            weather = self.weather_agent.get_weather(lat, lon)
            
            if weather["success"]:
                temp = weather["temperature"]
                rain = weather["rain_chance"] or 0
                response_parts.append(
                    f"In {place_display} it's currently {temp}°C with a {rain}% chance of rain."
                )
            else:
                response_parts.append(
                    f"I couldn't fetch the weather for {place_display} right now."
                )
        
        # Step 5: Get places if requested
        if intent["wants_places"]:
            places = self.places_agent.get_tourist_places(lat, lon, limit=5)
            
            if places["success"] and places["places"]:
                if response_parts:
                    response_parts.append("And these are the places you can go:")
                else:
                    response_parts.append(f"In {place_display} these are the places you can go:")
                
                for place in places["places"]:
                    response_parts.append(f"  • {place}")
            else:
                response_parts.append(
                    f"I couldn't find popular tourist spots in {place_display} right now."
                )
        
        # If user didn't specify, give them places by default
        if not intent["wants_weather"] and not intent["wants_places"]:
            places = self.places_agent.get_tourist_places(lat, lon, limit=5)
            
            if places["success"] and places["places"]:
                response_parts.append(f"In {place_display} these are the places you can go:")
                for place in places["places"]:
                    response_parts.append(f"  • {place}")
        
        return "\n".join(response_parts) if response_parts else f"I found {place_display}, but I'm not sure what you'd like to know about it."


# ============================================
# MAIN - Run the Tourism Agent
# ============================================
def main():
    agent = TourismAgent()
    
    print("=" * 50)
    print("  Welcome to the Tourism AI Assistant!")
    print("  Type 'quit' to exit")
    print("=" * 50)
    print()
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("\nSafe travels! Goodbye!")
            break
        
        if not user_input:
            continue
        
        print("\nAssistant:", agent.process_request(user_input))
        print()


if __name__ == "__main__":
    main()