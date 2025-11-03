import json
import time
import random
import os

# --- Configuration ---
INPUT_FILE = 'initial.geojson'
OUTPUT_FILE = 'data.geojson'
UPDATE_INTERVAL_SECONDS = 0.1
# ---------------------

def load_initial_geojson():
    """Loads the base GeoJSON data."""
    try:
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: The initial file '{INPUT_FILE}' was not found.")
        print("Please create an 'initial.geojson' file first.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Failed to parse '{INPUT_FILE}'. Check for valid JSON.")
        return None

def update_coordinates(geojson_data, step):
    """Updates the coordinates of the first feature slightly."""
    # We'll assume the first feature is a Point for this simple test
    feature = geojson_data['features'][0]
    
    # Simple change: increment the longitude by a small, random amount
    lon_change = (random.random() - 0.5) * 0.0001
    lat_change = (random.random() - 0.5) * 0.0001
    
    current_lon = feature['geometry']['coordinates'][0]
    current_lat = feature['geometry']['coordinates'][1]
    
    new_lon = current_lon + lon_change
    new_lat = current_lat + lat_change
    
    # Update the coordinates
    feature['geometry']['coordinates'][0] = new_lon
    feature['geometry']['coordinates'][1] = new_lat
    
    # Update a property to show the file is changing
    feature['properties']['timestamp'] = time.time()
    feature['properties']['update_count'] = step

    return geojson_data

def save_geojson(geojson_data):
    """Writes the updated GeoJSON data to the output file."""
    try:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(geojson_data, f, indent=2)
    except IOError as e:
        print(f"Error writing to file '{OUTPUT_FILE}': {e}")

def main():
    print(f"Starting GeoJSON updater...")
    
    # Load the starting data once
    data = load_initial_geojson()
    if data is None:
        return

    update_step = 0
    try:
        while True:
            update_step += 1
            
            # 1. Update the data
            updated_data = update_coordinates(data, update_step)
            
            # 2. Save the updated data
            save_geojson(updated_data)
            
            print(f"Update #{update_step} written to {OUTPUT_FILE} @ {time.strftime('%H:%M:%S')}")
            
            # 3. Wait for the specified interval (0.5 seconds)
            time.sleep(UPDATE_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nUpdater stopped by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == '__main__':
    main()