import socket
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Configuration ---
RPI_IP = '192.168.1.11'  # **CHANGE THIS to your Raspberry Pi's IP address**
PORT = 5005
FILE_TO_MONITOR = 'data.geojson'
MONITORED_DIR = '.'  # Monitor the current directory

# --- Global UDP Socket ---
# Create the UDP socket once outside the loop/class
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_geojson(filepath):
    """Loads a GeoJSON file and sends it via UDP."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Serialize and encode for transmission
        geojson_bytes = json.dumps(data).encode('utf-8')
        
        # Send the datagram
        sock.sendto(geojson_bytes, (RPI_IP, PORT))
        print(f"[{time.strftime('%H:%M:%S')}] SENT: New file detected and sent ({len(geojson_bytes)} bytes).")

    except FileNotFoundError:
        print(f"Error: {filepath} not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not parse {filepath}. Check file format.")
    except Exception as e:
        print(f"An error occurred during transmission: {e}")

# --- Watchdog Event Handler ---

class GeoJSONHandler(FileSystemEventHandler):
    """Custom handler to process file system events."""
    
    def on_modified(self, event):
        """Called when a file or directory is modified."""
        # We only care about the specific GeoJSON file
        if not event.is_directory and event.src_path.endswith(FILE_TO_MONITOR):
            # A brief sleep helps ensure the file write operation is complete 
            # and avoids reading a partially written file.
            time.sleep(0.1) 
            send_geojson(FILE_TO_MONITOR)

    def on_created(self, event):
        """Called when a file or directory is created."""
        if not event.is_directory and event.src_path.endswith(FILE_TO_MONITOR):
            send_geojson(FILE_TO_MONITOR)


def start_monitor():
    event_handler = GeoJSONHandler()
    observer = Observer()
    
    # Start the observer watching the current directory recursively
    observer.schedule(event_handler, MONITORED_DIR, recursive=False)
    observer.start()
    
    print(f"Monitoring '{FILE_TO_MONITOR}' for changes in {MONITORED_DIR}. Press Ctrl+C to stop.")
    
    # Initial send in case the file already exists
    if os.path.exists(FILE_TO_MONITOR):
        print(f"Initial send of existing file: {FILE_TO_MONITOR}")
        send_geojson(FILE_TO_MONITOR)
        
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

if __name__ == '__main__':
    # Need to import os here for os.path.exists
    import os
    start_monitor()