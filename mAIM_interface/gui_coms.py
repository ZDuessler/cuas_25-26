import socket
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os # Added import for file path operations

# --- Configuration ---
RPI_IP = '192.168.1.XXX'  # **CHANGE THIS to your Raspberry Pi's IP address**
PORT = 5005
FILE_TO_MONITOR = 'data.geojson'
AUTH_COMMAND_FILE = 'LAUNCH_AUTH.cmd' # NEW: File that grants authorization to send
MONITORED_DIR = '.'  # Monitor the current directory

# --- Global State & UDP Socket ---
IS_AUTHORIZED = False # NEW: Global flag to track authorization status
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_geojson(filepath):
    """Loads a GeoJSON file and sends it via UDP, only if authorized."""
    global IS_AUTHORIZED
    
    # NEW: Check authorization before proceeding
    if not IS_AUTHORIZED:
        print(f"[{time.strftime('%H:%M:%S')}] PENDING: Cannot send {filepath}. Waiting for authorization file '{AUTH_COMMAND_FILE}'.")
        return

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Serialize and encode for transmission
        geojson_bytes = json.dumps(data).encode('utf-8')
        
        # Send the datagram
        sock.sendto(geojson_bytes, (RPI_IP, PORT))
        print(f"[{time.strftime('%H:%M:%S')}] SENT: File detected and AUTHORIZED for sending ({len(geojson_bytes)} bytes).")

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
        global IS_AUTHORIZED
        
        # NEW: Check if the authorization file was modified
        if not event.is_directory and event.src_path.endswith(AUTH_COMMAND_FILE):
            IS_AUTHORIZED = True
            print(f"[{time.strftime('%H:%M:%S')}] AUTHORIZATION RECEIVED! Sending is now enabled.")
            return # Stop processing, it was a command file

        # Process GeoJSON file ONLY if authorized
        if not event.is_directory and event.src_path.endswith(FILE_TO_MONITOR):
            # A brief sleep helps ensure the file write operation is complete 
            # and avoids reading a partially written file.
            time.sleep(0.1) 
            send_geojson(FILE_TO_MONITOR)

    def on_created(self, event):
        """Called when a file or directory is created."""
        global IS_AUTHORIZED

        # NEW: Check if the authorization file was created
        if not event.is_directory and event.src_path.endswith(AUTH_COMMAND_FILE):
            IS_AUTHORIZED = True
            print(f"[{time.strftime('%H:%M:%S')}] AUTHORIZATION RECEIVED! Sending is now enabled.")
            return # Stop processing, it was a command file

        # Process GeoJSON file ONLY if authorized
        if not event.is_directory and event.src_path.endswith(FILE_TO_MONITOR):
            send_geojson(FILE_TO_MONITOR)


def start_monitor():
    global IS_AUTHORIZED
    event_handler = GeoJSONHandler()
    observer = Observer()
    
    # Start the observer watching the current directory recursively
    observer.schedule(event_handler, MONITORED_DIR, recursive=False)
    observer.start()
    
    print(f"Monitoring '{FILE_TO_MONITOR}' for changes in {MONITORED_DIR}.")
    
    # NEW: Check for existing authorization file on startup
    if os.path.exists(AUTH_COMMAND_FILE):
        IS_AUTHORIZED = True
        print(f"Initial check: Authorization file '{AUTH_COMMAND_FILE}' found. Sending is authorized.")

    print(f"--- STATUS ---")
    if IS_AUTHORIZED:
        print("Authorization is currently ON.")
    else:
        print(f"Authorization is currently OFF. Create the file '{AUTH_COMMAND_FILE}' to enable sending.")


    # Initial send in case the file already exists
    if os.path.exists(FILE_TO_MONITOR):
        print(f"Initial send attempt of existing file: {FILE_TO_MONITOR}")
        send_geojson(FILE_TO_MONITOR)
        
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

if __name__ == '__main__':
    # os is now imported at the top level
    start_monitor()
