from pip._vendor import requests
import json
import logging

# Configure logging 
logging.basicConfig( 
    filename="catfacts.log", 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s")

# Make your first API call to get a random cat fact
def get_cat_fact():
    url = "https://catfact.ninja/fact"
    
    try:
        # Send GET request to the API
        response = requests.get(url)
        
        # Check if request was successful
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()
            return data['fact']
        else:
            print(f"Error: {response.status_code}")
            return None
        
 # now with error handling & logging
    except requests.exceptions.RequestException as e:      
        logging.error(f"Request error: {e}") 
        return None 
    except ValueError as e: 
        logging.error(f"JSON decode error: {e}") 
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# function to get 5 unique facts
def get_facts():
    cat_fact = []
    while len(cat_fact) < 5:
        new_fact = get_cat_fact()
        if new_fact not in cat_fact:
            cat_fact.append(new_fact)
            logging.info(f"Retrieved fact: {new_fact}")
        else: 
            logging.info("Duplicate or invalid fact, retrying...")
    return cat_fact

# Save list of facts to a JSON file.
def save_facts_to_json(facts, filename="output.json"): 
    try: 
        with open(filename, "w", encoding="utf-8") as f: 
            json.dump({"facts": facts}, f, ensure_ascii=False, indent=2) 
            logging.info(f"Successfully saved {len(facts)} facts to {filename}") 
    except Exception as e: 
        logging.error(f"Failed to save facts: {e}")
 
facts = get_facts() 
if facts: 
    for i, fact in enumerate(facts, 1): 
        print(f"Cat fact {i}: {fact}") 
        save_facts_to_json(facts) 
    else: 
        logging.error("No facts retrieved.")

def get_public_holidays(country_code="US", year=2024):
    """
    Get public holidays for a specific country and year
    Uses Nager.Date API (free, no key required)
    """
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an exception for bad status codes
        
        holidays = response.json()
        return holidays
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

# Test with 3 different countries
countries = ['US', 'CA', 'GB']
summary = {}
for country in countries:
    holidays = get_public_holidays(country)
    if holidays:
        for h in holidays:
            print(f" {h['localName']} - {h['date']}")
            summary[country] = len(holidays)
    else:
        summary[country] = 0

print("\n--- Holiday Counts Summary ---")
for country, count in summary.items():
    print(f"{country}: {count} holidays")