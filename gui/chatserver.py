import socket
import os
import json
import time
from math import sin, cos, radians

# --- Configuration ---
SOCKET_PATH = "/tmp/ac_bridge"

# Base coordinates for the simulated area (near the map center)
BASE_LAT = 39.0182  # Central Latitude
BASE_LON = -104.8932 # Central Longitude
RADIUS = 0.0005     # Radius of circular movement in degrees

# --- Data Generation Function ---

def generate_drone_data(start_time: float, frequency: float) -> tuple:
    """
    Generates simulated drone coordinates and metadata.
   
    The coordinates trace a slow circular path around the base point.
    """
    current_time = time.time()
    time_elapsed = current_time - start_time
   
    # Calculate an angle that increases with time
    angle = (time_elapsed * frequency) % 360  # Angle in degrees

    # 1. Discovery Drone (Simple circular path)
    # Convert angle to a coordinate offset
    disco_lat = BASE_LAT + (RADIUS * sin(radians(angle)))
    disco_lon = BASE_LON + (RADIUS * cos(radians(angle)))
   
    # [Lat, Lon, Alt, Misc_1, Misc_2] - The client expects 5 elements
    disco_vals = [disco_lat, disco_lon, 100.0, 0.0, 0.0]

    # 2. Rogue Drone (A different, slightly offset path)
    # The -90 offset makes it start 90 degrees behind Discovery
    rogue_lat = BASE_LAT + (RADIUS * sin(radians(angle - 90)))
    rogue_lon = BASE_LON + (RADIUS * cos(radians(angle - 90)))

    # [Lat, Lon, Alt, Misc_1, Misc_2]
    rogue_vals = [rogue_lat, rogue_lon, 150.0, 0.0, 0.0]

    # 3. Timestamp (Must be a float)
    timestamp = current_time

    # 4. Mode (An integer representing the drone's status/mode)
    mode = 1

    # The format expected by client.py is: ([dVals list], [rVals list], timestamp, mode)
    return (disco_vals, rogue_vals, timestamp, mode)

# --- Main Server Logic ---

def run_server():
    print(f"Starting server for socket: {SOCKET_PATH}")

    # 1. Clean up old socket file if it exists
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)
        print("Cleaned up stale socket file.")

    # 2. Create the UNIX domain socket
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
   
    try:
        # 3. Bind the socket to the path
        server.bind(SOCKET_PATH)
        server.listen(1)
        print("Listening for GUI client connection...")

        # 4. Wait for a connection (This is a blocking call)
        conn, _ = server.accept()
        print("Client connected! Starting data transmission loop.")

        # Client sends a signal (b'0') when it is ready to receive data
        conn.recv(1024)
       
        start_time = time.time()
        # Frequency of the movement pattern (degrees/second)
        movement_frequency = 5.0
        # How often to send data (should be faster than GUI's 0.1s check)
        send_interval = 0.05

        # 5. Continuous Data Sending Loop
        while True:
            # Generate the latest coordinate data
            data = generate_drone_data(start_time, movement_frequency)
           
            # Serialize the data into a JSON string and encode it to bytes
            json_data = json.dumps(data).encode('utf-8')
           
            try:
                # Send the data over the connection
                conn.sendall(json_data)
            except (BrokenPipeError, ConnectionResetError):
                print("Client disconnected.")
                break # Exit the loop if the client closes the connection

            # Wait before sending the next update
            time.sleep(send_interval)

    except KeyboardInterrupt:
        print("\nServer shutting down.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 6. Clean up resources
        if 'conn' in locals() and conn:
            conn.close()
        server.close()
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        print("Server shutdown complete.")

if __name__ == "__main__":
    run_server()