import json
import os
from pip._vendor import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('.env')
# find path to config file
current_path = Path(__file__).resolve()
parent_dir = current_path.parent.parent
file_path = parent_dir/"config.json"

# get api key
with open(file_path, "r") as f:
    config = json.load(f)

api_key = os.getenv('WEATHER_API_KEY')

base_url = "http://api.openweathermap.org/data/2.5/weather"

# list of cities of interest
cities = ["Portland,ME,US", "Boston,MA,US", "Albany,NY,US", "Burlington,VT,US","New York,NY,US"]

# example url
portland_url = f"{base_url}?q={cities[0]}&APPID={api_key}"

response = requests.get(portland_url)
data = response.json()

if data["cod"] == 200:  # Check if the city was found
    main_data = data["main"]
    temperature = main_data["temp"]
    humidity = main_data["humidity"]
    weather_description = data["weather"][0]["description"]

    print(f"Temperature: {temperature} K")
    print(f"Humidity: {humidity}%")
    print(f"Weather Description: {weather_description}")
else:
    print("City not found.")
