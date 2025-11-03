import socket
import json

# --- Configuration ---
HOST = '0.0.0.0'  # Listen on all available interfaces (Ethernet, Wi-Fi)
PORT = 5005
BUFFER_SIZE = 65536 # Maximum size for a UDP datagram (set generously)

def receive_data_udp():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    print(f"Listening for UDP datagrams on {HOST}:{PORT}...")

    while True:
        try:
            # Receive data and the address of the sender
            # recvfrom is blocking until data is received
            geojson_bytes, addr = sock.recvfrom(BUFFER_SIZE) 
            
            # Since UDP packets are discrete, no length-header logic is needed.
            # Directly decode the received bytes.
            geojson_string = geojson_bytes.decode('utf-8')
            geojson_data = json.loads(geojson_string)
            
            print("-" * 30)
            print(f"Received data from {addr} (Size: {len(geojson_bytes)} bytes):")
            # **Your GeoJSON processing logic goes here**
            # Example: print the type of the GeoJSON object
            print(f"GeoJSON Type: {geojson_data.get('type', 'N/A')}")
            print("-" * 30)

        except json.JSONDecodeError:
            print("Error: Received invalid GeoJSON data.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    receive_data_udp()